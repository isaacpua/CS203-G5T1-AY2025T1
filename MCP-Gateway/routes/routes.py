import os
import json
import logging
import httpx
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from fastmcp import Client
import pandas as pd
from sqlalchemy import create_engine, text
import datetime
import asyncio
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI
from pathlib import Path

logging.basicConfig(level=logging.INFO)
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
MCP_SERVER_URL = f"{BASE_URL}/mcp/"
DB_CONFIG = {
    "DB_URL": os.getenv("DB_URL"),
    "DB_USERNAME": os.getenv("DB_USERNAME"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
}

# --- FILE PATHS ---
DATA_DIR = Path("data")
# This is for the new mailing list
MAILING_LIST_PATH = DATA_DIR / "mailinglist.json"
# Ensure the data directory exists
DATA_DIR.mkdir(exist_ok=True)


router = APIRouter(prefix="/mcp/api/v1")
client = Client(MCP_SERVER_URL)


class NewsletterRequest(BaseModel):
    # The server will get the list from its file
    # recipients: List[str] = Field(..., description="A list of email addresses to send the newsletter to.")
    markdown_content: str = Field(
        ..., description="The full raw markdown content of the newsletter.")


async def _get_mailing_list() -> List[str]:
    """Reads the mailing list from data/mailinglist.json."""
    if not MAILING_LIST_PATH.exists():
        return []  # Return empty list if file doesn't exist
    try:
        with open(MAILING_LIST_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError):
        logging.warning("Could not read or parse data/mailinglist.json")
        return []


async def _save_mailing_list(recipients: List[str]) -> bool:
    """Saves the mailing list to data/mailinglist.json."""
    try:
        with open(MAILING_LIST_PATH, "w", encoding="utf-8") as file:
            json.dump(recipients, file, indent=4)
        return True
    except IOError as e:
        logging.error(f"Failed to write to data/mailinglist.json: {e}")
        return False


async def summarize_newsletter(content: str) -> str:
    """
    Uses OpenAI to summarize the newsletter markdown into a plain-text email body.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY is not set.")
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set.")

    try:
        # Run the blocking OpenAI call in a separate thread
        def blocking_openai_call():
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an assistant that summarizes daily newsletter markdown into a concise, plain-text email body for a mailing list. Since it is plain text, provide the urls if any after each point.Do not give me an email template, the start of email should be \"Dear Users\", and the end will be \"Best Regards, TARIFF\". Focus on the key news items. Do not use markdown in your output."},
                    {"role": "user", "content": f"Summarize this newsletter:\n\n{content}"}
                ]
            )
            return completion.choices[0].message.content

        summary = await asyncio.to_thread(blocking_openai_call)
        return summary
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to summarize content with OpenAI: {e}")


@router.get("/greet")
async def greet(name: str):
    try:
        async with client:
            logging.info(f"Calling greet tool on {MCP_SERVER_URL} ...")
            response = await client.call_tool("greet", {"name": name})
            logging.info(f"Successfully called greet tool!")

            if response and hasattr(response, "content") and hasattr(response.content[0], "text"):
                result = response.content[0].text
                return result
            else:
                raise Exception(
                    f"Tool executed, but returned an unexpected result: {response}")

    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health")
async def healthcheck():
    return JSONResponse({"status": "ok"})


@router.get("/forecast")
async def get_forecast():
    try:
        connection_string = f"postgresql://{DB_CONFIG["DB_USERNAME"]}:{DB_CONFIG["DB_PASSWORD"]}@{DB_CONFIG["DB_URL"]}"
        db_engine = create_engine(connection_string)

        df = pd.read_sql("SELECT * FROM tariffs.tariff_forecasts", db_engine)

        return json.loads(df.to_json())

    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/forecast")
async def forecast_tariffs():
    try:
        response = httpx.get(f"{BASE_URL}/forecast/status")
        if (json.loads(response.read())["updating"]):
            raise Exception("Forecast update already in progress. Please try again later.")

        async with client:
            logging.info(
                f"Calling forecast_tariffs tool on {MCP_SERVER_URL} ...")
            response = await client.call_tool("forecast_tariffs", {})
            logging.info(f"Successfully called forecast_tariffs tool!")

            if response and hasattr(response, "content") and hasattr(response.content[0], "text"):
                result = response.content[0].text
                return result
            else:
                raise Exception(
                    f"Tool executed, but returned an unexpected result: {response}")

    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/newsletter")
async def get_newsletter():
    try:
        connection_string = f"postgresql://{DB_CONFIG["DB_USERNAME"]}:{DB_CONFIG["DB_PASSWORD"]}@{DB_CONFIG["DB_URL"]}"
        db_engine = create_engine(connection_string)
        today = datetime.date.today()

        # Try to fetch today's newsletter from the database (cache hit)
        try:
            query = text("SELECT content FROM tariffs.tariff_newsletters WHERE date = :today")
            with db_engine.connect() as connection:
                result = connection.execute(query, {"today": today}).fetchone()

            if result:
                print("Found today's newsletter in DB! Returning that...")
                response = {
                    "success": True,
                    "error": None,
                    "markdown": result.content
                }
                return response
            else:
                print("Stored newsletter is old or not found in DB!")

        except Exception as e:
            # If DB read fails, log it and fall through to scraping
            print(f"Failed to read from DB: {e}. Fetching new content...")

        # scrape it
        async with client:
            logging.info(f"Calling newsletter tool on {MCP_SERVER_URL} ...")
            mcp_response = await client.call_tool("newsletter_scrape")
            logging.info(f"Successfully called newsletter tool!")
            response = json.loads(mcp_response.content[0].text)

            if not response["success"]:
                raise Exception(response["error"])

            # save the newly scraped content to the database
            print("Writing today's Newsletter to DB...")
            new_markdown = response["markdown"]

            # INSERT a new row or UPDATE the existing row for today
            insert_query = text("""
                INSERT INTO tariffs.tariff_newsletters (date, content)
                VALUES (:today, :content)
                ON CONFLICT (date)
                DO UPDATE SET content = EXCLUDED.content;
            """)

            # .begin() automatically commits on success or rolls back on error
            with db_engine.begin() as connection:
                connection.execute(insert_query, {"today": today, "content": new_markdown})

            print("Successfully wrote to DB.")

            # Return the freshly scraped response
            return response

    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/newsletter/mailinglist")
async def get_mailing_list():
    recipients = await _get_mailing_list()
    return {"recipients": recipients}


@router.post("/newsletter/mailinglist")
async def update_mailing_list(recipients: List[str] = Body(..., embed=True)):
    if await _save_mailing_list(recipients):
        return {"status": "success", "message": "Mailing list updated."}
    else:
        raise HTTPException(status_code=500, detail="Failed to save mailing list.")


@router.post("/newsletter/send")
async def send_newsletter(request: NewsletterRequest = Body(...)):
    """
    This endpoint orchestrates the newsletter sending process:
    1. Reads the mailing list from data/mailinglist.json.
    2. Summarizes the markdown content using OpenAI.
    3. Sends the summary to each recipient using the MCP-Server's email tool.
    """

    recipients = await _get_mailing_list()
    if not recipients:
        raise HTTPException(
            status_code=400, detail="No recipients in mailing list. Please add emails first.")

    if not request.markdown_content:
        raise HTTPException(
            status_code=400, detail="No markdown content provided.")

    # Step 1: Summarize the content
    logging.info("Summarizing newsletter content...")
    try:
        email_body = await summarize_newsletter(request.markdown_content)
        # Suggestion: Change "Weekly" to "Daily" if it's a daily newsletter
        subject = "Your Daily Tariff Newsletter Digest"
    except HTTPException as e:
        return e

    logging.info("Summary complete. Starting email dispatch...")

    # Step 2: Send emails concurrently
    tasks = []
    try:
        async with client:
            for email in recipients:
                tool_payload = {
                    "to_email": email,
                    "subject": subject,
                    "body": email_body
                }
                tasks.append(client.call_tool("send_email", tool_payload))

            mcp_results = await asyncio.gather(*tasks, return_exceptions=True)

    except Exception as e:
        logging.error(f"Error connecting to MCP server: {e}")
        raise HTTPException(
            status_code=503, detail=f"Failed to connect to MCP-Server: {e}")

    logging.info("Email dispatch complete. Compiling results...")

    # Step 3: Report results
    dispatch_results = []
    success_count = 0

    for email, result in zip(recipients, mcp_results):
        if isinstance(result, Exception):
            dispatch_results.append({
                "email": email,
                "status": "error",
                "detail": f"Task failed: {result}"
            })
        else:
            try:
                tool_output = json.loads(result.content[0].text)

                if tool_output.get("status") == "success":
                    success_count += 1
                    dispatch_results.append({
                        "email": email,
                        "status": "success",
                        "message_id": tool_output.get("message_id")
                    })
                else:
                    dispatch_results.append({
                        "email": email,
                        "status": "error",
                        "detail": tool_output.get("detail", "Unknown error from email tool")
                    })
            except Exception as e:
                dispatch_results.append({
                    "email": email,
                    "status": "error",
                    "detail": f"Failed to parse tool response: {e}"
                })

    failed_count = len(recipients) - success_count

    return {
        "status": "complete",
        "total_sent": success_count,
        "total_failed": failed_count,
        "dispatch_results": dispatch_results
    }


@router.post("/analyze")
async def analyze(data: dict):
    try:
        async with client:
            url = data["url"]
            text = data["text"]
            md = ""
            if url:
                logging.info(f"Calling scrape tool on {MCP_SERVER_URL} ...")
                mcp_response = await client.call_tool("scrape_single_url", {"url": url})
                logging.info(f"Successfully called scrape tool!")
                response = json.loads(mcp_response.content[0].text)
                print(response)

                if not response["success"]:
                    raise Exception(response["error"])
                md = response["markdown"]

            if text:
                md = md + "\n" + text
            # print(md)

            logging.info(f"Calling analyze tool on {MCP_SERVER_URL} ...")
            mcp_response = await client.call_tool("analyze_article", {"input": md})
            response = json.loads(mcp_response.content[0].text)
            print(response)

            if not response["success"]:
                raise Exception(response["error"])

            return response

    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
