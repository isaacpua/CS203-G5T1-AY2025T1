import asyncio
import json
import logging 
from fastmcp import Client

logging.basicConfig(level=logging.INFO)
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/"


async def main():
    logging.info(f"Attempting to connect to the server at: {MCP_SERVER_URL}")

    try:
        client = Client(MCP_SERVER_URL)

        async with client:
            logging.info("Successfully connected to the scraper server!")
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            logging.info(f"Available tools: {tool_names}")

            tool_name = "forecast_tariffs"
            tool_params = {}
            if tool_name in tool_names:
                logging.info(f"Calling the tool: {tool_name}")
                result = await client.call_tool(tool_name, tool_params)
                if result and hasattr(result[0], 'text'):
                    response_data = json.loads(result[0].text)
                    logging.info("Tool call was successful!")
                    if (not response_data["success"]):
                        raise Exception(response_data["message"])
                    logging.info(response_data)
                else:
                    logging.error(f"Tool executed, but returned an unexpected result: {result}")
            else:
                logging.error(
                    f"Error: Tool {tool_name} not found on {MCP_SERVER_URL}")

    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    asyncio.run(main())
