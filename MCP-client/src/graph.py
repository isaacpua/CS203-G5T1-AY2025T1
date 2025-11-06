import os
import json
from pydantic import BaseModel
from typing import Annotated, List, Optional
from dotenv import load_dotenv

from langchain.tools import BaseTool
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessageChunk, ToolMessage
from langchain_openai import ChatOpenAI # Changed from AzureChatOpenAI

load_dotenv()

# --- 1. Simplified AgentState ---
# All state related to paywalls, sessions, and file uploads has been removed.
class AgentState(BaseModel):
    messages: Annotated[List, add_messages]


def build_graph(tools: List[BaseTool] = [], access_token: str = ""):
    
    # --- 2. Simplified System Prompt ---
    # This prompt is now simple and only describes your 4 new tools.
    # All old logic (paywalls, pptx, run_analysis) is gone.
    system_prompt = """
    Your name is TARIFF. You are a helpful assistant that can use the following tools to help the user.

    When the user sends a request, determine what they want and call the appropriate tool. Do not attempt to solve tasks yourself if a tool exists — always delegate to tools.

    ---

    AVAILABLE TOOLS:
    {tools}

    Example tool usage:
    - If the user says "greet Calvin", call `greet(name="calvin")`.
    - If the user asks for tariff news, call `newsletter_scrape()`.
    - If the user provides a URL to scrape, call `scrape_single_url(url="...")`.
    - If the user wants to generate new tariff forecasts, call `forecast_tariffs()`.
    - If the user wants to analyze tariff data, call `analyze()`.
    - If the user wants to send an email, call `send_email_logic(...)`. STRICTLY Make sure the email content sent starts with "Dear User" and ends with "Best regards, TARIFF".

    ---

    Please call the tools one at a time to avoid crashing. Reply the user as fast as possible. Be concise, professional, and avoid verbose output unless the user requests it.
    """

    # --- 3. Use ChatOpenAI ---
    # Reads OPENAI_API_KEY and OPENAI_MODEL_NAME from your .env file
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
        temperature=0
    )

    # --- 4. Bind Tools and Create Agent ---
    if tools:
        llm = llm.bind_tools(tools)
        
        # Create the tool descriptions for the prompt
        tools_descriptions = "\n\n".join(
            [f"Tool: {tool.name}\nDescription: {tool.description}\nParameters: {tool.args_schema}" for tool in tools]
        )
        system_prompt = system_prompt.format(tools=tools_descriptions)
    
    # Define the agent logic
    def assistant(state: AgentState) -> AgentState:
        """
        This is the main agent node. It's now much simpler.
        It just prepends the system prompt and calls the LLM.
        """
        # Create the message list to send to the LLM
        messages_with_prompt = [SystemMessage(content=system_prompt)] + state.messages
        
        # Invoke the LLM
        response = llm.invoke(messages_with_prompt)
        
        # Append the LLM's response to the state
        state.messages.append(response)
        
        return state
    
    # --- 5. Build the Simplified Graph ---
    builder = StateGraph(AgentState)

    # Add the two nodes we need: the agent and the tools
    builder.add_node("TARIFF", assistant)
    builder.add_node("tools", ToolNode(tools))

    # The graph starts with the "TARIFF" (agent) node
    builder.add_edge(START, "TARIFF")

    # After "TARIFF" runs, check if it called a tool
    builder.add_conditional_edges(
        "TARIFF",
        tools_condition,
        # The tools_condition function will automatically route
        # to "tools" if a tool is called, or to END if not.
        {"tools": "tools", "__end__": END},
    )

    # After the "tools" node runs, send the output back to "TARIFF"
    builder.add_edge("tools", "TARIFF")

    # Compile the graph with memory
    return builder.compile(checkpointer=MemorySaver())