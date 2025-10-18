from fastapi import APIRouter, HTTPException,Form, File, UploadFile, Request
from pydantic import BaseModel
from typing import Optional, List
import uuid
import json
from client import stream_graph_response
from graph import AgentState
from langchain_core.messages import HumanMessage
from fastapi.responses import StreamingResponse
from popup import popup_manager
from services.downloadpdf import getPdf
import os, re
import asyncio
from pptx import Presentation
from routes.websocket import ws_manager

# from fastapi import Request
from app import app_state

from services.scraped_content_pdf import generate_scraped_content_pdf


from services.file_handler import load_data

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str

def is_scraped_content(html_content: str) -> bool:
    """
    Detect if content is from the scraping workflow based on LLM formatting markers.
    
    Args:
        html_content: HTML content to analyze
        
    Returns:
        bool: True if content is from scraping workflow, False otherwise
    """
    # Check for the article-content wrapper that the LLM formatting service adds
    if 'class="article-content"' in html_content:
        return True
    
    # Additional check for content-container wrapper
    if 'class="content-container"' in html_content:
        return True
    
    # Check for source URL div that the formatter adds to scraped content
    if 'Source:</strong>' in html_content and 'target="_blank"' in html_content:
        return True
    
    return False

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    from app import app_state
    return {"status": "healthy", "agent_initialized": app_state.graph is not None}

@router.post("/test")
async def test(request: ChatRequest):
    """Test endpoint"""
    return {"status": "healthy", "message": request.message, "thread_id": request.thread_id}

@router.get("/tools")
async def get_available_tools():
    """Get list of available tools"""
    from app import app_state
    if app_state.mcp_client is None:
        raise HTTPException(status_code=500, detail="MCP client not initialized")
    
    tools = await app_state.mcp_client.get_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "args_schema": str(tool.args_schema) if hasattr(tool, 'args_schema') else None
            }
            for tool in tools
        ]
    }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    from app import app_state
    """Non-streaming chat endpoint"""
    if app_state.graph is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    # Generate thread_id if not provided
    thread_id = request.thread_id or str(uuid.uuid4())
    
    graph_config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # Collect all responses
    full_response = ""
    async for response_chunk in stream_graph_response(
        input=AgentState(messages=[HumanMessage(content=request.message)]),
        graph=app_state.graph,
        config=graph_config
    ):
        full_response += response_chunk
    
    return ChatResponse(response=full_response, thread_id=thread_id)

@router.post("/chat/stream")
async def chat_stream(
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    geojson: Optional[UploadFile] = File(None),
    thread_id: Optional[str] = Form(None)
):
    """Streaming chat endpoint"""
    from app import app_state
    if app_state.graph is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    """
        DISCLAIMER: geojson file handles only 1 file. Will need to update this chunk of code to handle multiple files.
        intern: Good luck next intern
    """

    data_records = []
    df = None
    geo_df = None
    pptxpdf = None

    # --- MODIFIED FILE HANDLING LOGIC ---
    # This block is updated to handle all document types intended for text extraction.
    if file and file.filename:
        # Define the file extensions that should be treated as documents for text extraction.
        document_extensions = ['.pdf', '.pptx', '.docx', '.txt']
        
        # Check if the uploaded file has one of the specified extensions.
        if any(file.filename.lower().endswith(ext) for ext in document_extensions):
            pptxpdf = load_data(file)
            print(f"[DEBUG] Loaded document file for text extraction: {file.filename}")
        # All other file types are assumed to be tabular data (e.g., CSV, Excel).
        else:
            try:
                df = load_data(file)
                data_records = df.to_dict(orient="records")
                print(f"[DEBUG] Loaded tabular data file: {file.filename}")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to process tabular file: {str(e)}")
    # --- END OF MODIFIED LOGIC ---

    # --- Load GeoJSON if present ---
    if geojson:
        print(f"[DEBUG] Received GeoJSON file: {geojson.filename}")
        try:
            import geopandas as gpd
            geo_df = gpd.read_file(geojson.file).to_json()
            geo_df = json.loads(geo_df)
            print(f"[DEBUG] GeoJSON loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load GeoJSON: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid GeoJSON file: {str(e)}")

    # Generate thread_id if not provided
    thread_id = thread_id or str(uuid.uuid4())
    
    graph_config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    async def generate_response():
        yield f"data: {json.dumps({'thread_id': thread_id, 'type': 'metadata'})}\n\n"

        async for response in stream_graph_response(
            input=AgentState(messages=[HumanMessage(content=message)], data=data_records, geojson=geo_df, pptxpdf=pptxpdf),
            graph=app_state.graph,
            config=graph_config
        ):
            if isinstance(response, str) and response.strip().startswith("{") and '"intent"' in response:
                yield f"data: {response}\n\n"
            else:
                yield f"data: {json.dumps({'content': response, 'type': 'content'})}\n\n"

        yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
