# --- Imports ---
import os
from dotenv import load_dotenv
import re

# --- Crawl4AI Setup ---
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, UndetectedAdapter, LLMConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai import JsonXPathExtractionStrategy
from crawl4ai.content_filter_strategy import LLMContentFilter
from crawl4ai.content_filter_strategy import PruningContentFilter



from bs4 import BeautifulSoup


from openai import AsyncOpenAI


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


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY not set in environment")


try:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    model_to_use = "gpt-4o-mini"
    print("OpenAI Client init!")
except Exception as e:
    print(f"Failed to initialize standard OpenAI client: {e}")
    client = None




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
        

        # Configure browser - headless mode can be detected easier
        headless_mode = True
        use_managed = True
        print(f"🔧 Browser config: headless={headless_mode}, use_managed_browser={use_managed}", flush=True)
        browser_config = BrowserConfig(
            headless = headless_mode,
            browser_type ="chromium",
            verbose = True,
            # "extra_args": [
            #     "--disable-blink-features=AutomationControlled",
            #     "--disable-dev-shm-usage",
            #     "--no-sandbox"
            # ],
            user_agent = user_agent,
            text_mode = True
        )
        
        

        # Initialize flags
        # use_temp_storage_file = False
        
        # Load from storage_state if available, no user_data_dir needed for pure in-memory
        # if final_storage_state_path:
        #     print(f"🔑 Loading session from storage_state file: {final_storage_state_path}", flush=True)
        #     browser_config_dict["storage_state"] = final_storage_state_path
        # elif session_data_to_apply:
        #     print("🔑 Using pure in-memory session data (dict directly to BrowserConfig)", flush=True)
        #     # PURE IN-MEMORY: Pass storage_state dict directly to BrowserConfig (no temp files!)
        #     # Clean session data before passing to BrowserConfig
        #     from .utils import clean_cookies_for_playwright
            
        #     print(f"🧹 Cleaning session data for direct BrowserConfig usage...", flush=True)
        #     cleaned_session_data = session_data_to_apply.copy()
            
        #     # Clean cookies if they exist - get storage state format for BrowserConfig
        #     if "cookies" in cleaned_session_data and cleaned_session_data["cookies"]:
        #         print(f"🍪 Original session data has {len(cleaned_session_data['cookies'])} cookies", flush=True)
        #         # Get cleaned cookies in storage state format for BrowserConfig
        #         storage_state = clean_cookies_for_playwright(cleaned_session_data["cookies"], return_storage_state=True, target_url=url)
        #         cleaned_session_data["cookies"] = storage_state.get("cookies", [])
        #         print(f"🧹 Cleaned session data now has {len(cleaned_session_data['cookies'])} cookies", flush=True)
            
        #     # Pass dict directly to BrowserConfig (Playwright supports this!)
        #     browser_config_dict["storage_state"] = cleaned_session_data
        # else:
        #     print("⚠️ No session loaded, using fresh session.", flush=True)
        


        # Create the undetected adapter
        undetected_adapter = UndetectedAdapter()
        # Create the crawler strategy with undetected adapter
        crawler_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=browser_config,
            browser_adapter=undetected_adapter
        )



        llm_filter = LLMContentFilter(
            llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=OPENAI_API_KEY),
            instruction="""
                Give me the latest tariff events and news in the format of a newsletter. I only want news on actual tariff changes. Format the ouptut as clean markdown with proper headers for specific news events.
            """,
            chunk_token_threshold = 512,
            verbose = True
        )
        bm25_filter = BM25ContentFilter(
            user_query="tariff tariffs",
            bm25_threshold=0.5,
            language="english"
        )
        prune_filter = PruningContentFilter(
            threshold = 0.5,
            threshold_type = "dynamic",
            min_word_threshold = 2
        )
        md_generator = DefaultMarkdownGenerator(
            content_source="cleaned_html",
            content_filter=prune_filter,
            options={"ignore_links": False}
        )





        # Create a chain of filters
        filter_chain = FilterChain([
            # Only follow URLs with specific patterns
            # URLPatternFilter(patterns=["https://finance.yahoo.com/news/*"]),

            # Only crawl specific domains
            DomainFilter(
                allowed_domains=["finance.yahoo.com"],
            ),
        ])
        scorer = KeywordRelevanceScorer(
            keywords=["tariff", "tariffs"],
            weight=0.7
        )
        # Configure the strategy
        strategy = BestFirstCrawlingStrategy(
            max_depth=1,
            include_external=False,
            url_scorer=scorer,
            # filter_chain=filter_chain,
            max_pages=5             # Maximum number of pages to crawl (optional)
        )
        



        # schema = {
        #     "name": "Tariff extractor",
        #     "baseSelector": "//h2[text() = 'Tariffs']/..",
        #     "fields": [
        #         {
        #             "name": "p elements",
        #             "selector": "//p",
        #             "type": "text"
        #         }
        #     ]
        # }
        # extraction_strategy = JsonXPathExtractionStrategy(
        #     schema = schema,
        #     verbose = True
        # )



        crawler_run_config = CrawlerRunConfig(
            cache_mode = CacheMode.BYPASS,
            verbose = True,
            # simulate_user =  True,
            markdown_generator = md_generator,
            # extraction_strategy = extraction_strategy,
            # deep_crawl_strategy = strategy,
            stream = False
        )





        # This tool performs a direct, headless scrape with retry logic.
        async with AsyncWebCrawler(crawler_strategy=crawler_strategy,config=browser_config) as crawler:
            print(f"🔍 DEBUG: Starting crawler with session data", flush=True)
            print(f"   - Using storage_state: {browser_config.storage_state is not None}", flush=True)
            print(f"   - Storage state path: {browser_config.storage_state}", flush=True)
            
            
            print("Attempting crawl!")
            results_list = await crawler.arun(url=url, config=crawler_run_config)
            # for result in results_list:
            result = results_list[0]
            if not result.success:
                print(f"Crawl failed: {result.error_message}")
                print(f"Status code: {result.status_code}")
            
            # extract links
            # soup = BeautifulSoup(result.cleaned_html, 'html.parser')
            # output = soup.find_all("h2", string="Tariffs")[0]
            # for parent in output.parents:
            #     print(parent.name)
            #     if parent.name == "section":
            #         print("Found section parent!")
            #         output = parent
            #         break
            
            # split text
            # gud_md = result.markdown.raw_markdown
            # split_index = gud_md.find("## Tariffs")
            # if split_index != -1: # found the target
            #     gud_md = gud_md[split_index:]
            # split_index = gud_md.find("(https://finance.yahoo.com/)")
            # if split_index != -1: # found the target
            #     gud_md = gud_md[:split_index]

            # gud_md = re.split("## Tariffs", gud_md)[1]
            # gud_md = re.split(r"\[\s*\]\(https://finance\.yahoo\.com/\)", gud_md)[0]
            


            gpt_response = None
            # print("Asking gpt to mess with fit md...")
            # # llm_chunks = llm_filter.filter_content(result.markdown.fit_markdown)
            # # llm_output = "\n".join(llm_chunks)
            # gpt_response = await client.responses.create(
            #     model = model_to_use,
            #     input = "Tell me a joke!"
            # )
            # print(gpt_response)

            response = {
                "url": result.url,
                "raw_html": result.html,
                "cleaned_html": result.cleaned_html,
                "fit_html": result.fit_html,
                "raw_markdown": result.markdown.raw_markdown,
                # "good_markdown": gud_md,
                "fit_markdown": result.markdown.fit_markdown,
                "llm_output": gpt_response
            }
            score = result.metadata.get("score", 0)
            depth = result.metadata.get("depth", 0)
            print(f"Depth: {depth} | Score: {score:.2f} | {result.url}")
            # async for crawled in await crawler.arun(url=url, config=crawler_run_config):
            #     result = {
            #         "url": crawled.url,
            #         "cleaned_html": crawled.cleaned_html
            #     }
            #     results.append(result)
            #     score = crawled.metadata.get("score", 0)
            #     depth = crawled.metadata.get("depth", 0)
            #     print(f"Depth: {depth} | Score: {score:.2f} | {crawled.url}")
        
        return response

        # Process the result
        # if result_obj and result_obj.success:
        #     page_metadata = {}
        #     media_data_attr = getattr(result_obj, 'media', None)
        #     metadata_attr = getattr(result_obj, 'metadata', None)

        #     if metadata_attr and isinstance(metadata_attr, dict):
        #         page_metadata.update({
        #             'title': metadata_attr.get('title'),
        #             'description': metadata_attr.get('description'),
        #             'keywords': metadata_attr.get('keywords'),
        #             'author': metadata_attr.get('author')
        #         })

        #     # Paywall, anti-scraping, and CAPTCHA detection
        #     warning_message = None
        #     raw_markdown_content = result_obj.markdown.raw_markdown if result_obj.markdown else ""            
        #     if not raw_markdown_content or len(raw_markdown_content) < 200: # Arbitrary small size
        #         if url not in ["https://example.com/"]: # Don't warn for example.com, it's known to be small
        #             warning_message = "Content is very small or missing. This could indicate an error page, a block, or anti-scraping measures."
            
        #     captcha_keywords = ["captcha", "are you a robot", "verify human", "recaptcha", "human verification"]
        #     if result_obj.markdown and any(keyword in raw_markdown_content.lower() for keyword in captcha_keywords):
        #         current_warning = warning_message + " " if warning_message else ""
        #         warning_message = current_warning + "Potential CAPTCHA or human verification page detected."
            
        #     # Extract updated session data if using in-memory sessions
        #     updated_session_data = None
        #     if session_data_to_apply and (not final_storage_state_path or session_data_to_apply is not None):
        #         # Use the same context access logic as above
        #         context = None
        #         try:
        #             if hasattr(crawler, 'browser_manager') and hasattr(crawler.browser_manager, 'context'):
        #                 context = crawler.browser_manager.context
        #             elif hasattr(crawler, 'crawler_strategy') and hasattr(crawler.crawler_strategy, 'browser_manager'):
        #                 browser_manager = crawler.crawler_strategy.browser_manager
        #                 if hasattr(browser_manager, 'context'):
        #                     context = browser_manager.context
        #                 elif hasattr(browser_manager, 'browser') and hasattr(browser_manager.browser, 'contexts'):
        #                     contexts = browser_manager.browser.contexts
        #                     if contexts:
        #                         context = contexts[0]
        #         except Exception as e:
        #             print(f"⚠️ Error accessing context for session extraction: {e}", flush=True)
                
        #         if context:
        #             updated_session_data = await extract_session_data_from_context(context, url)
            




        #     # Build the response content
        #     # response_content = {
        #     #     "metadata": page_metadata,
        #     #     "main_text_markdown": result_obj.markdown.fit_markdown if result_obj.markdown else "",
        #     #     "cleaned_html": result_obj.cleaned_html,
        #     #     # "media": media_data_attr if media_data_attr else {"images": [], "audio_files": [], "video_files": []},
        #     #     "warning": warning_message,
        #     #     # "vision_analysis": vision_analysis
        #     # }

            
        #     return {
        #         "url": result_obj.url,
        #         "status": "success",
        #         "error": None,
        #         "session_info": {
        #             "user_data_dir": user_data_dir, # Pass user_data_dir as is
        #             "storage_state_path": final_storage_state_path,  # Don't expose temp file path
        #             # "session_data": updated_session_data,
        #             "domain_based": user_data_dir is None
        #         },
        #         "content": response_content
        #     }
        # elif result_obj: # Crawl happened, but was not successful (e.g., 404)
        #     status_code = result_obj.metadata.get('status_code') if result_obj.metadata else None
        #     error_message = result_obj.error_message or "Unknown error during crawling"
        #     if status_code:
        #         error_message = f"HTTP {status_code}: {error_message}"
        #     # Check for specific error messages that might indicate a CAPTCHA even on failure
        #     warning_message = None
        #     if result_obj.markdown and any(keyword in result_obj.markdown.raw_markdown.lower() for keyword in ["captcha", "are you a robot", "verify human", "recaptcha"]):
        #         warning_message = "Potential CAPTCHA or human verification page detected on error page."

        #     return {
        #         "url": url,
        #         "status": "error",
        #         "error": error_message,
        #         "content": {
        #             "metadata": result_obj.metadata if result_obj.metadata else {},
        #             "main_text_markdown": result_obj.markdown.raw_markdown if result_obj.markdown else None,
        #             "media": {
        #                 "images": [],
        #                 "audio_files": [],
        #                 "video_files": []
        #             },
        #             "warning": warning_message
        #         }
        #     }
        # else: # No result object at all, indicates a failure before crawling could start
        #     return {
        #         "url": url,
        #         "status": "error",
        #         "error": "Failed to get a result from the crawler. The target might be blocking requests.",
        #         "content": None
        #     }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "error": f"An unexpected error occurred: {str(e)}",
            "content": None
        }