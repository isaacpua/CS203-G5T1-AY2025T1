import json
import uvicorn
import configparser, msal, os
import asyncio
import azure.cognitiveservices.speech as speechsdk
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph.state import CompiledStateGraph
from graph import build_graph
from typing import Optional, Any
from routes.websocket import ws_manager 

# Imports for Desktop automation
from client_ms_graph import ClientMsGraph

app = FastAPI(title="Jarvis")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store the initialized components
class AppState:
    def __init__(self):
        self.graph: Optional[CompiledStateGraph] = None
        self.mcp_client: Optional[MultiServerMCPClient] = None
        self.msgraph_access_token: str = ""

        self.stop_event: Optional[asyncio.Event] = None
        self.pause_event: Optional[asyncio.Event] = None
        self.synthesizer: Optional[Any] = None 
        
app_state = AppState()

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP client, graph and microsoft graph on startup"""
    app_state.stop_event = asyncio.Event()
    with open("mcp_config.json", "r") as f:
        config = json.load(f)

    # Initialise client msgraph, Use True / False to toggle msgraph authentication
    if False:
        print("Getting msgraph access token")
        print("If you see this and get stuck here, please go into dexbackend app.py code to set the first if True in app startup to if False")
        await get_msgraph_accesss_token()

        print("access token: ", app_state.msgraph_access_token[:50])
        config["mcpServers"]["desktop_automation"] = {
            "url": "http://127.0.0.1:8000/desktop_automation/mcp",
            "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {app_state.msgraph_access_token}"}
        }

    app_state.mcp_client = MultiServerMCPClient(
        connections=config["mcpServers"]
    )

    tools = await app_state.mcp_client.get_tools()
    app_state.graph = build_graph(tools=tools, access_token=app_state.msgraph_access_token)
    print("Jarvis Agent initialized successfully!")

from routes.routes import router
app.include_router(router)

# Function to initialise client ms graph
async def get_msgraph_accesss_token():
    # Get ms graph configurations
    config = configparser.ConfigParser()
    config.read(['config.cfg'])
    azure_settings = config["azure"]
    client_id = azure_settings['clientId']
    tenant_id = azure_settings['tenantId']
    scopes = azure_settings['graphUserScopes'].split(' ')

    # Set up cache
    cache = msal.SerializableTokenCache()
    cache_file = "token_cache.bin"
    if os.path.exists(cache_file):
        cache.deserialize(open(cache_file, "rb").read())

    app = msal.PublicClientApplication(client_id=client_id, token_cache=cache)
    
    # Attempt to get access token from cache
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, accounts[0])
        if result and "access_token" in result:
            app_state.msgraph_access_token = result["access_token"]
            print("access token aquired silently")

    # Authenticate to get access token
    if app_state.msgraph_access_token == "":
        flow = app.initiate_device_flow(scopes)
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            app_state.msgraph_access_token = result["access_token"]
            print("access token acquired normally")

    # Write token cache
    with open(cache_file, "wb") as f:
        f.write(cache.serialize().encode("utf-8"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keeps the connection open
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 