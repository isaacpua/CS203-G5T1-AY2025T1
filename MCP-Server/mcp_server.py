import asyncpg
import logging
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

db_pool = None

async def init_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            dsn=f'postgresql://{DB_CONFIG["DB_USERNAME"]}:{DB_CONFIG["DB_PASSWORD"]}@{DB_CONFIG["DB_URL"]}',
            min_size=1,
            max_size=10
        )

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


@mcp.tool(name="forecast_tariffs")
async def generate_tariff_forecasts() -> dict:
    if db_pool is None:
        await init_db_pool()

    async with db_pool.acquire() as conn:
        # Atomic check-and-set using UPDATE with WHERE condition
        result = await conn.execute(
            """
            UPDATE tariffs.forecast_lock 
            SET is_updating = TRUE, updated_at = NOW()
            WHERE id = 1 AND is_updating = FALSE
            """
        )
        logging.info(result)
        # If no rows updated, lock was already held
        if result == "UPDATE 0":
            return {
                "success": False,
                "error": "Forecast update already in progress. Please try again later."
            }

        try:
            response = await forecast_tariffs(DB_CONFIG)
            return response
        finally:
            # Always release the lock
            await conn.execute("UPDATE tariffs.forecast_lock SET is_updating = FALSE WHERE id = 1")


@mcp.custom_route("/forecast/status", methods=["GET"])
async def forecast_status(request: Request) -> JSONResponse:
    if db_pool is None:
        await init_db_pool()
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT is_updating FROM tariffs.forecast_lock WHERE id = 1"
        )
        return JSONResponse({"updating": row["is_updating"] if row else False})
