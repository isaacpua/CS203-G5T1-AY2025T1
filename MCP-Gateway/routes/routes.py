import os,json
import logging
import httpx
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from fastmcp import Client
import pandas as pd
from sqlalchemy import create_engine, Column, String, Integer, Float, Date, Text, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase # Added ORM imports
from load_data import main as data
import datetime
import asyncio
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any # Added Optional, Dict, Any
from openai import OpenAI
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
MCP_SERVER_URL = f"{BASE_URL}/mcp/"
DB_CONFIG = {
    "DB_URL": os.getenv("DB_URL"),
    "DB_USERNAME": os.getenv("DB_USERNAME"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
}

DATA_DIR = Path("data")
# This is for the new mailing list
MAILING_LIST_PATH = DATA_DIR / "mailinglist.json"
# Ensure the data directory exists
DATA_DIR.mkdir(exist_ok=True)

try:
    if not DB_CONFIG["DB_URL"] or not DB_CONFIG["DB_USERNAME"] or not DB_CONFIG["DB_PASSWORD"]:
        raise ValueError("DB_URL, DB_USER, or DB_PASSWORD is not set in .env")
    
    db_url_cleaned = DB_CONFIG["DB_URL"]
    if db_url_cleaned.startswith("jdbc:postgresql://"):
        db_url_cleaned = db_url_cleaned.replace("jdbc:postgresql://", "")
        
    connection_string = f"postgresql://{DB_CONFIG['DB_USERNAME']}:{DB_CONFIG['DB_PASSWORD']}@{db_url_cleaned}"
    
    sqlalchemy_engine = create_engine(connection_string, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlalchemy_engine)
    logger.info("MCP-Gateway: SQLAlchemy engine and SessionLocal created.")
except Exception as e:
    logger.error(f"MCP-Gateway: Failed to create SQLAlchemy engine: {e}")
    sqlalchemy_engine = None
    SessionLocal = None


router = APIRouter(prefix="/mcp/api/v1")
client = Client(MCP_SERVER_URL)


class NewsletterRequest(BaseModel):
    # The server will get the list from its file
    # recipients: List[str] = Field(..., description="A list of email addresses to send the newsletter to.")
    markdown_content: str = Field(
        ..., description="The full raw markdown content of the newsletter.")


class Base(DeclarativeBase):
    pass

class TariffMaster(Base):
    """
    SQLAlchemy ORM Model for the 'tariff_master' table in the 'tariffs' schema.
    This version matches the screenshot from image_b4387f.png
    """
    __tablename__ = 'tariff_master'
    __table_args__ = {'schema': 'tariffs'}

    tariffid = Column(String, primary_key=True)
    descriptionwcountry = Column(String)
    reportercountry = Column(Integer)
    partnercountry = Column(Integer)
    year = Column(Integer)
    advalorem = Column(Float)
    specificperunit = Column(Float)
    category = Column(String)
    unitname = Column(String)
    effectivedate = Column(Date)
    expirydate = Column(Date) # This column is in the screenshot
    datasource = Column(Text) # This column is in the screenshot

    def to_dict(self) -> Dict[str, Any]:
        """Converts the ORM object to a JSON-serializable dictionary."""
        return {
            "tariffid": self.tariffid,
            "descriptionwcountry": self.descriptionwcountry,
            "reportercountry": self.reportercountry,
            "partnercountry": self.partnercountry,
            "year": self.year,
            "advalorem": self.advalorem,
            "specificperunit": self.specificperunit,
            "category": self.category,
            "unitname": self.unitname,
            "effectivedate": self.effectivedate.strftime('%Y-%m-%d') if self.effectivedate else None,
            "expirydate": self.expirydate.strftime('%Y-%m-%d') if self.expirydate else None,
            "datasource": self.datasource
        }


def get_historical_data(
    db_session: Session,
    full_tariff_id_prefix: Optional[str] = None,
    hts6: Optional[str] = None,
    reporter_id: Optional[int] = None,
    partner_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetches historical tariff data from the database using an ORM session.
    """
    query = db_session.query(TariffMaster)
    
    if full_tariff_id_prefix:
        # --- Mode 1: Search by Full Tariff ID Prefix (e.g., '170211USAU') ---
        logger.info(f"Querying by full_tariff_id_prefix: {full_tariff_id_prefix}")
        query = query.filter(TariffMaster.tariffid.like(f"{full_tariff_id_prefix}%"))
        
    elif hts6 and reporter_id is not None and partner_id is not None:
        # --- Mode 2: Search by Parameters (using INT IDs and hts6 prefix) ---
        logger.info(f"Querying by params: hts6 prefix={hts6}, reporter_id={reporter_id}, partner_id={partner_id}")
        query = query.filter(
            TariffMaster.tariffid.like(f"{hts6}%"), # Match prefix of tariffid
            TariffMaster.reportercountry == reporter_id,  # Match integer ID
            TariffMaster.partnercountry == partner_id   # Match integer ID
        )
    
    else:
        # No valid search parameters provided
        logger.warning("No valid search parameters provided for historical data.")
        return []

    # Add ordering and a safety limit
    query = query.order_by(TariffMaster.year.asc(), TariffMaster.effectivedate.asc()).limit(1000)

    try:
        # Execute the query
        results = query.all()
        
        # Convert results to list of dictionaries
        data_points = [row.to_dict() for row in results]
        
        logger.info(f"Found {len(data_points)} data points.")
        return data_points

    except Exception as e:
        logger.error(f"Error executing historical tariff query: {e}")
        # Re-raise the exception so the endpoint can return a 500
        raise
# --- END NEW DATA ACCESS FUNCTION ---


async def _get_mailing_list() -> List[str]:
    """Reads the mailing list from data/mailinglist.json."""
    if not MAILING_LIST_PATH.exists():
        return []
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
        raise HTTPException(status_code=444, detail=str(e)) # Changed status to avoid clash with 404


@router.get("/health")
async def healthcheck():
    return JSONResponse({"status": "ok"})


@router.get("/forecast")
async def get_forecast():
    try:
        # --- MODIFIED: Use global engine ---
        if sqlalchemy_engine is None:
            raise HTTPException(status_code=503, detail="Database connection not initialized.")
            
        with sqlalchemy_engine.connect() as db_engine:
            df = pd.read_sql("SELECT * FROM tariffs.tariff_forecasts", db_engine)
        # --- END MODIFICATION ---

        return json.loads(df.to_json())

    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=444, detail=str(e)) # Changed status to avoid clash with 404


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
        raise HTTPException(status_code=444, detail=str(e)) # Changed status to avoid clash with 404


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

@router.get("/historical")
async def get_historical_data_endpoint(
    full_tariff_id_prefix: Optional[str] = None,
    hts6: Optional[str] = None,
    reporter_id: Optional[int] = None,
    partner_id: Optional[int] = None
):
    """
    Endpoint to get historical tariff data.
    
    Supports two search modes:
    1. ?full_tariff_id_prefix=170211USAU
    2. ?hts6=170211&reporter_id=188&partner_id=10
    """
    if SessionLocal is None:
        raise HTTPException(
            status_code=503, 
            detail="Database connection is not configured. Check server logs."
        )

    # Basic parameter validation
    is_mode_a = bool(full_tariff_id_prefix)
    is_mode_b = bool(hts6 and reporter_id is not None and partner_id is not None)

    if not is_mode_a and not is_mode_b:
        raise HTTPException(
            status_code=400, 
            detail="Invalid parameters. Provide either 'full_tariff_id_prefix' OR all of 'hts6', 'reporter_id', and 'partner_id'."
        )
    
    if is_mode_a and is_mode_b:
        raise HTTPException(
            status_code=400, 
            detail="Invalid parameters. Provide EITHER 'full_tariff_id_prefix' OR the other parameters, not both."
        )

    db_session: Session = SessionLocal()
    try:
        # Run the synchronous SQLAlchemy query in a separate thread
        data_points = await asyncio.to_thread(
            get_historical_data,
            db_session,
            full_tariff_id_prefix=full_tariff_id_prefix,
            hts6=hts6,
            reporter_id=reporter_id,
            partner_id=partner_id
        )
        
        return JSONResponse(content=data_points)

    except Exception as e:
        logger.error(f"Error in /historical endpoint: {e}")
        db_session.rollback() # Rollback on error
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")
    finally:
        db_session.close() # Always close the session

@router.post("/data/live")
async def load_live_data():
    try:
        logging.info("Starting data load")
        data.load_usitc_data()
        return {"message": "Load completed"}
    except Exception as e:
        logging.error(f"Error loading live data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

