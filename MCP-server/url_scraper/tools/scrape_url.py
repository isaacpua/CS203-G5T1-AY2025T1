# --- Imports ---
import os

# --- Crawl4AI Setup ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.cache_context import CacheMode

# --- Tenacity Setup - for retrying failed requests ---
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

# --- URL Normalization ---
from .utils import normalize_url, get_session_info_enhanced

# --- Paywall Detection ---
from .utils import _is_paywall_present

# --- Vision Analysis ---
from .utils import analyze_screenshot_for_paywall

# --- Session Data Management ---
from .utils import apply_session_data_to_context, extract_session_data_from_context

# --- Function to scrape a URL ---
async def scrape_url(
    url: str,
    storage_state_path: str | None = None,
    user_data_dir: str | None = None,
    user_agent: str | None = None,
    session_data: dict | None = None,
) -> dict:
    """
    Scrapes a given URL and returns its structured content.
    This tool is focused on pure scraping. It assumes that any necessary
    authentication or paywall bypass has been handled by providing valid
    session data or storage_state_path. It will perform a post-scrape check to verify if a
    paywall is still present, which helps the calling agent detect invalid sessions.

    Args:
        url: The URL to scrape.
        storage_state_path: Optional path to a storage_state.json file for pre-authenticated sessions.
        user_data_dir: Optional path to a Chrome/Chromium user data directory for
                       Crawl4AI's Managed Browser feature.
        user_agent: Optional custom User-Agent string for requests.
        session_data: Optional in-memory session data dictionary (cookies, localStorage, etc.)

    Returns:
        A dictionary containing the scraped URL, status, error (if any),
        structured content (metadata, markdown, media, warnings), vision analysis results,
        and updated session_info.
    """
    # --- Defensive Programming: Handle list input ---
    # If a list is passed by accident, take the first element and log a warning.
    # This makes the tool more robust to client-side errors.
    if isinstance(url, list):
        print(f"⚠️ WARNING: scrape_url received a list of URLs. Processing only the first one: {url[0]}", flush=True)
        url = url[0]
        
    url = normalize_url(url)
    try:
        # Get session info using the enhanced helper function
        final_storage_state_path, session_data_to_apply = get_session_info_enhanced(
            url, storage_state_path, user_data_dir, session_data
        )
        
        print(f"🗂️  Using pure in-memory session management (no persistent directories)", flush=True)
        
        # Configure browser - headless is always true for this focused tool
        headless_mode = True
        use_managed = True

        print(f"🔧 Browser config: headless={headless_mode}, use_managed_browser={use_managed}", flush=True)

        browser_config_dict = {
            "headless": headless_mode,
            "browser_type": "chromium",
            "verbose": True,
            "extra_args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        }
        
        # Initialize flags
        use_temp_storage_file = False
        
        # Load from storage_state if available, no user_data_dir needed for pure in-memory
        if final_storage_state_path:
            print(f"🔑 Loading session from storage_state file: {final_storage_state_path}", flush=True)
            browser_config_dict["storage_state"] = final_storage_state_path
        elif session_data_to_apply:
            print("🔑 Using pure in-memory session data (dict directly to BrowserConfig)", flush=True)
            # PURE IN-MEMORY: Pass storage_state dict directly to BrowserConfig (no temp files!)
            # Clean session data before passing to BrowserConfig
            from .utils import clean_cookies_for_playwright
            
            print(f"🧹 Cleaning session data for direct BrowserConfig usage...", flush=True)
            cleaned_session_data = session_data_to_apply.copy()
            
            # Clean cookies if they exist - get storage state format for BrowserConfig
            if "cookies" in cleaned_session_data and cleaned_session_data["cookies"]:
                print(f"🍪 Original session data has {len(cleaned_session_data['cookies'])} cookies", flush=True)
                # Get cleaned cookies in storage state format for BrowserConfig
                storage_state = clean_cookies_for_playwright(cleaned_session_data["cookies"], return_storage_state=True, target_url=url)
                cleaned_session_data["cookies"] = storage_state.get("cookies", [])
                print(f"🧹 Cleaned session data now has {len(cleaned_session_data['cookies'])} cookies", flush=True)
            
            # Pass dict directly to BrowserConfig (Playwright supports this!)
            browser_config_dict["storage_state"] = cleaned_session_data
        else:
            print("⚠️ No session loaded, using fresh session.", flush=True)
        
        browser_config_instance = BrowserConfig(**browser_config_dict)
        
        config_args = {}
        if user_agent is not None:
            config_args["user_agent"] = user_agent
        
        # Enable screenshot capture for post-scrape paywall verification
        config_args["screenshot"] = True
        
        # ALWAYS bypass the cache for scraping calls to ensure we get the latest
        # state of the page (especially after a login).
        config_args["cache_mode"] = CacheMode.BYPASS
        
        crawler_run_config = CrawlerRunConfig(**config_args)
        
        # This tool performs a direct, headless scrape with retry logic.
        async with AsyncWebCrawler(config=browser_config_instance) as crawler:
            result_obj = None
            
            print(f"🔍 DEBUG: Starting crawler with session data", flush=True)
            print(f"   - Using storage_state: {browser_config_instance.storage_state is not None}", flush=True)
            print(f"   - Storage state path: {browser_config_instance.storage_state}", flush=True)
            
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                reraise=True
            ):
                with attempt:
                    results_list = await crawler.arun(url=url, config=crawler_run_config)
                    result_obj = results_list[0] if results_list else None

        # Process the result
        if result_obj and result_obj.success:
            page_metadata = {}
            media_data_attr = getattr(result_obj, 'media', None)
            metadata_attr = getattr(result_obj, 'metadata', None)

            if metadata_attr and isinstance(metadata_attr, dict):
                page_metadata.update({
                    'title': metadata_attr.get('title'),
                    'description': metadata_attr.get('description'),
                    'keywords': metadata_attr.get('keywords'),
                    'author': metadata_attr.get('author')
                })

            # Paywall, anti-scraping, and CAPTCHA detection
            warning_message = None
            raw_markdown_content = result_obj.markdown.raw_markdown if result_obj.markdown else ""
            
            # Initialize vision analysis result
            vision_analysis = None
            
            # Keyword-based detection first
            paywall_keywords = [
                "subscribe to continue", "subscription required", "premium content",
                "sign in to read", "log in to continue", "create account to read",
                "free articles remaining", "you've reached your", "paywall", "subscription",
                "unlock this article", "become a member", "join to read",
                "limited time offer", "subscribe now", "free trial", "Become a member to read this story, and all of Medium."
            ]
            keyword_detected = any(keyword in raw_markdown_content.lower() for keyword in paywall_keywords)
            
            # Use vision-based paywall detection if screenshot available for verification
            print(f"🔍 Post-scrape verification: Checking for persistent paywall...", flush=True)
            if hasattr(result_obj, 'screenshot') and result_obj.screenshot:
                try:
                    print(f"📸 Screenshot captured! Analyzing with GPT-4o vision...", flush=True)
                    vision_analysis = await analyze_screenshot_for_paywall(result_obj.screenshot, result_obj.url)
                    print(f"👁️  Vision analysis: {'Paywall detected' if vision_analysis.get('paywall_detected') else 'No paywall'} (confidence: {vision_analysis.get('confidence', 0)}%)", flush=True)
                except Exception as e:
                    print(f"⚠️ Vision analysis failed, falling back to keyword detection: {str(e)}", flush=True)
                    vision_analysis = {
                        "paywall_detected": False,
                        "confidence": 0,
                        "method": "vision_analysis",
                        "error": f"Vision analysis failed: {str(e)}"
                    }
            else:
                print("⚠️ Screenshot not available. Possible reasons:", flush=True)
                print(f"   - hasattr(result_obj, 'screenshot'): {hasattr(result_obj, 'screenshot') if result_obj else 'result_obj is None'}", flush=True)
                if result_obj and hasattr(result_obj, 'screenshot'):
                    print(f"   - result_obj.screenshot exists but is empty: {not result_obj.screenshot}", flush=True)
                print("   - Falling back to keyword detection", flush=True)
            
            # Use the robust helper function to make the final decision
            paywall_detected, decision_reason, vision_analysis = _is_paywall_present(
                keyword_detected=keyword_detected,
                vision_analysis=vision_analysis,
                raw_content=raw_markdown_content
            )
            
            # Handle paywall detection logic
            is_using_saved_session = (final_storage_state_path and os.path.exists(final_storage_state_path)) or (session_data_to_apply is not None)
            
            if paywall_detected:
                # AGENT OVERRIDE LOGIC: Trust vision analysis over content length
                # This fixes the core issue where substantial content was incorrectly assumed to mean successful bypass
                content_is_substantial = raw_markdown_content and len(raw_markdown_content) > 1500
                vision_confidence = vision_analysis.get('confidence', 0) if vision_analysis else 0
                vision_detected_paywall = vision_analysis.get('paywall_detected', False) if vision_analysis else False
                
                print(f"🔍 DEBUG: Paywall detected, applying agent override logic:", flush=True)
                print(f"   - Content length: {len(raw_markdown_content)} characters", flush=True)
                print(f"   - Content is substantial (>1500 chars): {content_is_substantial}", flush=True)
                print(f"   - Vision analysis confidence: {vision_confidence}%", flush=True)
                print(f"   - Vision detected paywall: {vision_detected_paywall}", flush=True)
                print(f"   - Using session data: {session_data_to_apply is not None}", flush=True)
                print(f"   - Using storage state file: {final_storage_state_path is not None}", flush=True)
                if raw_markdown_content:
                    print(f"   - Content preview (first 300 chars): {raw_markdown_content[:300]}", flush=True)

                # CRITICAL: Vision analysis takes precedence over content length
                # BUT: If using session data and vision detects high-confidence paywall, session is invalid
                if vision_detected_paywall and vision_confidence >= 75:
                    if session_data_to_apply or final_storage_state_path:
                        print("🚨 SESSION INVALID: Vision analysis detected high-confidence paywall despite using session data.", flush=True)
                        print("🧹 INVALIDATING SESSION: The session may be expired, invalid, or insufficient for this content.", flush=True)
                        status = "session_invalid"
                        warning = (
                            f"Session authentication failed. Vision analysis detected a paywall with {vision_confidence}% confidence "
                            "despite using session data. The session may be expired, invalid, or your account may lack the required "
                            "subscription level. Please re-authenticate."
                        )
                    else:
                        print("🤖 AGENT OVERRIDE: Vision analysis detected high-confidence paywall. Forcing paywall_persistent status.", flush=True)
                        status = "paywall_persistent"
                        warning = (
                            f"Vision analysis detected a paywall with {vision_confidence}% confidence. "
                            "The session may be invalid, expired, or require authentication."
                        )
                elif content_is_substantial and (not vision_detected_paywall or vision_confidence < 75):
                    print("✅ Content is substantial and vision analysis shows low/no paywall confidence. Accepting as successful scrape.", flush=True)
                    warning_message = "Note: Paywall indicators found but content appears complete and vision analysis shows low paywall confidence."
                else:
                    # Short content OR high-confidence vision paywall detection
                    print("❌ Paywall persistent: Short content or high-confidence vision detection.", flush=True)
                    status = "paywall_persistent"
                    warning = (
                        "Paywall is still present after attempting to use a saved session. "
                        "The session may be invalid, expired, or require a higher subscription level."
                    )
                    
                    print(f" Mapped status to: {status}", flush=True)
                    
                    # Extract updated session data if using in-memory sessions
                    updated_session_data = None
                    if session_data_to_apply and (not final_storage_state_path or session_data_to_apply is not None):
                        # Use the same context access logic as above
                        context = None
                        try:
                            if hasattr(crawler, 'browser_manager') and hasattr(crawler.browser_manager, 'context'):
                                context = crawler.browser_manager.context
                            elif hasattr(crawler, 'crawler_strategy') and hasattr(crawler.crawler_strategy, 'browser_manager'):
                                browser_manager = crawler.crawler_strategy.browser_manager
                                if hasattr(browser_manager, 'context'):
                                    context = browser_manager.context
                                elif hasattr(browser_manager, 'browser') and hasattr(browser_manager.browser, 'contexts'):
                                    contexts = browser_manager.browser.contexts
                                    if contexts:
                                        context = contexts[0]
                        except Exception as e:
                            print(f"⚠️ Error accessing context for session extraction: {e}", flush=True)
                        
                        if context:
                            updated_session_data = await extract_session_data_from_context(context, url)
                    
                    return {
                        "url": result_obj.url,
                        "status": status,
                        "error": None, # It's a content access issue, not a technical failure.
                        "session_info": {
                            "user_data_dir": user_data_dir, # Pass user_data_dir as is
                            "storage_state_path": final_storage_state_path,  # Don't expose temp file path
                            "session_data": updated_session_data,
                            "domain_based": user_data_dir is None
                        },
                        "content": {
                            "metadata": page_metadata,
                            "main_text_markdown": raw_markdown_content,
                            "media": media_data_attr if media_data_attr else {"images": [], "audio_files": [], "video_files": []},
                            "warning": warning,
                            "vision_analysis": vision_analysis
                        }
                    }
            
            # If we reach this point, any paywall has been successfully bypassed.
            
            if not raw_markdown_content or len(raw_markdown_content) < 200: # Arbitrary small size
                if url not in ["https://example.com/"]: # Don't warn for example.com, it's known to be small
                    warning_message = "Content is very small or missing. This could indicate an error page, a block, or anti-scraping measures."
            
            captcha_keywords = ["captcha", "are you a robot", "verify human", "recaptcha", "human verification"]
            if result_obj.markdown and any(keyword in raw_markdown_content.lower() for keyword in captcha_keywords):
                current_warning = warning_message + " " if warning_message else ""
                warning_message = current_warning + "Potential CAPTCHA or human verification page detected."
            
            # Extract updated session data if using in-memory sessions
            updated_session_data = None
            if session_data_to_apply and (not final_storage_state_path or session_data_to_apply is not None):
                # Use the same context access logic as above
                context = None
                try:
                    if hasattr(crawler, 'browser_manager') and hasattr(crawler.browser_manager, 'context'):
                        context = crawler.browser_manager.context
                    elif hasattr(crawler, 'crawler_strategy') and hasattr(crawler.crawler_strategy, 'browser_manager'):
                        browser_manager = crawler.crawler_strategy.browser_manager
                        if hasattr(browser_manager, 'context'):
                            context = browser_manager.context
                        elif hasattr(browser_manager, 'browser') and hasattr(browser_manager.browser, 'contexts'):
                            contexts = browser_manager.browser.contexts
                            if contexts:
                                context = contexts[0]
                except Exception as e:
                    print(f"⚠️ Error accessing context for session extraction: {e}", flush=True)
                
                if context:
                    updated_session_data = await extract_session_data_from_context(context, url)
            
            # Build the response content
            response_content = {
                "metadata": page_metadata,
                "main_text_markdown": result_obj.markdown.raw_markdown if result_obj.markdown else "",
                "media": media_data_attr if media_data_attr else {"images": [], "audio_files": [], "video_files": []},
                "warning": warning_message,
                "vision_analysis": vision_analysis
            }
            
            return {
                "url": result_obj.url,
                "status": "success",
                "error": None,
                "session_info": {
                    "user_data_dir": user_data_dir, # Pass user_data_dir as is
                    "storage_state_path": final_storage_state_path,  # Don't expose temp file path
                    "session_data": updated_session_data,
                    "domain_based": user_data_dir is None
                },
                "content": response_content
            }
        elif result_obj: # Crawl happened, but was not successful (e.g., 404)
            status_code = result_obj.metadata.get('status_code') if result_obj.metadata else None
            error_message = result_obj.error_message or "Unknown error during crawling"
            if status_code:
                error_message = f"HTTP {status_code}: {error_message}"
            # Check for specific error messages that might indicate a CAPTCHA even on failure
            warning_message = None
            if result_obj.markdown and any(keyword in result_obj.markdown.raw_markdown.lower() for keyword in ["captcha", "are you a robot", "verify human", "recaptcha"]):
                warning_message = "Potential CAPTCHA or human verification page detected on error page."

            return {
                "url": url,
                "status": "error",
                "error": error_message,
                "content": {
                    "metadata": result_obj.metadata if result_obj.metadata else {},
                    "main_text_markdown": result_obj.markdown.raw_markdown if result_obj.markdown else None,
                    "media": {
                        "images": [],
                        "audio_files": [],
                        "video_files": []
                    },
                    "warning": warning_message
                }
            }
        else: # No result object at all, indicates a failure before crawling could start
            return {
                "url": url,
                "status": "error",
                "error": "Failed to get a result from the crawler. The target might be blocking requests.",
                "content": None
            }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "error": f"An unexpected error occurred: {str(e)}",
            "content": None
        }