import asyncio
import re
from typing import Callable
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.cache_context import CacheMode
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential
import tempfile
import shutil

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"


async def _scrape_url_internal(
    url: str,
    md_generator: DefaultMarkdownGenerator,
    markdown_property: str,
    post_process_func: Callable[[str], str] | None = None
) -> dict:
    """
    Internal helper function to handle the core scraping logic.
    """
    
    response = {
        "success": None,
        "error": None,
        "markdown": None
    }

    temp_dir = None
    
    try:
        temp_dir = tempfile.mkdtemp()
        print(f"Creating new WebKit profile in: {temp_dir}")

        # 1. Create a new BrowserConfig for this specific request
        browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            verbose=True,
            user_agent=USER_AGENT,
            text_mode=True,
            user_data_dir=temp_dir
        )

        # 2. Create Crawler config
        crawler_run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            markdown_generator=md_generator,
            stream=False
        )

        # 3. Create the undetected adapter
        undetected_adapter = UndetectedAdapter()

        # 4. Create the crawler strategy
        crawler_strategy = AsyncPlaywrightCrawlerStrategy(
            browser_config=browser_config,
            browser_adapter=undetected_adapter
        )

        # start crawlin
        async with AsyncWebCrawler(crawler_strategy=crawler_strategy, config=browser_config) as crawler:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                reraise=True
            ):
                with attempt:
                    print(f"Attempting crawl on: {url} (Profile: {temp_dir})")
                    results_list = await crawler.arun(url=url, config=crawler_run_config)
                    result = results_list[0]

            if not result.success:  # failed crawl
                print(f"Crawl failed: {result.error_message}")
                print(f"Status code: {result.status_code}")
                raise Exception(f"{result.error_message}")

            # successful crawl
            print("Crawl success!")
            
            # Dynamically get 'raw_markdown' or 'fit_markdown'
            markdown = getattr(result.markdown, markdown_property)

            # Apply post-processing if a function was provided
            if post_process_func:
                markdown = post_process_func(markdown)

            response["success"] = True
            response["markdown"] = markdown

        # return response
        return response

    except Exception as e:
        print(e)
        response["success"] = False
        response["error"] = e
        return response
    
    finally:
        if temp_dir:
            try:
                print(f"Cleaning up profile: {temp_dir}")
                await asyncio.to_thread(shutil.rmtree, temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Warning: Failed to clean up temp dir {temp_dir}: {e}")


async def newsletter_scrape() -> dict:
    """
    The tool for scraping the Yahoo Finance website for tariff related 
    news articles
    """
    
    url = "https://finance.yahoo.com/topic/tariffs/"

    # 1. Define the specific MD Generator
    md_generator = DefaultMarkdownGenerator(
        content_source="cleaned_html",
        options={"ignore_links": False}
    )

    # 2. Define the specific post-processing
    def post_process(md: str) -> str:
        # Added a check to prevent index error if split fails
        parts = re.split("## Tariffs", md, 1)
        md = parts[1] if len(parts) > 1 else md
        
        parts = re.split(r"\[\s*\]\(https://finance\.yahoo\.com/\)", md, 1)
        md = parts[0] if len(parts) > 0 else md
        return md

    # 3. Call the helper
    return await _scrape_url_internal(
        url=url,
        md_generator=md_generator,
        markdown_property="raw_markdown",
        post_process_func=post_process
    )


async def single_URL_scrape(url: str) -> dict:
    """
    The tool for scraping a single url (preferably yahoo sites :P)
    """

    # 1. Define the specific MD Generator
    prune_filter = PruningContentFilter(
        threshold=0.5,
        threshold_type="dynamic",
        min_word_threshold=2
    )
    md_generator = DefaultMarkdownGenerator(
        content_source="cleaned_html",
        content_filter=prune_filter,
        options={"ignore_links": False}
    )

    # 2. Call the helper (no post-processing needed)
    return await _scrape_url_internal(
        url=url,
        md_generator=md_generator,
        markdown_property="fit_markdown"
    )
