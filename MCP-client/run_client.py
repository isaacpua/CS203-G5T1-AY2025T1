import os
import json
import asyncio
from typing import AsyncGenerator, Any, Dict, Optional

# --- 1. Import from your *other* client files ---
from src.graph import build_graph, AgentState  # Import from src/graph.py
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from langgraph.graph import StateGraph
from dotenv import load_dotenv

# --- 2. This is the working import from your OLD client.py ---
# This is the key to fixing the problem.
from langchain_mcp_adapters.client import MultiServerMCPClient


load_dotenv()

async def stream_graph_response(
    input_text: str, 
    graph: StateGraph, 
    config: dict
) -> AsyncGenerator[str, None]:
    """
    Simplified streaming function based on your old client.py.
    All paywall and complex scraping logic has been removed.
    """
    
    # Create the input for the graph
    input_state = AgentState(messages=[HumanMessage(content=input_text)])
    
    async for message_chunk, metadata in graph.astream(
        input=input_state,
        stream_mode="messages",
        config=config
    ):
        node_name = metadata.get("langgraph_node", "")
        
        # Check for AIMessageChunk (the LLM's response)
        if isinstance(message_chunk, AIMessageChunk):
            if message_chunk.response_metadata:
                # Check if it's about to call a tool
                if message_chunk.response_metadata.get("finish_reason") == "tool_calls":
                    yield "\n\n"  # Add a newline for readability
                    continue

            # Yield the actual text content from the LLM
            if message_chunk.content and message_chunk.content.strip():
                yield message_chunk.content

        # Check for ToolMessage (the result from a tool)
        elif isinstance(message_chunk, ToolMessage):
            # Optionally, you can yield a summary of the tool result.
            # For now, we'll just print it server-side and let the
            # agent summarize it in the next loop.
            print(f"Tool {message_chunk.name} returned: {message_chunk.content[:200]}...")
            yield f"Running tool: {message_chunk.name}..."

        # You can add more handling here if needed

async def main():
    """
    Main function to load tools and run the chat loop.
    """
    print("Starting MCP Client...")
    
    # --- 3. Load MCP Config ---
    # This loads the tool configuration from your mcp_config.json
    try:
        with open("src/mcp_config.json", "r") as f:
            mcp_config = json.load(f)
        print("Loaded MCP server configuration from src/mcp_config.json")
    except FileNotFoundError:
        print("ERROR: src/mcp_config.json not found.")
        print("Please ensure the mcp_config.json file exists in the 'src' folder.")
        return
    except json.JSONDecodeError:
        print("ERROR: Could not parse src/mcp_config.json. Is it valid JSON?")
        return

    # --- 4. Load Tools using MultiServerMCPClient ---
    # This uses the method from your working, old client.
    print("Connecting to MCP servers and fetching tools...")
    try:
        client = MultiServerMCPClient(mcp_config["mcpServers"])
        tools = await client.get_tools()
        print(f"Successfully loaded {len(tools)} tools:")
        for tool in tools:
            print(f"- {tool.name}")
    except Exception as e:
        print(f"FATAL: Could not load tools via MultiServerMCPClient: {e}")
        return

    # --- 5. Build the Graph ---
    # We pass the loaded tools to our new, simple graph builder
    compiled_graph = build_graph(tools)
    print("Chatbot graph compiled successfully.")

    # --- 6. Run Chat Loop ---
    config = {"configurable": {"thread_id": "main_thread"}}
    print("\n--- Jarvis is online. (Type 'exit' to quit) ---")
    
    while True:
        try:
            user_input = await asyncio.to_thread(input, "You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Jarvis: Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("Jarvis: ...")
            full_response = ""
            async for chunk in stream_graph_response(user_input, compiled_graph, config):
                if chunk.strip():
                    full_response += chunk
                    print(chunk, end="", flush=True) # Print chunk without newline
            
            # Add a final newline after the response is complete
            if full_response:
                print("\n") 

        except KeyboardInterrupt:
            print("\nJarvis: Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())