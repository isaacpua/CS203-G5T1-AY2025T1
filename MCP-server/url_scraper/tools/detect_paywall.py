# --- Imports ---
import os

# --- Crawl4AI Setup ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.cache_context import CacheMode

# --- URL Normalization ---
from .utils import normalize_url, get_session_info_enhanced

# --- Paywall Detection ---
from .utils import _is_paywall_present

# --- Vision Analysis ---
from .utils import analyze_screenshot_for_paywall

# --- Session Data Management ---
from .utils import apply_session_data_to_context, extract_session_data_from_context


async def detect_paywall(
    url: str,
    storage_state_path: str | None = None,
    user_data_dir: str | None = None,
    user_agent: str | None = None,
    session_data: dict | None = None
) -> dict:
    """
    Detects paywall on a webpage using vision analysis and keyword detection.
    Fast operation that only takes a screenshot and analyzes content for paywall indicators.
    
    Args:
        url: The URL to check for paywall.
        storage_state_path: Optional path to a storage_state.json file for pre-authenticated sessions.
        user_data_dir: Optional path to Chrome user data directory for session persistence.
        user_agent: Optional custom User-Agent string.
        session_data: Optional in-memory session data dictionary (cookies, localStorage, etc.)
    
    Returns:
        Dict with paywall detection results, status, analysis details, and updated session_info.
    """
    url = normalize_url(url)
    try:
        # Get session info using the enhanced helper function
        final_storage_state_path, session_data_to_apply = get_session_info_enhanced(
            url, storage_state_path, user_data_dir, session_data
        )
        
        print(f"🗂️  Using pure in-memory session management (no persistent directories)", flush=True)
        
        # Configure browser for paywall detection (always headless for speed)
        browser_config_dict = {
            "headless": True,
            "browser_type": "chromium",
            "verbose": True
        }
        
        if final_storage_state_path:
            print(f"🔑 Loading session from storage_state: {final_storage_state_path}", flush=True)
            browser_config_dict["storage_state"] = final_storage_state_path
        elif session_data_to_apply:
            print("🔑 Using in-memory session data", flush=True)
            # Pure in-memory: no user_data_dir needed, will apply session data to context later
        else:
            print("⚠️ No session loaded, using fresh session.", flush=True)
            
        browser_config_instance = BrowserConfig(**browser_config_dict)

        config_args = {
            'screenshot': True,  # Always take screenshot for vision analysis
            'cache_mode': CacheMode.BYPASS  # Always get fresh content for accurate detection
        }
        
        if user_agent is not None:
            config_args["user_agent"] = user_agent
        
        crawler_run_config = CrawlerRunConfig(**config_args)
        
        # Perform quick scrape focused on paywall detection
        async with AsyncWebCrawler(config=browser_config_instance) as crawler:
            print(f"🔍 Checking {url} for paywall indicators...", flush=True)
            
            # Apply session data if provided and not using storage_state file
            if session_data_to_apply and not final_storage_state_path:
                context = crawler.crawler_strategy.browser_manager.context
                if context:
                    await apply_session_data_to_context(context, session_data_to_apply, target_url=url)
            
            results_list = await crawler.arun(url=url, config=crawler_run_config)
            result_obj = results_list[0] if results_list else None

        if result_obj and result_obj.success:
            raw_content = result_obj.markdown.raw_markdown if result_obj.markdown else ""
            
            # Keyword-based paywall detection
            paywall_keywords = [
                "subscribe to continue", "subscription required", "premium content",
                "sign in to read", "log in to continue", "create account to read",
                "free articles remaining", "you've reached your", "paywall",
                "unlock this article", "become a member", "join to read", 
                "Become a member to read this story, and all of Medium."
            ]
            
            keyword_detected = any(keyword in raw_content.lower() for keyword in paywall_keywords)
            keyword_indicators = [keyword for keyword in paywall_keywords if keyword in raw_content.lower()]
            
            print(f"📝 Keyword detection: {'Found indicators' if keyword_detected else 'No obvious keywords'}", flush=True)
            
            # Vision-based paywall detection
            vision_analysis = None
            if hasattr(result_obj, 'screenshot') and result_obj.screenshot:
                try:
                    print(f"📸 Screenshot captured! Analyzing with GPT-4o vision...", flush=True)
                    vision_analysis = await analyze_screenshot_for_paywall(result_obj.screenshot, result_obj.url)
                    print(f"👁️  Vision analysis: {'Paywall detected' if vision_analysis.get('paywall_detected') else 'No paywall'} (confidence: {vision_analysis.get('confidence', 0)}%)", flush=True)
                except Exception as e:
                    print(f"⚠️ Vision analysis failed: {str(e)}", flush=True)
                    vision_analysis = {
                        "paywall_detected": False,
                        "confidence": 0,
                        "method": "vision_analysis",
                        "error": f"Vision analysis failed: {str(e)}"
                    }
            else:
                print("⚠️ No screenshot available for vision analysis", flush=True)
                vision_analysis = {
                    "paywall_detected": False,
                    "confidence": 0,
                    "method": "vision_analysis", 
                    "error": "Screenshot not available"
                }
            
            # Use the robust helper function to make the final decision
            paywall_detected, decision_reason, vision_analysis = _is_paywall_present(
                keyword_detected=keyword_detected,
                vision_analysis=vision_analysis,
                raw_content=raw_content
            )
            
            # Determine confidence and method for reporting
            final_confidence = 0
            detection_method = "no_detection"

            if paywall_detected:
                if vision_analysis and vision_analysis.get("paywall_detected"):
                    detection_method = "vision_primary"
                    final_confidence = vision_analysis.get("confidence", 80)
                else:
                    detection_method = "keyword_primary"
                    final_confidence = 75
            else:
                 if vision_analysis and 'False positive' in decision_reason:
                     detection_method = "keyword_override"
                     final_confidence = vision_analysis.get("confidence", 30) # Low confidence in paywall
                 else:
                     detection_method = "no_detection"
                     final_confidence = 20

            # Extract updated session data if using in-memory sessions
            updated_session_data = None
            if session_data_to_apply and not final_storage_state_path:
                context = crawler.crawler_strategy.browser_manager.context
                if context:
                    updated_session_data = await extract_session_data_from_context(context, url)

            return {
                "url": result_obj.url,
                "status": "paywall_detected" if paywall_detected else "no_paywall",
                "paywall_detected": paywall_detected,
                "confidence": final_confidence,
                "detection_method": detection_method,
                "decision_reason": decision_reason,
                "session_info": {
                    "user_data_dir": user_data_dir, # Keep user_data_dir for context
                    "storage_state_path": final_storage_state_path,
                    "session_data": updated_session_data,
                    "domain_based": user_data_dir is None
                },
                "analysis": {
                    "keyword_detection": {
                        "detected": keyword_detected,
                        "indicators": keyword_indicators
                    },
                    "vision_analysis": vision_analysis
                },
                "content_preview": {
                    "length": len(raw_content),
                    "sample": raw_content[:500] + "..." if len(raw_content) > 500 else raw_content
                }
            }
        else:
            return {
                "url": url,
                "status": "error",
                "error": f"Failed to load page: {result_obj.error_message if result_obj else 'No result returned'}",
                "paywall_detected": False,
                "confidence": 0
            }
            
    except Exception as e:
        return {
            "url": url,
            "status": "error", 
            "error": f"Paywall detection failed: {str(e)}",
            "paywall_detected": False,
            "confidence": 0
        }