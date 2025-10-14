from langchain_openai import ChatOpenAI
from langchain_community.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv
import os
# Load .env file
load_dotenv()

GPT4O_API_BASE = os.getenv("GPT4O_API_BASE")
GPT4O_DEPLOYMENT_NAME = os.getenv("GPT4O_DEPLOYMENT_NAME")
GPT4O_API_KEY = os.getenv("GPT4O_API_KEY")
GPT4O_API_VERSION = os.getenv("GPT4O_API_VERSION")

def llm():
    return ChatOpenAI(
        model="gpt-4o", # <-- Specify the model name directly
        temperature=1
    )