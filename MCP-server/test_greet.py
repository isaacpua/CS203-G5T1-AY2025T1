# test.py
import asyncio
from fastmcp import Client

# The full URL to the specific MCP server you want to test
# This is defined by how you mount it in your main.py
GREET_SERVER_URL = "http://127.0.0.1:8000/greet/mcp"

async def main():
    """
    Connects to the running MCP server, lists available tools,
    and calls the 'greet' tool.
    """
    print(f"Attempting to connect to the server at: {GREET_SERVER_URL}")

    try:
        # Create a client for the specific server endpoint
        client = Client(GREET_SERVER_URL)

        # The 'async with' block handles connecting and disconnecting
        async with client:
            print("✅ Successfully connected to the server!")

            # 1. List all available tools on this endpoint
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"🛠️  Available tools: {tool_names}")

            # 2. Call the 'greet' tool with a sample argument
            if "greet" in tool_names:
                print("\n📞 Calling the 'greet' tool with name='World'...")
                result = await client.call_tool("greet", {"name": "World"})

                # The result is a list of outputs; we'll take the first one
                if result and hasattr(result[0], 'text'):
                    print(f"🎉 Success! Server responded: '{result[0].text}'")
                else:
                    print(f"⚠️ Tool executed, but returned an unexpected result: {result}")
            else:
                print("❌ Error: 'greet' tool not found on this server endpoint.")

    except Exception as e:
        print(f"\n❌ An error occurred. Is your server running?")
        print(f"   Error details: {e}")

if __name__ == "__main__":
    # Ensure your FastAPI server is running before executing this script
    print("--- Running MCP Tool Test Script ---")
    asyncio.run(main())
    print("\n--- Test complete ---")