# --- Imports ---
import os

# --- MCP Server Setup ---
from fastmcp import FastMCP

# --- Crawl4AI Setup ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.cache_context import CacheMode

# --- Starlette Setup - for HTTP requests ---
from typing import Optional
from starlette.requests import Request
from starlette.responses import JSONResponse

# --- Time Setup - for timing requests ---
import time

# --- Tools ---
from .tools.scrape_url import scrape_url
from .tools.detect_paywall import detect_paywall
from .tools.open_login_browser import open_login_browser

# --- MCP Server Setup ---
# This MCP server has 3 tools:
# 1. scrape_url - scrapes a single URL
# 2. detect_paywall - detects if a webpage has a paywall
# 3. open_login_browser - opens a visible browser window for user login/authentication on paywalled sites
mcp = FastMCP("WebScraperMCP Server")

# --- Healthcheck Route ---
@mcp.custom_route("/", methods=["GET"])
async def healthcheck(request: Request) -> JSONResponse:
    """
    Responds with a 200 OK status for health checks, required by Cloud Run.
    """
    return JSONResponse({"status": "ok"})

# --- Register Tools ---
# --- Tool 1: scrape_single_url - scrapes a single URL ---
@mcp.tool(
    name="scrape_single_url",
    description="""This is the main workhorse tool for extracting the full, clean content from a URL in Markdown format. It should be used as the final step in the scraping workflow.

**Session Data Usage (CRITICAL):**
- **session_data parameter**: The MOST IMPORTANT parameter when dealing with authenticated content
- **When to use session_data**: ALWAYS when you have session_data from `open_login_browser`
- **How to use**: Pass the exact `session_data` object from `open_login_browser` response

**Pure In-Memory Session Management:**
- This tool now uses PURE IN-MEMORY session management - no persistent directories are created
- Sessions are handled entirely through the `session_data` parameter
- No filesystem dependencies or directory contamination between scraping attempts

**Workflow Examples:**

**Use Case 1 (No Paywall):**
```
detect_paywall(url="example.com") → paywall_detected: false
scrape_single_url(url="example.com")  # No session_data needed
```

**Use Case 2 (Paywall Bypassed - CORRECT WAY):**
```
detect_paywall(url="medium.com/article") → paywall_detected: true
open_login_browser(url="medium.com/article") → session_info.session_data: {...}
scrape_single_url(url="medium.com/article", session_data={...})  # MUST include session_data
```

**🚨 CRITICAL Return Value Monitoring:**
Pay close attention to the `status` field in the returned JSON:
- **`status: 'success'`**: Successful scrape. Workflow complete.
- **`status: 'paywall_persistent'`**: ⚠️ **SESSION INVALID** - Paywall remains despite using session. The user's account may lack subscription or session expired. Inform user and offer to retry authentication.

**Parameter Priority (Use in this order):**
1. **session_data** (in-memory session - PREFERRED for authenticated content)
2. storage_state_path (file-based session - legacy support only)"""
)
async def scrape_url_tool(
    url: str,
    storage_state_path: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_data: Optional[dict] = None
) -> dict:
    """
    The main tool for scraping a single URL. It assumes any necessary login
    or paywall bypass has been handled by providing a valid session.

    Args:
        url: The URL to scrape.
        storage_state_path: Optional path to a storage_state.json file for pre-authenticated sessions.
        user_agent: Optional custom User-Agent string to avoid blocking.
        session_data: Optional in-memory session data dictionary (cookies, localStorage, etc.) - PREFERRED METHOD.
    """
    return await scrape_url(
        url=url,
        storage_state_path=storage_state_path,
        user_data_dir=user_data_dir,
        user_agent=user_agent,
        session_data=session_data
    )

