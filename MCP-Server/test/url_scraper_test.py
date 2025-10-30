import asyncio
import json
from fastmcp import Client

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/"

# A simple URL to test against
TEST_URL = "https://www.ft.com/content/59851cb3-c983-4d81-a1fc-a9c0189304cf"
# TEST_URL = "https://finance.yahoo.com/topic/tariffs/"
# USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
# USER_AGENT = generate_random_user_agent(device_type='windows')


async def main():
    """
    Connects to the URL scraper MCP server, lists its tools,
    and calls the 'scrape_single_url' tool.
    """
    print(f"--- Running URL Scraper Test Script ---")
    print(f"Attempting to connect to the server at: {MCP_SERVER_URL}")

    try:
        client = Client(MCP_SERVER_URL)

        async with client:
            print("✅ Successfully connected to the scraper server!")

            # 1. List available tools
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"🛠️  Available tools: {tool_names}")



            print(f"\n📞 Calling 'scrape_single_url' for URL: {TEST_URL}...")
            mcp_response = await client.call_tool("scrape_single_url", {"url": TEST_URL})
            response = json.loads(mcp_response.content[0].text)
            print("🎉 Success! Server responded:")
            print(response)
            md = response["markdown"]
            # print(md)
            with open("article.md", "w", encoding="utf-8") as file:
                print("Writing md to file...")
                file.write(md)



            # print(f"\n📞 Calling 'analyze_article' ...")
            # mcp_response = await client.call_tool("analyze_article", {"md": md})
            # response = json.loads(mcp_response.content[0].text)
            # print("🎉 Success! Server responded:")
            # md = response["markdown"]
            # print(md)
            # with open("analysis.md", "w", encoding="utf-8") as file:
            #     print("Writing md to file...")
            #     file.write(md)
            

    except Exception as e:
        print(f"\n❌ An error occurred. Is your FastAPI server running?")
        print(f"   Error details: {e}")
        print("\n   Troubleshooting:")
        print("   - Ensure your main server is running with 'fastapi run'.")
        print(f"   - Check that the server URL is correct: {MCP_SERVER_URL}")


if __name__ == "__main__":
    asyncio.run(main())
    print("\n--- Test complete ---")
