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
from text_to_speech import text_to_speech
from routes.websocket import ws_manager

# from fastapi import Request
from app import app_state

from services.scraped_content_pdf import generate_scraped_content_pdf

import azure.cognitiveservices.speech as speechsdk

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

@router.get("/popup")
async def get_popup():
    popup_data = popup_manager.get_popup_data()
    if popup_data:
        # print("popup_data", popup_data)
        popup_manager.clear_popup_data()
        return {"has_popup": True, "popup_data": popup_data}
    else:
        return {"has_popup": False}

class HtmlContent(BaseModel):
    content: str

@router.post("/download-popup")
async def download_popup(data: HtmlContent):
    """
    Download popup content as PDF.
    Automatically detects content type and routes to appropriate PDF service.
    """
    html_content = data.content
        # Detect content type and route to appropriate PDF service
    if is_scraped_content(html_content):
        print("Detected scraped content - using specialized PDF service")
        pdf_content = generate_scraped_content_pdf(html_content)
    else:
        print("Detected non-scraped content - using original PDF service")
        pdf_content = getPdf(html_content)
    
    return pdf_content

# For dexnew_frontend to use tool in mcp_backend via dexnew_backend
@router.post("/tools/launch-avatar")
async def call_launch_avatar(request: Request):
    """
    Backend route that calls the MCP tool `launch_avatar` with a URL.
    Frontend should POST { "url": "..." } to this.
    """
    data = await request.json()
    url = data.get("url")

    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' in request")

    try:
        tools = await app_state.mcp_client.get_tools()
        tool = next((t for t in tools if t.name == "launch_avatar"), None)

        if not tool:
            raise HTTPException(status_code=500, detail="Tool 'launch_avatar' not found")

        result = await tool.ainvoke({"url": url})
        
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# @router.post("/tools/next-slide")
# async def call_next_slide(request: Request):
#     """
#     Backend route that calls the MCP tool `next_slide`.
#     Frontend can POST to this without any body.
#     """
#     try:
#         tools = await app_state.mcp_client.get_tools()
#         tool = next((t for t in tools if t.name == "next_slide"), None)

#         if not tool:
#             raise HTTPException(status_code=500, detail="Tool 'next_slide' not found")

#         result = await tool.ainvoke({})
        
#         return {"status": "success", "result": result}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# ------------MCP VER---------------------
# @router.post("/tools/extract-speaker-notes")
# async def call_extract_speaker_notes(request: Request):
#     """
#     Calls the MCP tool 'extract_speaker_notes' with a ppt_filename.
#     Expects JSON: { "ppt_filename": "yourfile.pptx" }
#     """
#     data = await request.json()
#     ppt_filename = data.get("ppt_filename")
#     if not ppt_filename:
#         raise HTTPException(status_code=400, detail="Missing 'ppt_filename' in request")
#     try:
#         tools = await app_state.mcp_client.get_tools()
#         tool = next((t for t in tools if t.name == "extract_speaker_notes"), None)
#         if not tool:
#             raise HTTPException(status_code=500, detail="Tool 'extract_speaker_notes' not found")
#         result = await tool.ainvoke({"ppt_filename": ppt_filename})
#         return {"status": "success", "result": result}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @router.post("/tools/speaker-note-to-speech")
# async def call_speaker_note_to_speech(request: Request):
#     """
#     Calls the MCP tool 'speaker_note_to_speech' with a note.
#     Expects JSON: { "note": "your speaker note text" }
#     """
#     data = await request.json()
#     note = data.get("note")
#     if not note:
#         raise HTTPException(status_code=400, detail="Missing 'note' in request")
#     try:
#         tools = await app_state.mcp_client.get_tools()
#         tool = next((t for t in tools if t.name == "speaker_note_to_speech"), None)
#         if not tool:
#             raise HTTPException(status_code=500, detail="Tool 'speaker_note_to_speech' not found")
#         result = await tool.ainvoke({"note": note})
#         return {"status": "success", "result": result}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}
    
