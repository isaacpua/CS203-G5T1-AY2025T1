# --- Imports ---
import os
import asyncio
import time

# --- Crawl4AI Setup ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# --- URL Normalization ---
from .utils import normalize_url, get_session_info_enhanced

# --- Session Data Management ---
from .utils import extract_session_data_from_context

# --- Function to open login browser ---
async def open_login_browser(
    url: str,
    user_data_dir: str | None = None,
    wait_timeout_seconds: int = 420,
    user_agent: str | None = None,
    instructions: str | None = None,
    session_data: dict | None = None
) -> dict:
    """
    Opens a visible browser window for user login/authentication.
    
    Args:
        url: The URL to open for login.
        user_data_dir: Optional path to Chrome user data directory or session key.
        wait_timeout_seconds: Maximum time to wait for user login.
        user_agent: Optional custom User-Agent string.
        instructions: Optional custom message to display to user.
        session_data: Optional existing session data to pre-populate browser.
    
    Returns:
        Dict with login session completion status and session info, including session_data.
    """
    url = normalize_url(url)
    import asyncio
    
    # Use enhanced session info to handle both file-based and in-memory sessions
    storage_state_path, existing_session_data = get_session_info_enhanced(
        url, None, user_data_dir, session_data
    )
    
    # Check if user_data_dir is a session key format (contains ':')
    is_session_key = user_data_dir and ':' in user_data_dir
    
    start_time = time.time()
    completion_method = "error"
    error_message = "An unknown error occurred."
    extracted_session_data = {}
    
    # An asyncio.Event to signal when the browser is closed by the user
    browser_closed_event = asyncio.Event()

    # Provide a default User-Agent if none is specified to avoid error in BrowserConfig
    final_user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

    # PURE IN-MEMORY: No user_data_dir needed for browser config
    browser_config = BrowserConfig(
        headless=False,
        use_managed_browser=False,  # We are managing the browser manually
        browser_type="chromium",
        user_agent=final_user_agent
    )
    
    # The run config is mostly a dummy here, as we control the flow
    interactive_run_config = CrawlerRunConfig(
        user_agent=final_user_agent,
        # We don't use the delay, but set it for completeness
        delay_before_return_html=wait_timeout_seconds 
    )

    user_instructions = instructions or (
        "A browser window has been opened for you. "
        "Please complete any necessary login or CAPTCHA. "
        "Close the browser window when you are finished."
    )
    
    print("--- Starting Interactive Login Session ---", flush=True)
    print(f"URL: {url}", flush=True)
    print(f"Session mode: Pure in-memory (no persistent directories)", flush=True)
    print(f"Timeout: {wait_timeout_seconds} seconds", flush=True)
    print(user_instructions, flush=True)

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # We must get the page from the strategy's browser_manager
            page, context = await crawler.crawler_strategy.browser_manager.get_page(interactive_run_config)
            
            print("... Attaching close listener to browser page ...", flush=True)

            # Apply existing session data if provided (either from parameter or retrieved)
            session_to_apply = session_data or existing_session_data
            if session_to_apply:
                print("🔑 Applying existing session data to browser...", flush=True)
                from .utils import apply_session_data_to_context
                await apply_session_data_to_context(context, session_to_apply, target_url=url)
            
            # Set the event when the page's 'close' event fires.
            page.on("close", lambda: browser_closed_event.set())
            
            # Navigate the page to the target URL
            await page.goto(url)

            print("🖥️  Browser is open. Waiting for you to complete login and close the window...", flush=True)

            # Create tasks to wait for either the browser close event or our timeout
            browser_closed_task = asyncio.create_task(browser_closed_event.wait())
            timeout_task = asyncio.create_task(asyncio.sleep(wait_timeout_seconds))

            # Wait for whichever task completes first
            done, pending = await asyncio.wait(
                {browser_closed_task, timeout_task},
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel the other, still-pending task
            for task in pending:
                task.cancel()

            # CRITICAL FIX: Check browser closure status BEFORE extracting session data
            if browser_closed_task in done:
                print("✅ Browser window closed by user.", flush=True)
                completion_method = "manual_close"
                
                # Extract session data only after confirming successful browser closure
                try:
                    print("🔄 Extracting session data from valid browser context...", flush=True)
                    # Add timeout to prevent hanging on session extraction
                    extracted_session_data = await asyncio.wait_for(
                        extract_session_data_from_context(context, url),
                        timeout=30.0  # 30 second timeout for session extraction
                    )
                    print(f"✅ Extracted session data with {len(extracted_session_data.get('cookies', []))} cookies", flush=True)
                except asyncio.TimeoutError:
                    print("⚠️ Session extraction timed out, using empty session data", flush=True)
                    extracted_session_data = {}
                except Exception as e:
                    print(f"⚠️ Session extraction failed: {e}, using empty session data", flush=True)
                    extracted_session_data = {}
                
                # Only save to file if not using session key format (backward compatibility)
                if not is_session_key and storage_state_path:
                    print(f"💾 Saving session state to {storage_state_path}...", flush=True)
                    await context.storage_state(path=storage_state_path)
                    print("... Session state saved.", flush=True)
                else:
                    print("💾 Session data extracted for in-memory storage.", flush=True)
            else:
                print("⏰ Timeout reached.", flush=True)
                completion_method = "timeout"
                
                # For timeout case, attempt session extraction with shorter timeout and more error tolerance
                try:
                    print("🔄 Attempting session extraction on timeout (with reduced timeout)...", flush=True)
                    extracted_session_data = await asyncio.wait_for(
                        extract_session_data_from_context(context, url),
                        timeout=10.0  # Shorter timeout for timeout scenarios
                    )
                    print(f"✅ Extracted session data with {len(extracted_session_data.get('cookies', []))} cookies", flush=True)
                except (asyncio.TimeoutError, Exception) as e:
                    print(f"⚠️ Session extraction failed on timeout ({e}), using empty session data", flush=True)
                    extracted_session_data = {}
                
                # Only save to file if not using session key format (backward compatibility)
                if not is_session_key and storage_state_path:
                    print(f"💾 Saving session state to {storage_state_path}...", flush=True)
                    await context.storage_state(path=storage_state_path)
                    print("... Session state saved on timeout.", flush=True)
                else:
                    print("💾 Session data extracted for in-memory storage (timeout).", flush=True)

    except Exception as e:
        print(f"❌ An error occurred in open_login_browser: {e}", flush=True)
        completion_method = "error"
        error_message = str(e)

    finally:
        # Ensure the crawler's resources are cleaned up if it was initialized
        if 'crawler' in locals() and crawler.ready:
            await crawler.close()
            
        end_time = time.time()
        duration = int(end_time - start_time)

        # Construct response based on whether we're using session keys or file paths
        response = {
            "status": "login_session_complete",
            "completion_method": completion_method,
            "duration_seconds": duration,
            "session_info": {
                "user_data_dir": user_data_dir,  # Return original user_data_dir (session key or path)
                "session_data": extracted_session_data,
                "domain_based": True
            }
        }
        
        # Only include storage_state_path for backward compatibility with file-based sessions
        if not is_session_key and storage_state_path:
            response["session_info"]["storage_state_path"] = storage_state_path
            
        if completion_method == "error":
            response["error_message"] = error_message
            
        return response