# --- Tool 2: detect_paywall - detects if a webpage has a paywall ---
@mcp.tool(
    name="detect_paywall",
    description="""Your **MANDATORY FIRST STEP** for any URL scraping request. This tool quickly and efficiently checks if a URL is protected by a paywall using a combination of keyword analysis and AI vision on a screenshot, without performing a full content scrape.

**Pure In-Memory Session Management:**
- Now uses PURE IN-MEMORY session management - no persistent directories created
- No filesystem dependencies or contamination between detection attempts
- Sessions handled entirely through the `session_data` parameter

**Required Workflow Sequence:**
1. **ALWAYS** call this tool first to assess the URL
2. **If paywall_detected: false** → proceed directly to `scrape_single_url` tool
3. **If paywall_detected: true** → MUST call `open_login_browser` next to handle authentication

**Critical Next Steps Based on Results:**
- **NO PAYWALL DETECTED**: Call `scrape_single_url(url="[URL]")` immediately
- **PAYWALL DETECTED**: Call `open_login_browser(url="[URL]")` to get session_data, then call `scrape_single_url(url="[URL]", session_data={...})`

**Advanced Usage:**
You can provide session data from a previous session using the `session_data` parameter. The tool will then check for a paywall *as if* it were a logged-in user, which is useful for validating an existing session. **Always use `session_data` for session management** - it's the recommended approach for passing authentication data between tools.

**Example Return:**
```json
{
  "paywall_detected": true,
  "confidence": 95,
  "session_info": {
    "user_data_dir": null,
    "session_data": {...}
  }
}
```
**CRITICAL:** Always use the `session_data` field from `session_info` for passing authentication between tools. Never proceed to scraping without following the workflow sequence.""",
)
async def detect_paywall_tool(
    url: str,
    storage_state_path: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_data: Optional[dict] = None
) -> dict:
    """
    Detects paywall on a webpage using vision analysis and keyword detection.
    
    Args:
        url: The URL to check for paywall.
        storage_state_path: Optional path to a storage_state.json file for pre-authenticated sessions.
        user_agent: Optional custom User-Agent string.
        session_data: Optional in-memory session data dictionary (cookies, localStorage, etc.) - PREFERRED METHOD.
    
    Returns:
        Dict with paywall detection results including confidence, method, and indicators.
    """
    return await detect_paywall(
        url=url,
        storage_state_path=storage_state_path,
        user_data_dir=user_data_dir,
        user_agent=user_agent,
        session_data=session_data
    )

# --- Tool 3: open_login_browser - opens a visible browser window for user login/authentication on paywalled sites ---
@mcp.tool(
    name="open_login_browser",
    description="""🚨 **CRITICAL**: Use this tool **ONLY after** `detect_paywall` has returned `paywall_detected: true`. It handles the human-in-the-loop step of the paywall bypass workflow.

**Pure In-Memory Session Management:**
- Now uses PURE IN-MEMORY session management - no persistent directories created
- Browser sessions are temporary and clean between attempts
- No filesystem dependencies or directory contamination

**Workflow:**
1. Inform the user that a browser window is opening for them to log in
2. Call this tool. It will open a visible browser, allowing the user to manually log in, solve a CAPTCHA, or handle a subscription
3. When the user closes the browser, this tool saves their authenticated session

**🔑 CRITICAL SESSION DATA EXTRACTION:**
This tool returns a JSON object containing `session_data` in the `session_info` field. You **MUST** capture and preserve this session data for subsequent authenticated scraping.

**Example Response Structure:**
```json
{
  "status": "login_session_complete",
  "completion_method": "manual_close",
  "session_info": {
    "user_data_dir": "session_key",
    "session_data": {
      "cookies": [...],
      "origins": [...]
    }
  }
}
```

**⚠️ WARNING: DO NOT LOSE SESSION DATA!**
The `session_data` you receive must be passed to the `scrape_single_url` tool to perform the authenticated scrape. **Always use the `session_data` field** - it contains all necessary authentication information for seamless session management across tools.

**MANDATORY Next Step:**
After this tool completes, you **MUST** call: `scrape_single_url(url="[SAME_URL]", session_data={session_data_from_this_response})`"""
)
async def open_login_browser_tool(
    url: str,
    user_data_dir: Optional[str] = None,
    wait_timeout_seconds: Optional[int] = 420,
    user_agent: Optional[str] = None,
    instructions: Optional[str] = None,
    session_data: Optional[dict] = None
) -> dict:
    """
    Opens a browser window for user login/authentication.
    
    Args:
        url: The URL to open for login (usually the paywalled page).
        wait_timeout_seconds: Maximum time to wait for user login (default: 420 seconds / 7 minutes).
        user_agent: Optional custom User-Agent string.
        instructions: Optional custom message to display to user about what to do.
        session_data: Optional existing session data to pre-populate browser - PREFERRED METHOD.
    
    Returns:
        Dict with login session completion status and session info for subsequent scraping.
    """
    return await open_login_browser(
        url=url,
        user_data_dir=user_data_dir,
        wait_timeout_seconds=wait_timeout_seconds,
        user_agent=user_agent,
        instructions=instructions,
        session_data=session_data
    )

# --- Server Execution ---
if __name__ == "__main__":
    # Force port 8080 for local development, override any environment variable
    server_port = 8080
    port_env = os.environ.get("PORT")
    if port_env:
        print(f"WARNING: Overriding PORT environment variable ({port_env}) with {server_port}", flush=True)
    print(f"Starting FastMCP server on port {server_port}...", flush=True)

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=server_port,
        path="/scraper/",  # Serve MCP tools at this path
    )