# # Global flag to control stopping
# is_presenting = False

# import os

# @router.post("/tools/start-presentation")
# async def start_presentation(request: Request):
# # async def start_presentation(data: PresentationStartRequest):
#     global is_presenting

#     # Always use the file in src\uploads
#     # This is a hardcoded path for demonstration purposes.
#     ppt_filename = os.path.join(
#         os.path.dirname(__file__),
#         "..", "uploads", "MCP Final Presenter.pptx"
#     )
#     ppt_filename = os.path.abspath(ppt_filename)

#     if not os.path.isfile(ppt_filename):
#         raise HTTPException(status_code=400, detail=f"File not found: {ppt_filename}")

#     try:
#         tools = await app_state.mcp_client.get_tools()
#         extract_tool = next((t for t in tools if t.name == "extract_speaker_notes"), None)
#         speak_tool = next((t for t in tools if t.name == "speaker_note_to_speech"), None)
#         advance_tool = next((t for t in tools if t.name == "next_slide"), None)

#         if not extract_tool or not speak_tool or not advance_tool:
#             raise HTTPException(status_code=500, detail="Required tools not found")

#         # Extract notes
#         notes_result = await extract_tool.ainvoke({"ppt_filename": ppt_filename})
#         if isinstance(notes_result, str):
#             try:
#                 notes_result = json.loads(notes_result)
#             except Exception:
#                 raise HTTPException(status_code=500, detail="Failed to parse notes_result as JSON")

#         print("notes_result:", notes_result)
        
#         if not isinstance(notes_result, dict):
#             raise HTTPException(status_code=500, detail="Invalid notes_result format")

#         notes_list = notes_result.get("notes", [])
#         if not isinstance(notes_list, list):
#             raise HTTPException(status_code=500, detail="Invalid notes format")

#         is_presenting = True

#         for i, note in enumerate(notes_list):
#             # Wait while paused
#             while is_paused:
#                 await asyncio.sleep(0.5)

#             if not is_presenting:
#                 break

#             text = note.get("notes") or ""
#             if text.strip():
#                 result = await speak_tool.ainvoke({"note": text})
#                 print(f"Slide {i+1} result:", result)

#                 if isinstance(result, dict) and result.get("status") == "done":
#                     print("End of presentation reached.")
#                     break
#             else:
#                 print(f"Slide {i+1} has no speaker notes; skipping.")

#             # Advance to next slide *unless it's the last one*
#             if i < len(notes_list) - 1:
#                 result = await advance_tool.ainvoke({})
#                 print(f"Advanced to slide {i+2}: {result}")

#         return {"status": "success", "slides_read": len(notes_list)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during presentation: {str(e)}")

# is_paused = False
# @router.post("/tools/pause-presentation")
# async def pause_presentation():
#     """
#     Pauses the automated presentation.
#     """
#     global is_paused
#     is_paused = True
#     return {"status": "success", "message": "Presentation paused"}

# @router.post("/tools/resume-presentation")
# async def resume_presentation():
#     """
#     Resumes the automated presentation.
#     """
#     global is_paused
#     is_paused = False
#     return {"status": "success", "message": "Presentation resumed"}


# ------------LOCAL OUTOPUT BY SENTENCES---------------------
# def split_sentences(text):
#     return re.split(r'(?<=[.?!]) +', text.strip())

# @router.post("/tools/start-presentation")
# async def start_presentation():
#     app_state.stop_event.clear()
#     ppt_filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "MCP Final Presenter.pptx"))

#     if not os.path.isfile(ppt_filename):
#         raise HTTPException(status_code=400, detail=f"File not found: {ppt_filename}")

#     try:
#         prs = Presentation(ppt_filename)
#         notes_list = [
#             slide.notes_slide.notes_text_frame.text
#             if slide.has_notes_slide and slide.notes_slide.notes_text_frame else ""
#             for slide in prs.slides
#         ]

#         speech_key = os.environ.get("AZURE_SPEECH_API_KEY")
#         speech_region = os.environ.get("AZURE_SPEECH_REGION")

