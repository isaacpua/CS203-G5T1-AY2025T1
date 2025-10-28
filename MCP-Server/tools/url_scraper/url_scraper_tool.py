import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, UndetectedAdapter, LLMConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.cache_context import CacheMode
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"


# Configure browser
browser_config = BrowserConfig(
    headless=True,
    browser_type="chromium",
    verbose=True,
    user_agent=USER_AGENT,
    text_mode=True
)


# Create the undetected adapter
undetected_adapter = UndetectedAdapter()


# Create the crawler strategy with undetected adapter
crawler_strategy = AsyncPlaywrightCrawlerStrategy(
    browser_config=browser_config,
    browser_adapter=undetected_adapter
)


response = {
    "success": None,
    "error": None,
    "markdown": None
}


async def newsletter_scrape() -> dict:
    """
    The tool for scraping the Yahoo Finance website for tariff related 
    news articles

    Returns:
        Dict with the success state, and error message or response markdown text for
        the various news items and the respective links to those articles
    """

    url = "https://finance.yahoo.com/topic/tariffs/"

    try:
        # Create MD Generator
        md_generator = DefaultMarkdownGenerator(
            content_source="cleaned_html",
            options={"ignore_links": False}
        )

        # Crawler config
        crawler_run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            # simulate_user =  True,
            markdown_generator=md_generator,
            stream=False
        )

        # start crawlin
        async with AsyncWebCrawler(crawler_strategy=crawler_strategy, config=browser_config) as crawler:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                reraise=True
            ):
                with attempt:
                    print("Attempting crawl!")
                    results_list = await crawler.arun(url=url, config=crawler_run_config)
                    result = results_list[0]


            if not result.success:  # failed crawl
                print(f"Crawl failed: {result.error_message}")
                print(f"Status code: {result.status_code}")
                raise Exception(f"{result.error_message}")

            # successful crawl
            markdown = result.markdown.raw_markdown
            markdown = re.split("## Tariffs", markdown)[1]
            markdown = re.split(
                r"\[\s*\]\(https://finance\.yahoo\.com/\)", markdown)[0]

            response["success"] = True
            response["markdown"] = markdown

        # return response
        return response

    except Exception as e:
        print(e)
        response["success"] = False
        response["error"] = e
        return response


async def single_URL_scrape(url: str) -> dict:
    """
    The tool for scraping a single url (preferably yahoo sites :P)

    Args:
        url: A string of the url to scrape

    Returns:
        Dict with the success state, and error message or response markdown text for
        the scraped information

    """

    try:
        # Create MD Generator
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

        # Crawler config
        crawler_run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            verbose=True,
            # simulate_user =  True,
            markdown_generator=md_generator,
            stream=False
        )

        # start crawlin
        async with AsyncWebCrawler(crawler_strategy=crawler_strategy, config=browser_config) as crawler:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                reraise=True
            ):
                with attempt:
                    print("Attempting crawl!")
                    results_list = await crawler.arun(url=url, config=crawler_run_config)
                    result = results_list[0]

                    
            if not result.success:  # failed crawl
                print(f"Crawl failed: {result.error_message}")
                print(f"Status code: {result.status_code}")
                raise Exception(f"{result.error_message}")

            # successful crawl
            markdown = result.markdown.fit_markdown

            response["success"] = True
            response["markdown"] = markdown

        # return response
        return response

    except Exception as e:
        print(e)
        response["success"] = False
        response["error"] = e
        return response
