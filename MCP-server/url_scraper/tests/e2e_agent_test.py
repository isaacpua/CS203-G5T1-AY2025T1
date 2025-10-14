#!/usr/bin/env python3
"""
End-to-end test for the web scraping workflow using a LangGraph agent.

This script defines a simple agent that follows the paywall bypass logic:
1. Detects paywall on a URL.
2. If a paywall is found, it opens a browser for the user to log in.
3. After login (or if no paywall was found), it scrapes the full content.
"""

import asyncio
import json
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from fastmcp import Client
import pprint

# --- Agent State Definition ---
class AgentState(TypedDict):
    """
    Defines the state of our agent.
    """
    url: str
    session_dir: str | None
    storage_state_path: str | None  # Path to the saved session state
    session_used_in_detection: bool # Flag to check if a session was used
    paywall_status: Literal[
        "unknown", "detected", "not_detected", 
        "login_complete", "scrape_success", "scrape_paywall_persistent"
    ]
    scraped_content: dict | None
    error: str | None

# --- MCP Client Setup ---
SERVER_URL = "http://localhost:8080/scraper/"

# --- Agent Node Implementations ---

async def detect_paywall_node(state: AgentState) -> AgentState:
    """
    Calls the detect_paywall tool and updates the agent's state.
    """
    print("\n--- Node: detect_paywall ---")
    url = state["url"]
    storage_state_path = state.get("storage_state_path")
    print(f"Checking URL: {url}")

    try:
        async with Client(SERVER_URL) as client:
            params = {"url": url, "storage_state_path": storage_state_path}
            result_list = await client.call_tool("detect_paywall", params)

        if not result_list or not hasattr(result_list[0], 'text'):
            return {**state, "error": "Invalid response from detect_paywall tool"}

        result_json = json.loads(result_list[0].text)
        pprint.pprint(result_json)

        if result_json.get("status") == "error":
            return {**state, "error": result_json.get("error", "Unknown tool error")}

        paywall_detected = result_json.get("paywall_detected", False)
        session_info = result_json.get("session_info", {})
        storage_path_used = session_info.get("storage_state_path")

        return {
            **state,
            "paywall_status": "detected" if paywall_detected else "not_detected",
            "session_dir": session_info.get("user_data_dir"),
            "storage_state_path": storage_path_used,
            "session_used_in_detection": bool(storage_path_used)
        }
    except Exception as e:
        return {**state, "error": f"Failed to call detect_paywall: {e}"}


async def open_login_browser_node(state: AgentState) -> AgentState:
    """
    Opens the browser for the user to log in and saves the session state.
    """
    print("\n--- Node: open_login_browser ---")
    url = state["url"]
    session_dir = state.get("session_dir")
    print(f"Opening browser for URL: {url}")

    try:
        async with Client(SERVER_URL) as client:
            result_list = await client.call_tool(
                "open_login_browser",
                {"url": url, "user_data_dir": session_dir, "wait_timeout_seconds": 420}
            )

        if not result_list or not hasattr(result_list[0], 'text'):
            return {**state, "error": "Invalid response from open_login_browser tool"}

        result_json = json.loads(result_list[0].text)
        pprint.pprint(result_json)
        
        session_info = result_json.get("session_info", {})
        
        if result_json.get("status") == "login_session_complete":
             print(f"✅ Login reported as complete (method: {result_json.get('completion_method')}).")
             return {
                 **state,
                 "paywall_status": "login_complete",
                 "session_dir": session_info.get("user_data_dir"),
                 "storage_state_path": session_info.get("storage_state_path")
             }
        else:
            return {**state, "error": result_json.get("error_message", "Login failed")}

    except Exception as e:
        return {**state, "error": f"Failed to call open_login_browser: {e}"}


