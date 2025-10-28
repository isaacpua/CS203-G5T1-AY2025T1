import os
from fastmcp import FastMCP
from fastapi import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from tools import newsletter_scrape, single_URL_scrape, forecast_tariffs

load_dotenv()
DB_CONFIG = {
    "DB_URL": os.getenv("DB_URL"),
    "DB_USERNAME": os.getenv("DB_USERNAME"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
}

mcp = FastMCP(
    name="DexiaMCP",
    instructions="""
        This server provides tools.
    """,
    stateless_http=True
)


@mcp.custom_route("/", methods=["GET"])
async def healthcheck(request: Request) -> JSONResponse:
    """
    Responds with a 200 OK status for health checks, required by Cloud Run.
    """
    return JSONResponse({"status": "ok"})


@mcp.tool(name="greet")
async def greet(name: str):
    return f"Greetings {name}!"


@mcp.tool(name="newsletter_scrape")
async def scrape_tariff_news_articles() -> dict:
    """
    The tool for scraping the Yahoo Finance website for tariff related 
    news articles

    Returns:
        Dict with the success state, and error message or response markdown text for
        the various news items and the respective links to those articles
    """
    return await newsletter_scrape()


@mcp.tool(name="scrape_single_url")
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
