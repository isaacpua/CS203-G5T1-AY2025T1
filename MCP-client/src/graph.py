from pydantic import BaseModel
from typing import Annotated, List, Optional
from dotenv import load_dotenv

import os
import json
import base64 # Import the base64 module


from langchain.tools import BaseTool
from langgraph.graph import StateGraph, START, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI
from popup import popup_manager

from services.content_formatter import format_scraped_content_for_display

from typing import Optional


load_dotenv()

class AgentState(BaseModel):
    messages: Annotated[List, add_messages]
    current_session_data: Optional[dict] = None
    last_paywall_url: Optional[str] = None
    data: List[dict] = [] 
    geojson: Optional[dict] = None
    pptxpdf: Optional[dict[str, str]] = None

def build_graph(tools: List[BaseTool] = [], access_token: str = ""):
    system_prompt = """
    Your name is Jarvis. You are a helpful assistant that can use the following tools to help the user.

    When the user sends a request, determine what they want and call the appropriate tool. Do not attempt to solve tasks yourself if a tool exists — always delegate to tools.

    ---

    AVAILABLE TOOLS:
    {tools}

        When a user asks you to perform an action, determine what they want, analyze their request carefully to extract the relevant parameters and call the appropriate tool.
        Do not attempt to solve tasks yourself if a tool exists — always delegate to tools.

        ----------

        Always extract the necessary parameters from the user's message. For example:
        - If they say "greet calvin", call the greet tool with name="calvin"
        - If they say "hello to john", call the greet tool with name="john"
        - If they say to send an email, extract out the subject, body and recipient to call the send mail tool
        - If they say to classify news with keywords, extract any sites or keywords 
        - If they say "open sales_deck.pptx", call launch_ppt tool with ppt_filename="sales_deck.pptx"
        - If they ask "what presentations are available?" or "list available slides", call the `list_ppt_files` tool with no parameters.

        Important behavior rules for build_ppt_from_json tool:
        - When calling `build_ppt_from_json`, always pass the uploaded file contents as `files_content`, using the `pptxpdf` object (if available).
        - Extract the exact name of the zip file generated which should be "uuid_presentation_with_images.zip", if the user wants to send the presentation in an email, call send_email_with_attachment using that file name as attachment name, use subject of "test" and send it to sleongxy@gmail.com
        - If the send_email_with_attachment fails, try again for a maximum of 3 times as it may take a while for the file to load on the backend.
        
        Important behavior rules for classify_news_by_keywords tool:
        - If the user asks to send an email after classifing news, after completion, keep the output with HTML tags, and send an email without attachment using the HTML output as the body, use subject of "NewsLetter" and send it to sleongxy@gmail.com
        
        Important behavior rules for scraping tool:
        - If you use a scraping tool or any content-fetching tool, **do not return the raw scraped content directly to the user**.
        - Never include full HTML, Markdown, or long excerpts unless the user explicitly asks for it.
        - If content is scraped, summarize it briefly or confirm that it was retrieved successfully.
        - Only include structured results (like titles, dates, summaries) if relevant and concise.
        - Always prioritize clarity and brevity in responses when dealing with content from external sources.
        
        Important behavior rules for 'run_analysis':
        - Set `data=...` (do not include actual data, just pass `data=...`)
        - Set `user_prompt` to the exact user request (verbatim)
        - Set `geojson` to the provided object, or `None` if not available
        - correct usage: run_analysis(data=..., user_prompt="the user's exact request", geojson=...)
        - NEVER embed the actual dataset or records inside the tool call. Doing so will cause errors.

        ----------
        
        **Session Management Workflow:**
        When scraping content that may be paywalled, ALWAYS follow this exact sequence:

        1. **Detection Phase**: First call `detect_paywall` to check if authentication is needed
        2. **Authentication Phase**: If paywall detected, call `open_login_browser` and CAPTURE the returned session_data
        3. **Scraping Phase**: Call `scrape_single_url` with the session_data from step 2

        **Critical Session Data Handling:**
        - ALWAYS extract `session_info.session_data` from `open_login_browser` response
        - ALWAYS pass this session_data to `scrape_single_url` using the `session_data` parameter
        - NEVER call `scrape_single_url` without session_data if authentication was required

        **Example Workflow:**
        User: "Scrape this Medium article: [URL]"
        1. detect_paywall(url="[URL]") → returns paywall_detected: true
        2. open_login_browser(url="[URL]") → returns session_info.session_data: {{...}}  
        3. scrape_single_url(url="[URL]", session_data={{...}}) → returns full content

        **Session Failure Handling:**
        - If `scrape_single_url` returns status: "paywall_persistent", the session is invalid
        - In this case, inform the user and offer to retry authentication
        - NEVER repeatedly call tools without informing the user of session failures
        - If session becomes invalid, do NOT reuse the old session_data
        - Always explain to the user why authentication failed and what options they have
        - Common session failure reasons: expired login, insufficient subscription, account restrictions
        
        **Error Recovery Workflow:**
        1. Detect failure (paywall_persistent status)
        2. Inform user about the specific issue
        3. Offer to retry authentication if appropriate
        4. Do NOT automatically retry without user consent

        **IMPORTANT FINAL CONDITION**
        - At the end of the scraping workflow, print out in text a summary of the content scraped.
        
        ----------

        Be concise, professional, and avoid verbose output unless the user requests it.
    """

    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("GPTO3_MINI_DEPLOYMENT_NAME"),
        openai_api_version=os.getenv("GPTO3_MINI_API_VERSION"), # type: ignore
        api_key=os.getenv("GPTO3_MINI_API_KEY"),
        azure_endpoint=os.getenv("GPTO3_MINI_API_BASE"),
        temperature=1 # O3-mini/reasoning models do not support temperature parameter so have to fix this to 1
    )

    def assistant(state: AgentState) -> AgentState:
        # --- 1. Session and Paywall Handling Logic ---
        if state.messages and hasattr(state.messages[-1], 'content'):
            last_message = state.messages[-1]
            
            if hasattr(last_message, 'tool_call_id') and hasattr(last_message, 'name'):
                tool_name = getattr(last_message, 'name', '')
                tool_content = getattr(last_message, 'content', '')
                
                if tool_name == 'open_login_browser' and isinstance(tool_content, str):
                    try:
                        tool_response = json.loads(tool_content)
                        if isinstance(tool_response, dict) and 'session_info' in tool_response:
                            session_info = tool_response.get('session_info', {})
                            if isinstance(session_info, dict) and 'session_data' in session_info:
                                state.current_session_data = session_info['session_data']
                    except (json.JSONDecodeError, KeyError, TypeError):
                        pass
                
                elif tool_name == 'detect_paywall' and isinstance(tool_content, str):
                    try:
                        tool_response = json.loads(tool_content)
                        if isinstance(tool_response, dict) and tool_response.get('paywall_detected'):
                            for msg in reversed(state.messages[:-1]):
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    for tool_call in msg.tool_calls:
                                        if tool_call.get('name') == 'detect_paywall':
                                            url = tool_call.get('args', {}).get('url')
                                            if url:
                                                state.last_paywall_url = url
                                            break
                                    break
                    except (json.JSONDecodeError, KeyError, TypeError):
                        pass
                
                elif tool_name == 'scrape_single_url' and isinstance(tool_content, str):
                    try:
                        tool_response = json.loads(tool_content)
                        if isinstance(tool_response, dict):
                            status = tool_response.get('status')
                            if status in ('paywall_persistent', 'session_invalid'):
                                state.current_session_data = None
                            elif status == 'success':
                                print("🧹 Clearing session data after successful scrape to prevent stale reuse", flush=True)
                                state.current_session_data = None
                                state.last_paywall_url = None
                    except (json.JSONDecodeError, KeyError, TypeError):
                        pass

        # --- 2. Fixed (Idempotent) File Context Injection ---
        # Corrected to use dot notation (state.data instead of state.get('data'))
        if state.data:
            data_message_content = f"The user has uploaded a dataset with {len(state.data)} rows."
            if not any(data_message_content in (getattr(msg, 'content', '')) for msg in state.messages if isinstance(msg, SystemMessage)):
                sample_keys = list(state.data[0].keys())
                column_summary = ", ".join(sample_keys)
                full_message = f"{data_message_content} The columns are: {column_summary}. Use this data to answer the user's query."
                state.messages.insert(-1, SystemMessage(content=full_message))

        # Corrected to use dot notation (state.pptxpdf instead of state.get('pptxpdf'))
        elif state.pptxpdf:
            pptxpdf_message_content = "The user has uploaded a PPTX/PDF file. Use this file to answer the user's query."
            if not any(pptxpdf_message_content in (getattr(msg, 'content', '')) for msg in state.messages if isinstance(msg, SystemMessage)):
                context_text = state.pptxpdf.get("summary", "") # .get() is OK here because pptxpdf is a dict
                full_message = (
                    f"{pptxpdf_message_content}\n\n"
                    f"--- Start of Uploaded File Summary ---\n"
                    f"{context_text}\n"
                    f"--- End of Uploaded File Summary ---"
                )
                state.messages.insert(-1, SystemMessage(content=full_message))

        # --- 3. Core LLM Invocation ---
        safe_messages = [msg for msg in state.messages]
        response = llm.invoke([SystemMessage(content=system_prompt)] + safe_messages)

        # --- 4. Special Data Patching for `run_analysis` ---
        # Corrected to use dot notation
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.get("name") == "run_analysis" and state.data:
                    print(f"[DEBUG] Overriding data in run_analysis tool call with full dataset ({len(state.data)} records)")
                    tool_call.setdefault("args", {})
                    tool_call["args"]["data"] = state.data
                    if state.geojson:
                        tool_call["args"]["geojson"] = state.geojson

        # --- 5. Final State Update ---
        state.messages.append(response)
        
        return state
    
    def formatting_node(state: AgentState) -> AgentState:
        """
        Enhanced formatting node using dedicated GPT-4 service.
        Extracts scraped content from tool responses and formats using content_formatter service.
        """
        print("🎨 Formatting Node: Starting content formatting...")
        
        # Extract tool response from the last message
        last_message = state.messages[-1] if state.messages else None
        if not last_message or not hasattr(last_message, 'content'):
            print("❌ Formatting Node: No valid message content found")
            return state
        
        try:
            # Parse the tool response JSON
            tool_content = getattr(last_message, 'content', '')
            if not isinstance(tool_content, str):
                print("❌ Formatting Node: Tool content is not a string")
                return state
            
            # Parse JSON response from MCP tool
            tool_response = json.loads(tool_content)
            if not isinstance(tool_response, dict):
                print("❌ Formatting Node: Tool response is not a dictionary")
                return state
            
            print(f"📊 Formatting Node: Parsed tool response successfully")
            print(f"   - Status: {tool_response.get('status', 'unknown')}")
            print(f"   - URL: {tool_response.get('url', 'unknown')}")
            
            # Verify this is a successful scrape response
            status = tool_response.get('status')
            if status != 'success':
                print(f"⚠️ Formatting Node: Skipping formatting - status is '{status}', not 'success'")
                return state
            
            # Extract content data
            content_data = tool_response.get('content')
            if not content_data or not isinstance(content_data, dict):
                print("❌ Formatting Node: No valid content data found in tool response")
                return state
            
            # Verify we have markdown content to format
            markdown_text = content_data.get('main_text_markdown', '')
            if not markdown_text or markdown_text.strip() == '':
                print("❌ Formatting Node: No markdown content found to format")
                return state
            
            print(f"📝 Formatting Node: Found content to format ({len(markdown_text)} characters)")
            
            # Format the content using our dedicated service
            try:
                import asyncio
                formatted_content = asyncio.run(format_scraped_content_for_display(tool_response))
                
                # Set popup data with formatted content
                popup_data = {
                    "content": formatted_content,
                }
                popup_manager.set_popup_data(popup_data)
                
                print(f"✅ Formatting Node: Successfully formatted content ({len(formatted_content)} characters)")
                print(f"📤 Formatting Node: Popup data set for display")
                
            except Exception as formatting_error:
                print(f"❌ Formatting Node: Content formatting failed: {formatting_error}")
                print(f"🔄 Formatting Node: Skipping formatting - content will not be available in popup")
                # Don't fail the entire workflow - just skip formatting
                
        except json.JSONDecodeError as e:
            print(f"❌ Formatting Node: Failed to parse tool response JSON: {e}")
        except Exception as e:
            print(f"❌ Formatting Node: Unexpected error during formatting: {e}")
        
        return state

    def clean_session_data(session_data):
        """
        Clean session data to remove malformed cookies that would cause Playwright errors.
        Filters out cookies missing required domain/path information.
        """
        if not isinstance(session_data, dict) or 'cookies' not in session_data:
            return session_data
        
        original_cookies = session_data.get('cookies', [])
        cleaned_cookies = []
        
        for cookie in original_cookies:
            if not isinstance(cookie, dict):
                continue
                
            # Check required fields for Playwright
            name = cookie.get('name')
            domain = cookie.get('domain')
            
            if not name or not isinstance(name, str) or not domain or not isinstance(domain, str):
                continue
                
            # Convert value to string if needed
            if not isinstance(cookie.get('value'), str):
                cookie['value'] = str(cookie.get('value', ''))
                
            # Ensure path exists - default to root if missing
            if not cookie.get('path') or not isinstance(cookie.get('path'), str):
                cookie['path'] = '/'
            
            # Clean up expires field
            if 'expires' in cookie:
                expires = cookie['expires']
                if expires == -1 or not isinstance(expires, (int, float)) or expires < 0:
                    del cookie['expires']
            
            # Ensure boolean fields are actually booleans
            for bool_field in ['httpOnly', 'secure']:
                if bool_field in cookie:
                    cookie[bool_field] = bool(cookie[bool_field])
            
            # Validate sameSite values
            if 'sameSite' in cookie:
                valid_same_site = ['Strict', 'Lax', 'None']
                if cookie['sameSite'] not in valid_same_site:
                    del cookie['sameSite']
            
            cleaned_cookies.append(cookie)
        
        # Create cleaned session data
        cleaned_session_data = session_data.copy()
        cleaned_session_data['cookies'] = cleaned_cookies
        
        return cleaned_session_data
    
    def session_validator(state: AgentState) -> AgentState:
        """
        Session validation node that runs after tool calls to ensure proper session management.
        Only applies session logic to scraping tools to avoid affecting other workflows.
        Checks for captured session data and provides context for subsequent scraping calls.
        """
        # Only apply session validation to scraping-related tools
        last_message = state.messages[-1] if state.messages else None
        if not last_message or not hasattr(last_message, 'name'):
            return state
            
        tool_name = getattr(last_message, 'name', '')
        scraping_tools = {'detect_paywall', 'open_login_browser', 'scrape_single_url'}
        
        # Skip session validation for non-scraping tools
        if tool_name not in scraping_tools:
            print(f"🔄 Session Validator: Skipping validation for non-scraping tool: {tool_name}", flush=True)
            return state
        
        print(f"🔍 Session Validator: Processing {tool_name} response", flush=True)
        
        # Check if we have session data and a paywall URL that needs scraping
        has_session_data = state.current_session_data is not None
        has_paywall_url = state.last_paywall_url is not None
        
        # Check if the last tool call was open_login_browser (just got session data)
        just_authenticated = (tool_name == 'open_login_browser')
        
        # If we just authenticated and have session data, inject guidance for next scraping call
        if just_authenticated and has_session_data and has_paywall_url:
            session_guidance = SystemMessage(
                content=f"[SESSION CONTEXT] You have successfully captured session data from user authentication. "
                f"The URL '{state.last_paywall_url}' required authentication and you now have valid session_data available. "
                f"For your next scrape_single_url call, you MUST include the session_data parameter to access the authenticated content. "
                f"Remember: session_data is available in your current context - use it for the scraping call."
            )
            state.messages.append(session_guidance)
        
        # Check for session failures and paywall_persistent status
        elif has_session_data and not just_authenticated:
            # Look for recent scrape tool calls and their responses
            recent_scrape_call = False
            session_failure_detected = False
            
            # First check if the current message is a session failure (immediate detection)
            if tool_name == 'scrape_single_url' and hasattr(last_message, 'content'):
                try:
                    tool_content = getattr(last_message, 'content', '')
                    if isinstance(tool_content, str):
                        tool_response = json.loads(tool_content)
                        if isinstance(tool_response, dict):
                            status = tool_response.get('status')
                            if status == 'paywall_persistent' or status == 'session_invalid':
                                print(f"🚨 Session Validator: IMMEDIATE session failure detected - status: {status}", flush=True)
                                session_failure_detected = True
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    print(f"⚠️ Session Validator: Error parsing current tool response: {e}", flush=True)
            
            # If not found in current message, check recent history
            if not session_failure_detected:
                for msg in reversed(state.messages[-5:]):  # Check last 5 messages for broader context
                    # Check for tool calls without session data
                    if (hasattr(msg, 'tool_calls') and msg.tool_calls):
                        for tool_call in msg.tool_calls:
                            if tool_call.get('name') == 'scrape_single_url':
                                args = tool_call.get('args', {})
                                if 'session_data' not in args or not args.get('session_data'):
                                    recent_scrape_call = True
                                break
                    
                    # Check for scraping failures indicating session problems
                    elif (hasattr(msg, 'tool_call_id') and hasattr(msg, 'name') and 
                          getattr(msg, 'name', '') == 'scrape_single_url'):
                        try:
                            tool_content = getattr(msg, 'content', '')
                            if isinstance(tool_content, str):
                                tool_response = json.loads(tool_content)
                                if isinstance(tool_response, dict):
                                    status = tool_response.get('status')
                                    error_value = tool_response.get('error', '')
                                    error_msg = (error_value or '').lower()  # Handle None values safely
                                    
                                    # Check for various session failure indicators
                                    if (status == 'paywall_persistent' or 
                                        status == 'session_invalid' or
                                        status == 'error' and ('cookie' in error_msg or 
                                                              'session' in error_msg or 
                                                              'browser context' in error_msg)):
                                        print(f"🚨 Session Validator: Historical session failure detected - status: {status}", flush=True)
                                        session_failure_detected = True
                                        break
                        except (json.JSONDecodeError, KeyError, TypeError):
                            pass
            
            # Handle different failure scenarios
            if session_failure_detected:
                # Session is invalid - clear ALL session state and prompt for re-authentication
                print("🧹 Session Validator: CRITICAL - Session failure detected, cleaning up state", flush=True)
                print(f"   - Clearing current_session_data: {'✅ Had data' if state.current_session_data else '❌ Already None'}", flush=True)
                print(f"   - Clearing last_paywall_url: {'✅ Had URL' if state.last_paywall_url else '❌ Already None'}", flush=True)
                
                state.current_session_data = None
                state.last_paywall_url = None  # Clear paywall URL to force fresh detection
                
                failure_guidance = SystemMessage(
                    content="[SESSION FAILURE] The scraping failed due to session/authentication issues. "
                    "This could be caused by: expired cookies, invalid session data, or insufficient subscription access. "
                    "You should inform the user that the authentication session is no longer valid and offer to retry "
                    "the authentication process if they wish to continue. Do NOT attempt to scrape again with the same session data. "
                    "All session data has been cleared and a fresh authentication will be needed."
                )
                state.messages.append(failure_guidance)
                print("🚨 Session Validator: User guidance added for session failure", flush=True)
                
            elif recent_scrape_call:
                # Scrape call made without session data - suggest using it
                print("💡 Session Validator: Scrape call without session data detected, providing reminder", flush=True)
                session_reminder = SystemMessage(
                    content="[SESSION REMINDER] You have valid session_data available from previous authentication. "
                    "If the scraping result shows paywalled content, retry the scrape_single_url call with the session_data parameter."
                )
                state.messages.append(session_reminder)
            else:
                print("✅ Session Validator: No session issues detected, maintaining current state", flush=True)
        
        # Log final session state for debugging
        if has_session_data or has_paywall_url:
            print(f"📊 Session Validator: Final state - session_data: {'✅' if state.current_session_data else '❌'}, paywall_url: {'✅' if state.last_paywall_url else '❌'}", flush=True)
        
        return state
            

    if tools:
        llm = llm.bind_tools(tools)
        # Enhanced tool schema processing with session management emphasis
        tools_descriptions = []
        
        def enhance_tool_description(tool):
            """Enhanced tool description formatter with session management emphasis"""
            tool_info = f"Tool: {tool.name}\nDescription: {tool.description}"
            
            # Add enhanced parameter schema if available
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema_str = str(tool.args_schema)
                
                # Highlight session_data parameter if present
                if 'session_data' in schema_str:
                    schema_str = schema_str.replace(
                        'session_data', 
                        '🔑 session_data [CRITICAL FOR AUTHENTICATED SCRAPING]'
                    )
                
                tool_info += f"\nParameters: {schema_str}"
            
            # Add session-specific enhancements for scraping tools
            if tool.name == 'scrape_single_url':
                tool_info += "\n\n🔑 SESSION MANAGEMENT CRITICAL:"
                tool_info += "\n- ALWAYS use session_data parameter when scraping URLs that required authentication"
                tool_info += "\n- session_data comes from open_login_browser tool responses"
                tool_info += "\n- Example: scrape_single_url(url='https://example.com', session_data={{...}})"
                tool_info += "\n- Without session_data on paywalled content = FAILURE"
                
            elif tool.name == 'open_login_browser':
                tool_info += "\n\n🔑 SESSION OUTPUT CRITICAL:"
                tool_info += "\n- This tool returns session_info.session_data in the response"
                tool_info += "\n- You MUST extract and save this session_data for subsequent scraping"
                tool_info += "\n- Example response: {{'session_info': {{'session_data': {{...}}}}}}"
                tool_info += "\n- Pass session_data to scrape_single_url immediately after"
                
            elif tool.name == 'detect_paywall':
                tool_info += "\n\n🔑 WORKFLOW ENTRY POINT:"
                tool_info += "\n- ALWAYS call this FIRST before any scraping attempt"
                tool_info += "\n- If paywall_detected: true → call open_login_browser next"
                tool_info += "\n- If paywall_detected: false → call scrape_single_url directly"
                tool_info += "\n- Can also use session_data parameter to test existing sessions"
            
            return tool_info
      
        # Process each tool with enhanced descriptions
        for tool in tools:
            enhanced_description = enhance_tool_description(tool)
            tools_descriptions.append(enhanced_description)
        
        # Add session workflow examples to the tool descriptions
        session_workflow_examples = """

📋 SESSION WORKFLOW EXAMPLES:

Example 1 - New Paywall Article:
User: "Scrape this Medium article"
1. detect_paywall(url="...") → {{paywall_detected: true}}
2. open_login_browser(url="...") → {{session_info: {{session_data: {{...}}}}}}
3. scrape_single_url(url="...", session_data={{...}}) → {{status: "success", content: "..."}}

Example 2 - Public Article:
User: "Scrape this blog post"
1. detect_paywall(url="...") → {{paywall_detected: false}}
2. scrape_single_url(url="...") → {{status: "success", content: "..."}}

Example 3 - Session Failure Recovery:
1. scrape_single_url(url="...", session_data={{...}}) → {{status: "paywall_persistent"}}
2. Inform user: "Session expired, would you like to re-authenticate?"
3. If yes: open_login_browser(url="...") → get new session_data
4. scrape_single_url(url="...", session_data={{NEW_SESSION}}) → success

⚠️  CRITICAL SESSION RULES:
- session_data is a dictionary object, not a string
- Always extract session_data from open_login_browser responses
- Never call scrape_single_url without session_data if authentication was required
- Clear/discard session_data if you receive paywall_persistent status
"""
        
        tools_descriptions.append(session_workflow_examples)
        system_prompt = system_prompt.format(tools="\n\n".join(tools_descriptions), access_token= access_token)
    
    builder = StateGraph(AgentState)

    builder.add_node("Jarvis", assistant)
    builder.add_node(ToolNode(tools))
    builder.add_node("SessionValidator", session_validator)

    builder.add_edge(START, "Jarvis")
    builder.add_conditional_edges(
        "Jarvis",
        tools_condition,
    )
    # Route tools through session validator first
    builder.add_edge("tools", "SessionValidator")

    builder.add_node("Formatting", formatting_node)
    builder.add_conditional_edges(
        "SessionValidator",
        need_formatting_condition,
        {
            True: "Formatting",
            False: "Jarvis"
        }
    )
    builder.add_edge("Formatting", "Jarvis")

    return builder.compile(checkpointer=MemorySaver())

def need_formatting_condition(state: AgentState) -> bool:
    """
    Determines if content should be formatted. Only formats successful scrape results.
    """
    last_message = state.messages[-1] if state.messages else None
    
    # Check if this is a scrape tool response
    if (hasattr(last_message, "tool_call_id") and 
        hasattr(last_message, "name") and 
        "scrape" in getattr(last_message, "name")):
        
        # Check if the scraping was actually successful
        try:
            tool_content = getattr(last_message, 'content', '')
            if isinstance(tool_content, str):
                tool_response = json.loads(tool_content)
                if isinstance(tool_response, dict):
                    status = tool_response.get('status')
                    
                    # Only format if scraping was successful
                    if status == 'success':
                        return True
                    else:
                        return False
        except (json.JSONDecodeError, KeyError, TypeError):
            return False
    
    return False