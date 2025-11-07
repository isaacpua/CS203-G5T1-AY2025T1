import os
import json
import logging
import httpx
from fastapi import APIRouter, HTTPException
from fastmcp import Client
import pandas as pd
from sqlalchemy import create_engine
import datetime

logging.basicConfig(level=logging.INFO)
BASE_URL = "http://127.0.0.1:8000"
MCP_SERVER_URL = f"{BASE_URL}/mcp/"
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
                return result
            else:
                raise Exception(
                    f"Tool executed, but returned an unexpected result: {response}")

    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=404, detail=str(e))


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
        async with client:
            try:
                with open("data/newsletter.json", "r", encoding="utf-8") as file:
                    print("Reading stored newsletter")
                    curr_newsletter_json = json.load(file)
                if datetime.datetime.strptime(curr_newsletter_json["date"], "%d/%m/%Y").date() == datetime.date.today():
                    print("Stored newsletter is updated! Returning that...")
                    response = {
                        "success": True,
                        "error": None,
                        "markdown": curr_newsletter_json["content"]
                    }
                    # print(response)
                    return response
                else:
                    print("Stored newsletter is old!")
            except(FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
                print("Failed to read stored newsletter or date")


            logging.info(f"Calling newsletter tool on {MCP_SERVER_URL} ...")
            mcp_response = await client.call_tool("newsletter_scrape")
            logging.info(f"Successfully called newsletter tool!")
            response = json.loads(mcp_response.content[0].text)
            # print(response)


            if not response["success"]:
                raise Exception(response["error"])


            print("Creating newsletter json...")
            new_newsletter_json = {
                "date": datetime.date.today().strftime("%d/%m/%Y"),
                "content": response["markdown"]
            }
            with open("data/newsletter.json", "w", encoding="utf-8") as file:
                print("Writing today's Newsletter to file...")
                json.dump(new_newsletter_json, file, indent = 4)


            return response
        
    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    


@router.get("/analyze")
async def analyze(url: str):
    try:
        async with client:
            logging.info(f"Calling scrape tool on {MCP_SERVER_URL} ...")
            mcp_response = await client.call_tool("scrape_single_url", {"url": url})
            logging.info(f"Successfully called scrape tool!")
            response = json.loads(mcp_response.content[0].text)
            print(response)

            if not response["success"]:
                raise Exception(response["error"])
            
            md = response["markdown"]

            logging.info(f"Calling analyze tool on {MCP_SERVER_URL} ...")
            mcp_response = await client.call_tool("analyze_article", {"md": md})
            response = json.loads(mcp_response.content[0].text)
            print(response)

            if not response["success"]:
                raise Exception(response["error"])
            
            return response
        
    except Exception as e:
        logging.error(f"Error details: {e}")
        raise HTTPException(status_code=404, detail=str(e))
