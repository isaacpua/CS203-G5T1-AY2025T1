import os
import json
import asyncio
from typing import AsyncGenerator, Any, Dict, Optional

# Import client files
from src.graph import build_graph, AgentState  # Import from src/graph.py
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from langgraph.graph import StateGraph
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient


load_dotenv()

async def stream_graph_response(
    input_text: str, 
    graph: StateGraph, 
    config: dict
) -> AsyncGenerator[str, None]:
    """
    Simplified streaming function for client.
    """
    
    # This captures all messages currently in memory (the "old" ones)
    try:
        # get_state is synchronous and returns a StateSnapshot
        current_state = graph.get_state(config) 
        
        # The snapshot (current_state) contains the AgentState in its .values attribute
        if current_state and current_state.values and "messages" in current_state.values:
            old_message_ids = {m.id for m in current_state.values["messages"]}
        else:
            old_message_ids = set()

    except Exception as e:
        # This is EXPECTED on the very first run when no state exists
        print(f"[WARN] No prior state or error getting state: {e}")
        old_message_ids = set()
    
    # Create the input for the graph
    input_state = AgentState(messages=[HumanMessage(content=input_text)])
    
    async for message_chunk, metadata in graph.astream(
        input=input_state,
        stream_mode="messages",
        config=config
    ):
        node_name = metadata.get("langgraph_node", "")

        # Check if this message ID is from our "old" set
        is_old_memory = message_chunk.id in old_message_ids
        
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
        # Use the `is_old_memory` flag to change the printout ---
            if is_old_memory:
                # This is from the checkpoint
                yield f"[DEBUG-MEMORY] Replaying tool: {message_chunk.name}...\n"
                print(f"[DEBUG-MEMORY] Tool {message_chunk.name} replayed: {message_chunk.content[:100]}...")
            else:
                # This is a new tool call
                yield f"[DEBUG-NEW] Running tool: {message_chunk.name}...\n"
                print(f"[DEBUG-NEW] Tool {message_chunk.name} returned: {message_chunk.content[:200]}...")

async def main():
    """
    Main function to load tools and run the chat loop.
    """
    print("Starting MCP Client...")
    
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

    # Load Tools using MultiServerMCPClient
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

    # Build the Graph
    # We pass the loaded tools to our new, simple graph builder
    compiled_graph = build_graph(tools)
    print("Chatbot graph compiled successfully.")

    # Run Chat Loop
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