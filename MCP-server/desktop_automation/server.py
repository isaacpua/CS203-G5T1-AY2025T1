import configparser
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from pydantic import Field
# from serverGraph import ServerGraph
from desktop_automation.serverGraph import ServerGraph

from typing import Optional
import os
from desktop_automation.news.merge_documents import find_latest_docx, convert_docx_to_html_text, render_and_extract_text
from desktop_automation.news.news_playwright import check_news_smart
from typing_extensions import Annotated


# Initialize the FastMCP server
mcp = FastMCP(
    name="DesktopAutomation",
    instructions="This server provides tools for automating desktop tasks and browser automation.",
)

########################################## MS GRAPH TOOLS ##########################################
# Initialise Global Variables
graph_client: ServerGraph

# Send email without attachment Tool
@mcp.tool(
    name="send_email_without_attachment",
    description="Sends an email without attachment through the user's email."
)
async def send_email_without_attachment(
    subject: str = Field(..., description="The subject of the email"),
    body: str = Field(..., description="The body of the email"),
    recipients: list[str] = Field(..., description="The main recipients of the email"),
):
    # Get access token from http header
    print("Getting access token from http header")
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return "Missing or invalid Authorization header."
    access_token = auth_header.split(" ", 1)[1]
    print("Found access token: ", access_token)

    # Get Config, can abstract out
    print("Extracting Azure Config")
    config = configparser.ConfigParser()
    config.read(['config.cfg', 'config.dev.cfg'])
    azure_settings = config['azure']
    print("Extracted Azure Config: ", azure_settings)

    # Create ServerGraph client
    print("Creating ms graph client")
    try: 
        graph_client = ServerGraph(azure_settings, access_token)
        print("Sucessfully created ms graph client")
    except Exception as e:
        print("Error creating ms graph client: ", str(e))
        return 

    print("Sending mail through client")
    result_str = await graph_client.send_mail_without_attachment(subject=subject, body=body, recipients=recipients) 
    return result_str

# Send Email with attachment Tool
@mcp.tool(
    name="send_email_with_attachment",
    description="Sends an email with an attachment through the user's email. Body of the email is not needed as it it auto generated based on the attachment"
)
async def send_email_with_attachment(
    attachment_name: str = Field(..., description="The full name of the attachment to be added to the email"),
    subject: str = Field(..., description="The subject of the email"),
    recipients: list[str] = Field(..., description="The main recipients of the email"),
):
    # Get access token from http header
    headers = get_http_headers()
    auth_header = headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return "Missing or invalid Authorization header."
    access_token = auth_header.split(" ", 1)[1]

    # Get Config
    config = configparser.ConfigParser()
    config.read(['config.cfg', 'config.dev.cfg'])
    azure_settings = config['azure']
    
    # Create ServerGraph client
    print("Creating ms graph client")
    try: 
        graph_client = ServerGraph(azure_settings, access_token)
        print("Sucessfully created ms graph client")
        pass
    except Exception as e:
        print("Error creating ms graph client: ", str(e))
        return "Error creating ms graph client"

    result_str = await graph_client.send_mail_with_attachment(subject=subject, recipients=recipients, attachment_name=attachment_name) 
    return result_str

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")
HTML_PATH = os.path.abspath("view.html")

@mcp.tool(
    name="merge_string_with_docx",
    description="Extracts text from the most recent docx in Downloads and prepends it with the output from the news headlines identification tool."
)
async def merge_string_with_docx(
    merge_summary: str = Field(..., description="Summary string from classify_news_by_prompt to prepend."),
    download_dir: Optional[str] = Field(default=DOWNLOADS_DIR, description="Path to Downloads folder.")
) -> str:
    docx_path = find_latest_docx(download_dir)
    convert_docx_to_html_text(docx_path, HTML_PATH)
    copied_text = await render_and_extract_text(HTML_PATH)
    final_output = f"{merge_summary}\n\n{copied_text}"
    return final_output

BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL = "computer-use-preview"
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 768
API_VERSION = "preview"

@mcp.tool(
    name="news_headlines_identification",
    description="Goes to sites provided by the user and extract headlines containing technology-related keywords using Azure OpenAI + Playwright"
)
async def classify_news_by_prompt(
    user_prompt: Annotated[str, Field(..., description="User's prompt to classify news and detect sites/topics.")],
    sites: Annotated[Optional[list[str]], Field(description="Optional list of news sites. Leave blank to auto-detect.")] = None,
    topics: Annotated[Optional[list[str]], Field(description="Optional topic keywords to focus on. Leave blank to auto-detect.")] = None
) -> str:
    """
    Smart news checker MCP tool that opens a browser, screenshots tech news sites, and classifies results using LLM.
    """
    return await check_news_smart(user_prompt=user_prompt, sites=sites, topics=topics)
    
# Run the server
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=5000,
        path="/mcp",
        log_level="debug",
    )
