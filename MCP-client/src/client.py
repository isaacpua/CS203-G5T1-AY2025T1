import json
from langchain_mcp_adapters.client import MultiServerMCPClient
from graph import build_graph, AgentState
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessageChunk, FunctionMessage, ToolMessage
from typing import AsyncGenerator, Any, Dict, Optional
import pandas as pd

async def stream_graph_response(input: AgentState, graph: StateGraph, config: dict = {}) -> AsyncGenerator[str, None]:
    """
    Stream the response from the graph while parsing out tool calls.

    Args:
        input: The input for the graph.
        graph: The graph to run.
        config: The config to pass to the graph. Required for memory.

    Yields:
        A processed string from the graph's chunked response.
    """
    async for message_chunk, metadata in graph.astream(
        input=input,
        stream_mode="messages",
        config=config
    ):
        node_name = metadata.get("langgraph_node", "")
        if node_name == "Formatting":
            print(f"Skipping output from formatting node")
            continue
        if isinstance(message_chunk, AIMessageChunk):
            # Check if this chunk has complete tool_calls (not just chunks)
            if hasattr(message_chunk, 'tool_calls') and message_chunk.tool_calls:
                for tool_call in message_chunk.tool_calls:
                    tool_name = tool_call.get('name', '')
                    
                    # Only process if we have a valid tool name (not empty)
                    if tool_name and tool_name == "open_login_browser":
                        user_guide = """🔐 *Paywall Detected*

I've detected that this content is behind a paywall and need your help to access it.

• A browser window is opening automatically
• Please log in to your account on the website
• After logging in successfully, close the browser window
• I'll then continue scraping the content with your authenticated session"""
                        yield user_guide
                        continue  # Important: continue after yielding

            # print("part one")
            if message_chunk.response_metadata:
                finish_reason = message_chunk.response_metadata.get("finish_reason", "")
                if finish_reason == "tool_calls":
                    yield "\n\n"

                if message_chunk.tool_call_chunks:
                    tool_chunk = message_chunk.tool_call_chunks[0]
                    tool_name = tool_chunk.get("name", "")
                    args = tool_chunk.get("args", "")
                                
                    # Don't yield anything for empty tool names to avoid infinite loops
                    if not tool_name:
                        continue
                        
                    # For other tools, we don't yield the tool call details
                    continue
                else:
                    # Only yield content if it's not empty to avoid spam
                    if message_chunk.content and message_chunk.content.strip():
                        yield message_chunk.content
                continue

        elif (hasattr(message_chunk, "tool_call_id")):
            if "detect_paywall" in getattr(message_chunk, "name") or "generate_ppt_json" in getattr(message_chunk, "name"):            
                print("Skipping tool call for detect_paywall, generate_ppt_json")
                continue
            
            # Special handling for open_login_browser completion
            if (hasattr(message_chunk, "name") and "open_login_browser" in getattr(message_chunk, "name") and
                hasattr(message_chunk, "content") and isinstance(message_chunk.content, str)):
                try:
                    # Parse the tool response to check if login was successful
                    login_response = json.loads(message_chunk.content)
                    if login_response.get("status") == "login_session_complete":
                        completion_message = """✅ *Authentication Complete!*

Great! I'm now proceeding to scrape the content with your login credentials. Please wait while I extract the full article...
"""
                        yield completion_message
                        continue
                    else:
                        # Handle other statuses if needed
                        yield "🔄 **Login session processing...** Please wait while I prepare to scrape the content."
                        continue
                except json.JSONDecodeError:
                    # Fallback to generic message if JSON parsing fails
                    yield "✅ **Login completed!** Proceeding with content extraction..."
                    continue
            
            # print(f"Message chunk: {message_chunk}")
            
            # TARGETED FIX: Extract content from scrape_single_url JSON for Jarvis to summarize
            if (hasattr(message_chunk, "name") and "scrape_single_url" in getattr(message_chunk, "name") and
                hasattr(message_chunk, "content") and isinstance(message_chunk.content, str)):
                content_str = message_chunk.content.strip()
                # Check for formatted JSON starting with { and containing "url" early
                if (content_str.startswith('{') and '"url":' in content_str[:100]):
                    try:
                        # Parse the JSON to extract meaningful content
                        scraped_data = json.loads(content_str)
                        
                        # Extract key information for Jarvis to work with
                        url = scraped_data.get("url", "")
                        status = scraped_data.get("status", "unknown")
                        
                        if status == "success" and "content" in scraped_data:
                            content = scraped_data["content"]
                            metadata = content.get("metadata", {})
                            title = metadata.get("title", "Untitled")
                            author = metadata.get("author", "Unknown author")
                            description = metadata.get("description", "")
                            
                            # Create a conversational summary for Jarvis
                            summary_for_jarvis = f"""Perfect! I've successfully scraped the article **"{title}"** by {author}.

{description}

I'm now formatting this content for you - a popup window will appear shortly with the full article, and I'll also prepare a PDF download so you can save it for later. The content looks comprehensive and should be very useful!"""
                            
                            yield summary_for_jarvis
                            continue
                        else:
                            yield f"❌ Scraping failed with status: {status}"
                            continue
                            
                    except json.JSONDecodeError:
                        print("Failed to parse scrape_single_url JSON response")
                        yield "✅ Content scraped successfully (parsing issue - check logs)"
                        continue
                            
            # Only yield non-empty content to avoid spam
            if hasattr(message_chunk, 'content') and message_chunk.content and message_chunk.content.strip():
                yield message_chunk.content
        elif isinstance(message_chunk, ToolMessage):
            content = message_chunk.content
            if isinstance(content, dict) and "intent" in content:
                yield json.dumps({"type": "structured", **content})
            elif isinstance(content, str) and content.strip().startswith("{") and '"intent"' in content:
                try:
                    parsed = json.loads(content)
                    yield json.dumps({"type": "structured", **parsed})
                except Exception:
                    yield json.dumps({"type": "content", "content": content})
