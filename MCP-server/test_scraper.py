# test_scraper.py
import asyncio
import json
from fastmcp import Client

# The URL for the scraper server is defined in your main.py and url_scraper/server.py
# main.py mounts it at /scraper
# server.py serves the MCP tools under the /scraper/ path
SCRAPER_SERVER_URL = "http://127.0.0.1:8000/scraper/mcp"

# A simple URL to test against
TEST_URL = "http://example.com"

async def main():
    """
    Connects to the URL scraper MCP server, lists its tools,
    and calls the 'detect_paywall' tool.
    """
    print(f"--- Running URL Scraper Test Script ---")
    print(f"Attempting to connect to the server at: {SCRAPER_SERVER_URL}")

    try:
        client = Client(SCRAPER_SERVER_URL)

        async with client:
            print("✅ Successfully connected to the scraper server!")

            # 1. List available tools
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"🛠️  Available tools: {tool_names}")

            # 2. Call the 'detect_paywall' tool
            if "detect_paywall" in tool_names:
                print(f"\n📞 Calling 'detect_paywall' for URL: {TEST_URL}...")
                result = await client.call_tool("detect_paywall", {"url": TEST_URL})

                if result and hasattr(result[0], 'text'):
                    # The tool returns a JSON string, so we parse it for readability
                    response_data = json.loads(result[0].text)
                    print("🎉 Success! Server responded:")
                    # Pretty print the JSON response
                    print(json.dumps(response_data, indent=2))
                else:
                    print(f"⚠️ Tool executed, but returned an unexpected result: {result}")
            else:
                print("❌ Error: 'detect_paywall' tool not found on this server endpoint.")

    except Exception as e:
        print(f"\n❌ An error occurred. Is your FastAPI server running?")
        print(f"   Error details: {e}")
        print("\n   Troubleshooting:")
        print("   - Ensure your main server is running with 'fastapi run'.")
        print(f"   - Check that the server URL is correct: {SCRAPER_SERVER_URL}")


if __name__ == "__main__":
    asyncio.run(main())
    print("\n--- Test complete ---")