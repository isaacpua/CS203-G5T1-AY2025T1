import logging
from fastapi import APIRouter
from fastmcp import Client

logging.basicConfig(level=logging.INFO)
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/"

router = APIRouter(prefix="/mcp/api/v1")
client = Client(MCP_SERVER_URL)

@router.get("/greet")
async def greet(name:str):
    try:
        async with client:
            logging.info(f"Calling greet tool on {MCP_SERVER_URL} ...")
            response = await client.call_tool("greet", {"name": name})
            logging.info(f"Successfully called greet tool!")
            
            if response and hasattr(response, "content") and hasattr(response.content[0], "text"):
                result = response.content[0].text
                return response
            else:
                raise Exception(f"Tool executed, but returned an unexpected result: {result}")

    except Exception as e:
        logging.error(f"Error details: {e}")
        return {"error": e}
    