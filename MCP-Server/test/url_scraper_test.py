import asyncio
import json
from fastmcp import Client

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp/"

# A simple URL to test against
TEST_URL = "https://www.bloomberg.com/news/features/2025-10-17/robinhood-s-next-bet-gen-z-401-k-s-and-trump?utm_campaign=bw&utm_medium=distro&utm_source=yahooUS"
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

            # 2. Call the 'scrape_single_url' tool
            tool_name = "scrape_single_url"
            tool_params = {
                "url": TEST_URL,
                #  "user_agent": USER_AGENT
            }
            if tool_name in tool_names:
                print(
                    f"\n📞 Calling 'scrape_single_url' for URL: {TEST_URL}...")
                # print(f"User Agent: {USER_AGENT}")
                result = await client.call_tool(tool_name, tool_params)

                if result and hasattr(result[0], 'text'):
                    # The tool returns a JSON string, so we parse it for readability
                    response_data = json.loads(result[0].text)
                    print("🎉 Success! Server responded:")
                    # print(f"URL: {response_data['url']}")
                    # print(response_data.keys())

                    # As of writing, the only available keys are ['success', 'error', 'markdown']

                    # Pretty print the JSON response
                    # print(json.dumps(response_data, indent=2))
                    # with open("raw.html", "w", encoding="utf-8") as file:
                    #     print("Writing raw html to file...")
                    #     file.write(response_data["raw_html"])
                    # with open("clean.html", "w", encoding="utf-8") as file:
                    #     print("Writing clean html to file...")
                    #     file.write(response_data["cleaned_html"])
                    # with open("fit.html", "w", encoding="utf-8") as file:
                    #     print("Writing fit html to file...")
                    #     file.write(response_data["fit_html"])
                    # with open("raw.md", "w", encoding="utf-8") as file:
                    #     print("Writing raw md to file...")
                    #     file.write(response_data["raw_markdown"])
                    # with open("fit.md", "w", encoding="utf-8") as file:
                    #     print("Writing fit md to file...")
                    #     file.write(response_data["fit_markdown"])
                    # with open("gud.md", "w", encoding="utf-8") as file:
                    #     print("Writing gud md to file...")
                    #     file.write(response_data["good_markdown"])
                    # with open("llm_output.txt", "w", encoding="utf-8") as file:
                    #     print("Writing llm output to file...")
                    #     file.write(response_data["llm_output"])
                    with open("response.json", "w", encoding="utf-8") as file:
                        print("Writing response to file...")
                        json.dump(response_data, file,
                                  ensure_ascii=False, indent=2)
                else:
                    print(
                        f"⚠️ Tool executed, but returned an unexpected result: {result}")
            else:
                print(
                    "❌ Error: 'scrape_single_url' tool not found on this server endpoint.")

    except Exception as e:
        print(f"\n❌ An error occurred. Is your FastAPI server running?")
        print(f"   Error details: {e}")
        print("\n   Troubleshooting:")
        print("   - Ensure your main server is running with 'fastapi run'.")
        print(f"   - Check that the server URL is correct: {MCP_SERVER_URL}")


if __name__ == "__main__":
    asyncio.run(main())
    print("\n--- Test complete ---")
