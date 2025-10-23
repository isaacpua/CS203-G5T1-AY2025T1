from fastmcp import FastMCP
from fastapi import Request
from fastapi.responses import JSONResponse

from url_scraper_tool import newsletter_scrape, single_URL_scrape

mcp = FastMCP(
    name="DexiaMCP",
    instructions="""
        This server provides tools.
    """,
)

# --- Healthcheck Route ---
@mcp.custom_route("/", methods=["GET"])
async def healthcheck(request: Request) -> JSONResponse:
    """
    Responds with a 200 OK status for health checks, required by Cloud Run.
    """
    return JSONResponse({"status": "ok"})



@mcp.tool
async def scrape_tariff_news_articles() -> dict:
    """
    The tool for scraping the Yahoo Finance website for tariff related 
    news articles

    Returns:
        Dict with the success state, and error message or response markdown text for
        the various news items and the respective links to those articles
    """
    return await newsletter_scrape()


@mcp.tool
async def scrape_single_article(url: str) -> dict:
    """
    The tool for scraping a single url (preferably yahoo sites :P)

    Args:
        url: A string of the url to scrape

    Returns:
        Dict with the success state, and error message or response markdown text for
        the scraped information
    
    """
    return await single_URL_scrape(url) 


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=4200,
        path="/mcp",
        log_level="debug",
    )