#         if not speech_key or not speech_region:
#             raise HTTPException(status_code=500, detail="Azure Speech credentials missing")

#         tools = await app_state.mcp_client.get_tools()
#         next_slide_tool = next((t for t in tools if t.name == "next_slide"), None)

#         if not next_slide_tool:
#             raise HTTPException(status_code=500, detail="Tool 'next_slide' not found")

#         for i, note in enumerate(notes_list):
#             print(f"Processing slide {i+1}")

#             if app_state.stop_event.is_set():
#                 print("🛑 Stop signal received. Ending presentation.")
#                 break

#             if note.strip():
#                 try:
#                     sentences = split_sentences(note)
#                     for j, sentence in enumerate(sentences):
#                         if not sentence.strip():
#                             continue

#                         print(f"🗣️ Speaking sentence {j+1} of slide {i+1}")
#                         await ws_manager.emit("talking")

#                         try:
#                             await text_to_speech(sentence, speech_key, speech_region)
#                         except Exception as e:
#                             print(f"Error in sentence {j+1}: {e}")

#                         await ws_manager.emit("not_talking")
#                         # await asyncio.sleep(0.3)

#                     print(f"Slide {i+1} done.")
#                 except Exception as e:
#                     print(f"Stopped at slide {i+1}: {e}")
#                     break
#             else:
#                 print(f"Slide {i+1} skipped — no speaker notes.")

#             try:
#                 await next_slide_tool.ainvoke({})
#                 print(f"Called next_slide tool for slide {i+1}")
#             except Exception as e:
#                 print(f"Failed to call next_slide tool after slide {i+1}: {e}")
#                 break

#             await ws_manager.emit("advance_slide", {"slide": i + 1})

#         print("Presentation finished or stopped")
#         return {"status": "success", "slides_read": len(notes_list)}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# ------------w/o mcp extract speaker notes----------------
# @router.post("/tools/start-presentation")
# async def start_presentation():
#     app_state.stop_event.clear()  # 🔁 reset stop flag
#     ppt_filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "MCP Final Presenter.pptx"))

#     if not os.path.isfile(ppt_filename):
#         raise HTTPException(status_code=400, detail=f"File not found: {ppt_filename}")

#     try:
#         prs = Presentation(ppt_filename)
#         notes_list = []
#         for i, slide in enumerate(prs.slides):
#             text = ""
#             if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
#                 text = slide.notes_slide.notes_text_frame.text
#             notes_list.append(text)

#         speech_key = os.environ.get("AZURE_SPEECH_API_KEY")
#         speech_region = os.environ.get("AZURE_SPEECH_REGION")

#         if not speech_key or not speech_region:
#             raise HTTPException(status_code=500, detail="Azure Speech credentials missing")
        
#         tools = await app_state.mcp_client.get_tools()
#         next_slide_tool = next((t for t in tools if t.name == "next_slide"), None)

#         if not next_slide_tool:
#             raise HTTPException(status_code=500, detail="Tool 'next_slide' not found")

#         for i, note in enumerate(notes_list):
#             print(f"Processing slide {i+1}")

#             if app_state.stop_event.is_set():
#                 print("🛑 Stop signal received. Ending presentation.")
#                 break

#             if note.strip():
#                 try:
#                     print(f"Calling text_to_speech for slide {i+1}")
#                     await text_to_speech(note, speech_key, speech_region, ws_manager=ws_manager)
#                     print(f"Slide {i+1} done.")
#                 except Exception as e:
#                     print(f"Stopped at slide {i+1}: {e}")
#                     break
#             else:
#                 print(f"Slide {i+1} skipped — no speaker notes.")

#             # Call next_slide tool to advance
#             try:
#                 await next_slide_tool.ainvoke({})
#                 print(f"Called next_slide tool for slide {i+1}")
#             except Exception as e:
#                 print(f"Failed to call next_slide tool after slide {i+1}: {e}")
#                 break

#             print(f"Emitting advance_slide for slide {i+1}")
#             await ws_manager.emit("advance_slide", {"slide": i + 1})

