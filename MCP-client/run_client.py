import os
import json
import asyncio
import uvicorn
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import AsyncGenerator, Any, Dict, Optional

# Import client files
from src.graph import build_graph, AgentState  # Import from src/graph.py
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from langgraph.graph import StateGraph
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# --- Globals to hold the compiled graph and client ---
compiled_graph = None
client = None

# -----------------------------------------------------------------
# 1. MODIFIED STREAMING LOGIC
# This function now yields a tuple: (event_type, content)
# "ai" -> for frontend, "debug" -> for terminal
# -----------------------------------------------------------------
async def _stream_graph_logic(
    input_text: str, 
    graph: StateGraph, 
    config: dict
) -> AsyncGenerator[tuple[str, str], None]:
    """
    Internal streaming logic that yields structured events.
    """
    
    try:
        current_state = graph.get_state(config) 
        if current_state and current_state.values and "messages" in current_state.values:
            old_message_ids = {m.id for m in current_state.values["messages"]}
        else:
            old_message_ids = set()
    except Exception as e:
        print(f"[WARN] No prior state or error getting state: {e}")
        old_message_ids = set()
    
    input_state = AgentState(messages=[HumanMessage(content=input_text)])
    
    async for message_chunk, metadata in graph.astream(
        input=input_state,
        stream_mode="messages",
        config=config
    ):
        # Check for AIMessageChunk (the LLM's response)
        if isinstance(message_chunk, AIMessageChunk):
            if message_chunk.response_metadata:
                if message_chunk.response_metadata.get("finish_reason") == "tool_calls":
                    continue  # Skip the tool call marker

            if message_chunk.content and message_chunk.content.strip():
                # Yield an "ai" event for the frontend
                yield ("ai", message_chunk.content)

        # Check for ToolMessage (the result from a tool)
        elif isinstance(message_chunk, ToolMessage):
            is_old_memory = message_chunk.id in old_message_ids
            if is_old_memory:
                debug_msg = f"[DEBUG-MEMORY] Replaying tool: {message_chunk.name}...\n"
                print(f"[DEBUG-MEMORY] Tool {message_chunk.name} replayed: {message_chunk.content[:100]}...")
            else:
                debug_msg = f"[DEBUG-NEW] Running tool: {message_chunk.name}...\n"
                print(f"[DEBUG-NEW] Tool {message_chunk.name} returned: {message_chunk.content[:200]}...")
            
            # Yield a "debug" event for the terminal
            yield ("debug", debug_msg)

# -----------------------------------------------------------------
# 2. SERVER SETUP
# We create a FastAPI app and a Socket.IO server
# -----------------------------------------------------------------

# Allow all origins for simplicity. For production, restrict this
# to your frontend's URL (e.g., "http://localhost:5173")
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Standard FastAPI app
app = FastAPI()

# Wrap the FastAPI app with the Socket.IO server
sio_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)

# Add CORS middleware to the FastAPI app itself
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------
# 3. STARTUP LOGIC
# This replaces the old `main` function.
# It loads tools and builds the graph when the server starts.
# -----------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    Main function to load tools and build the graph.
    """
    global compiled_graph, client
    print("Starting MCP Client Server...")
    
    try:
        with open("src/mcp_config.json", "r") as f:
            mcp_config = json.load(f)
        print("Loaded MCP server configuration from src/mcp_config.json")
    except FileNotFoundError:
        print("ERROR: src/mcp_config.json not found.")
        return
    except json.JSONDecodeError:
        print("ERROR: Could not parse src/mcp_config.json.")
        return

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

    compiled_graph = build_graph(tools)
    print("Chatbot graph compiled successfully.")
    print("\n--- Jarvis is online. Waiting for frontend connection... ---")

# -----------------------------------------------------------------
# 4. SOCKET.IO EVENT HANDLERS
# These replace the old `while True:` terminal loop
# -----------------------------------------------------------------

@sio.event
async def connect(sid, environ):
    print(f"[Socket.IO] Frontend connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"[Socket.IO] Frontend disconnected: {sid}")

@sio.event
async def chat_message(sid, data):
    """
    Handles incoming chat messages from the frontend.
    """
    if not compiled_graph:
        await sio.emit('ai_response', {'chunk': 'Error: Graph not initialized.'}, to=sid)
        return

    user_input = data.get("message")
    # Use the session ID (sid) as a default thread_ID to maintain memory
    thread_id = data.get("thread_id", sid) 
    
    if not user_input:
        return

    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"\n[Request from {sid}] User: {user_input}")
    print("Jarvis: ...")

    try:
        # Loop over the generator and route events
        async for event_type, content in _stream_graph_logic(user_input, compiled_graph, config):
            
            if event_type == "ai":
                # Send AI responses to the frontend
                await sio.emit('ai_response', {'chunk': content}, to=sid)
            
            elif event_type == "debug":
                # Print debug messages to the terminal (as requested)
                print(content.strip())
        
        # Signal the end of the stream to the frontend
        await sio.emit('ai_response_end', to=sid)
        print("[Jarvis] Response stream complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
        await sio.emit('ai_response', {'chunk': f'An error occurred: {e}'}, to=sid)
        await sio.emit('ai_response_end', to=sid)


# -----------------------------------------------------------------
# 5. SERVER RUNNER
# This starts the Uvicorn server
# -----------------------------------------------------------------
if __name__ == "__main__":
    # Note: The startup_event() is automatically called by FastAPI/Uvicorn
    print("Starting Socket.IO server on http://127.0.0.1:8001")
    uvicorn.run(
        sio_app, 
        host="127.0.0.1", 
        port=8001
    )