async def scrape_content_node(state: AgentState) -> AgentState:
    """
    Scrapes the final content using the saved session state.
    """
    print("\n--- Node: scrape_content ---")
    url = state["url"]
    storage_state_path = state.get("storage_state_path")
    print(f"Scraping final content for URL: {url}")
    if storage_state_path:
        print(f"Using session state file: {storage_state_path}")

    try:
        async with Client(SERVER_URL) as client:
            result_list = await client.call_tool(
                "scrape_single_url",
                {"url": url, "storage_state_path": storage_state_path}
            )

        if not result_list or not hasattr(result_list[0], 'text'):
            return {**state, "error": "Invalid response from scrape_single_url tool"}

        result_json = json.loads(result_list[0].text)
        
        scrape_status = result_json.get("status")
        final_status = "unknown"
        
        if scrape_status == "success":
            print("✅ Content scraped successfully!")
            final_status = "scrape_success"
        elif scrape_status == "paywall_persistent":
            print(" Mapped status to: scrape_paywall_persistent", flush=True)
            final_status = "scrape_paywall_persistent"
        else:
            print(f"⚠️ Scraping returned an unexpected status: {scrape_status}")
            return {**state, "error": result_json.get("error", "Failed to scrape"), "scraped_content": result_json.get("content")}

        return {
            **state,
            "paywall_status": final_status,
            "scraped_content": result_json.get("content")
        }

    except Exception as e:
        return {**state, "error": f"Failed to call scrape_single_url: {e}"}


# --- Graph Routers ---

def entry_router(state: AgentState) -> Literal["open_login_browser", "scrape_content", "__end__"]:
    """
    Determines the next step in the workflow based on the initial paywall detection.
    """
    print(f"\n--- Router: entry_router ---")
    print(f"Current paywall status: {state['paywall_status']}")

    if state.get("error"):
        print("❌ Error detected, ending graph.")
        return END

    if state["paywall_status"] == "detected":
        if state.get("session_used_in_detection"):
            print("🚦 Paywall detected, but a session was already used. Routing directly to 'scrape_content'.")
            return "scrape_content"
        
        print("🚦 Paywall detected and no session used. Routing to 'open_login_browser'.")
        return "open_login_browser"
    
    if state["paywall_status"] in ["not_detected", "login_complete"]:
        print("🚦 No paywall or login complete. Routing to 'scrape_content'.")
        return "scrape_content"
    
    print("🚦 Unknown state, ending graph.")
    return END

def after_scrape_router(state: AgentState) -> Literal["open_login_browser", "__end__"]:
    """
    Determines the next step after a scrape attempt.
    """
    print(f"\n--- Router: after_scrape_router ---")
    print(f"Current paywall status: {state['paywall_status']}")

    if state["paywall_status"] == "scrape_success":
        print("✅ Scrape was successful. Ending graph.")
        return END
    
    if state["paywall_status"] == "scrape_paywall_persistent":
        print(" PAYWALL IS STILL THERE. The session is likely invalid. Routing back to 'open_login_browser'.")
        return "open_login_browser"

    print("🚦 Scrape ended with an unhandled status, ending graph.")
    return END


# --- Graph Definition ---

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("detect_paywall", detect_paywall_node)
    workflow.add_node("open_login_browser", open_login_browser_node)
    workflow.add_node("scrape_content", scrape_content_node)

    workflow.add_conditional_edges(
        "detect_paywall",
        entry_router,
        {
            "open_login_browser": "open_login_browser",
            "scrape_content": "scrape_content",
            "__end__": END,
        },
    )
    workflow.add_edge("open_login_browser", "scrape_content")
    
    # New conditional edge to create the feedback loop
    workflow.add_conditional_edges(
        "scrape_content",
        after_scrape_router,
        {
            "open_login_browser": "open_login_browser",
            "__end__": END
        }
    )

    workflow.set_entry_point("detect_paywall")
    
    return workflow.compile()


# --- Main Execution ---

def get_initial_state(url: str) -> AgentState:
    return {
        "url": url,
        "session_dir": None,
        "storage_state_path": None,
        "session_used_in_detection": False,
        "paywall_status": "unknown",
        "scraped_content": None,
        "error": None,
    }

async def main():
    print("🚀 Starting End-to-End Paywall Agent Test 🚀")
    print("============================================================")
    
    test_url = input("Enter the URL to test (e.g., a Medium article): ").strip()
    if not test_url:
        print("No URL provided. Exiting.")
        return

    app = build_graph()
    initial_state = get_initial_state(test_url)

    final_state = await app.ainvoke(initial_state)

    print("\n\n🏁 --- Workflow Complete --- 🏁")
    print("\nFull final state object:")
    pprint.pprint(final_state)
    
    if final_state.get("scraped_content"):
        print("\n--- Final Scraped Content ---")
        markdown = final_state["scraped_content"].get("main_text_markdown", "No markdown content found.")
        print(markdown[:2000] + "..." if len(markdown) > 2000 else markdown)
    elif final_state.get("error"):
        print(f"\n--- Error ---")
        print(final_state["error"])


if __name__ == "__main__":
    asyncio.run(main()) 