#         print("Presentation finished or stopped")


#         return {"status": "success", "slides_read": len(notes_list)}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/start-presentation")
async def start_presentation():
    ppt_filename_only = "MCP Final Presenter.pptx"
    ppt_path_local = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", ppt_filename_only))

    if not os.path.isfile(ppt_path_local):
        raise HTTPException(status_code=400, detail=f"File not found: {ppt_path_local}")

    try:
        # Try to extract speaker notes via MCP tool
        notes_list = []
        try:
            tools = await app_state.mcp_client.get_tools()
            extract_tool = next((t for t in tools if t.name == "extract_speaker_notes"), None)

            if extract_tool:
                response = await extract_tool.ainvoke({"ppt_filename": ppt_filename_only})
                
                # Parse JSON if returned as a string
                if isinstance(response, str):
                    response = json.loads(response)

                if response.get("status") == "success":
                    notes_list = [n["notes"] for n in response["notes"]]
                    print("✅ Notes extracted using MCP tool.")
                else:
                    raise ValueError(response.get("message", "Unknown MCP tool error"))
            else:
                raise ValueError("extract_speaker_notes tool not found")
        
        except Exception as mcp_err:
            print(f"⚠️ MCP tool failed: {mcp_err}. Falling back to local parsing.")
            prs = Presentation(ppt_path_local)
            for slide in prs.slides:
                note = ""
                if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                    note = slide.notes_slide.notes_text_frame.text
                notes_list.append(note)

        # Get TTS credentials
        speech_key = os.environ.get("AZURE_SPEECH_API_KEY")
        speech_region = os.environ.get("AZURE_SPEECH_REGION")
        if not speech_key or not speech_region:
            raise HTTPException(status_code=500, detail="Azure Speech credentials missing")

        # Get next_slide tool
        tools = await app_state.mcp_client.get_tools()
        next_slide_tool = next((t for t in tools if t.name == "next_slide"), None)
        if not next_slide_tool:
            raise HTTPException(status_code=500, detail="Tool 'next_slide' not found")

        # Process each slide
        for i, note in enumerate(notes_list):
            print(f"\n📄 Processing slide {i + 1}")

            if app_state.stop_event.is_set():
                print("🛑 Stop signal received. Ending presentation.")
                break

            if note.strip():
                try:
                    print(f"🗣️ Speaking slide {i + 1}")
                    await text_to_speech(note, speech_key, speech_region, ws_manager=ws_manager)
                    print(f"✅ Finished slide {i + 1}")
                except Exception as e:
                    print(f"❌ Error on slide {i + 1}: {e}")
                    break
            else:
                print(f"⚠️ Slide {i + 1} has no notes, skipping.")

            # Advance slide
            try:
                await next_slide_tool.ainvoke({})
                print(f"➡️ Called next_slide tool for slide {i + 1}")
            except Exception as e:
                print(f"❌ Failed to advance slide {i + 1}: {e}")
                break

            # Emit to frontend
            await ws_manager.emit("advance_slide", {"slide": i + 1})

        print("\n✅ Presentation complete.")
        return {"status": "success", "slides_read": len(notes_list)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/tools/stop-presentation")
# async def stop_presentation():
#     app_state.stop_event.set()

#     if app_state.synthesizer:
#         try:
#             app_state.synthesizer.stop_speaking()
#             print("⛔ Speech interrupted.")
#         except Exception as e:
#             print("⚠️ Error stopping synthesizer:", str(e))

#     return {"status": "Stopping presentation"}

@router.post("/tools/pause-presentation")
async def pause_presentation():
    print("⏸️ Pause triggered")
    # await ws_manager.emit("not_talking")
    app_state.pause_event.set()
    return {"status": "paused"}

@router.post("/tools/resume-presentation")
async def resume_presentation():
    print("▶️ Resume triggered")
    # await ws_manager.emit("talking")
    app_state.pause_event.set()  # re-triggers wait()
    return {"status": "resumed"}