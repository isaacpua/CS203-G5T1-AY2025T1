import os
import json
import logging
from fastapi import APIRouter
from fastmcp import Client
import pandas as pd
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO)
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/"
DB_CONFIG = {
    "DB_URL": os.getenv("DB_URL"),
    "DB_USERNAME": os.getenv("DB_USERNAME"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
}

router = APIRouter(prefix="/mcp/api/v1")
client = Client(MCP_SERVER_URL)


@router.get("/greet")
async def greet(name: str):
    try:
        async with client:
            logging.info(f"Calling greet tool on {MCP_SERVER_URL} ...")
            response = await client.call_tool("greet", {"name": name})
            logging.info(f"Successfully called greet tool!")

            if response and hasattr(response, "content") and hasattr(response.content[0], "text"):
                result = response.content[0].text
                return response
            else:
                raise Exception(
                    f"Tool executed, but returned an unexpected result: {result}")

    except Exception as e:
        logging.error(f"Error details: {e}")
        return {"error": e}


@router.get("/forecast")
async def get_forecast():
    try:
        connection_string = f"postgresql://{DB_CONFIG["DB_USERNAME"]}:{DB_CONFIG["DB_PASSWORD"]}@{DB_CONFIG["DB_URL"]}"
        db_engine = create_engine(connection_string)

        df = pd.read_sql("SELECT * FROM tariffs.tariff_forecasts", db_engine)

        return json.loads(df.to_json())

    except Exception as e:
        logging.error(f"Error details: {e}")
        return {"error": e}


@router.post("/forecast")
async def forecast_tariffs():
    try:
        async with client:
            logging.info(
                f"Calling forecast_tariffs tool on {MCP_SERVER_URL} ...")
            response = await client.call_tool("forecast_tariffs", {})
            logging.info(f"Successfully called forecast_tariffs tool!")

            if response and hasattr(response, "content") and hasattr(response.content[0], "text"):
                result = response.content[0].text
                return response
            else:
                raise Exception(
                    f"Tool executed, but returned an unexpected result: {result}")

    except Exception as e:
        logging.error(f"Error details: {e}")
        return {"error": e}
    

@router.get("/newsletter")
async def get_newsletter():
    try:
        async with client:
            logging.info(f"Calling newsletter tool on {MCP_SERVER_URL} ...")
            mcp_response = await client.call_tool("newsletter_scrape")
            logging.info(f"Successfully called newsletter tool!")

            response = json.loads(mcp_response.content[0].text)
            print(response)

            # with open("response.md", "w", encoding="utf-8") as file:
            #     print("Writing md to file...")
            #     file.write(response["markdown"])
            return response
        
    except Exception as e:
        logging.error(f"Error details: {e}")
        return {"error": e}
    


# !! INCOMPLETE !!
@router.get("/analyze")
async def analyze(url: str):
    try:
        async with client:
            logging.info(f"Calling scrape tool on {MCP_SERVER_URL} ...")
            mcp_response = await client.call_tool("scrape_single_url", {"url": url})
            logging.info(f"Successfully called scrape tool!")

            response = json.loads(mcp_response.content[0].text)
            print(response)

            # with open("response.md", "w", encoding="utf-8") as file:
            #     print("Writing md to file...")
            #     file.write(response["markdown"])
            return response
        
    except Exception as e:
        logging.error(f"Error details: {e}")
        return {"error": e}