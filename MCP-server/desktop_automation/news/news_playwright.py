import os
import asyncio
import base64
from openai import AzureOpenAI
from playwright.async_api import TimeoutError, async_playwright
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage

MODEL = "computer-use-preview"
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 768
API_VERSION = "preview"

last_successful_screenshot = None

def validate_coordinates(x, y):
    """
    Clamp coordinates within display bounds.
    """
    return max(0, min(x, DISPLAY_WIDTH)), max(0, min(y, DISPLAY_HEIGHT))

async def take_screenshot(page):
    """
    Capture and return base64 screenshot, fallback to last successful.
    """
    global last_successful_screenshot
    try:
        screenshot_bytes = await page.screenshot(full_page=False)
        last_successful_screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
        print("📸 Screenshot captured successfully")
        return last_successful_screenshot
    except Exception as e:
        print(f"❌ Screenshot failed: {str(e)}")
        if last_successful_screenshot:
            print("🔄 Using last successful screenshot")
        else:
            print("⚠️ No previous screenshot available")
        return last_successful_screenshot or None

async def extract_sites_and_topics(prompt: str, llm: AzureChatOpenAI) -> tuple[list[str], list[str]]:

    if prompt == "classify news by prompt" or prompt == "news headlines identification":
        print("Skipping extraction for 'classify news by prompt' or 'computer use'")
        return [], []
    
    print(prompt)
    
    extract_instruction = (
        "You will be given a prompt from a user who wants to summarize technology news.\n"
        "Extract two things:\n"
        "1. A list of websites to check (if mentioned)\n"
        "2. A list of topic keywords to focus on (if mentioned)\n"
        "If a site is mentioned, identify the URL of the site.\n"
        "If either is not specified, return an empty list.\n\n"
        f"Prompt: {prompt}\n\n"
        "Return result as Python dict: {\"sites\": [...], \"topics\": [...]} — do NOT include extra text or markdown."
    )
    response = await llm.ainvoke([HumanMessage(content=extract_instruction)])
    try:
        extracted = eval(response.content.strip())
        sites = extracted.get("sites", [])
        topics = extracted.get("topics", [])
        print("I AM HEREEE")
        # Step 2: Resolve site names to URLs (if needed)
        unresolved_sites = [s for s in sites if not s.startswith("http")]
        if unresolved_sites:
            resolve_prompt = (
                "Convert the following list of news site names into full URLs (homepages). "
                "Return a Python list of strings. If unsure, give your best guess. No explanations.\n\n"
                f"{unresolved_sites}"
            )
            resolved_response = await llm.ainvoke([HumanMessage(content=resolve_prompt)])
            try:
                resolved_urls = eval(resolved_response.content.strip())
                # Replace unresolved names with resolved URLs
                for name, url in zip(unresolved_sites, resolved_urls):
                    sites[sites.index(name)] = url
            except Exception as e:
                print("⚠️ Failed to resolve some site names:", e)

        print("SITESSS", sites)
        print("TOPICSSS", topics)
        return sites, topics
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return [], []

async def check_news_smart(user_prompt: str, sites: list[str] = None, topics: list[str] = None) -> str:
    """
    Full workflow: Extract intent → open sites → take screenshots → summarize → classify by keyword → return HTML.
    """
    BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT")
    API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    GPT4O_API_BASE = os.getenv("GPT4O_API_BASE")
    GPT4O_API_KEY = os.getenv("GPT4O_API_KEY")
    GPT4O_API_VERSION = os.getenv("GPT4O_API_VERSION")
    GPT4O_DEPLOYMENT_NAME = os.getenv("GPT4O_DEPLOYMENT_NAME")

    client = AzureOpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        api_version=API_VERSION
    )

    llm = AzureChatOpenAI(
        azure_deployment=GPT4O_DEPLOYMENT_NAME,
        openai_api_version=GPT4O_API_VERSION,
        api_key=GPT4O_API_KEY,
        azure_endpoint=GPT4O_API_BASE,
    )

    extracted_sites, extracted_topics = await extract_sites_and_topics(user_prompt, llm)
    print("Extracted sites:", extracted_sites)
    print("Extracted topics:", extracted_topics)
    sites = extracted_sites
    topics = extracted_topics

    if not sites:
        sites = [
            "https://www.bbc.com/news/technology",
            "https://www.cnn.com/business/tech",
            "https://techcrunch.com/",
            "https://www.theverge.com/tech"
        ]

    all_findings = []
    successful_check = False

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": DISPLAY_WIDTH, "height": DISPLAY_HEIGHT})
        page = await context.new_page()

        print("sites here areee", sites)
        for i, site in enumerate(sites, 1):
            print("the i is ", i, "the site is ", site)
            print(f"\n{'='*60}")
            print(f"🔍 Checking site {i}/{len(sites)}: {site}")
            print(f"{'='*60}")

            try:
                await page.goto(site, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(3)

                screenshot_base64 = await take_screenshot(page)
                if not screenshot_base64:
                    print(f"❌ Failed to capture screenshot for {site}")
                    continue

                if topics:
                    topic_filter = f"focusing on the following topic(s): {', '.join(topics)}"
                    visible_instruction = f"Identify headlines related to or loosely connected with: {', '.join(topics)}."
                else:
                    topic_filter = "focusing on the most important breaking news"
                    visible_instruction = "Identify the most important and prominent headlines."

                prompt = f"""
                    You are a news summarization assistant. You will be shown a screenshot of a news website.

                    Only analyze the visible content — do not click or scroll. Your task is to:

                    1. Identify up to 3 headlines visible in the screenshot {topic_filter}. 
                    2. Write a 2–3 sentence summary for each headline. The headline should be relevant to {topic_filter}. 

                    Include the source site name: {site}
                    Respond in this format:
                    <ul>
                      <li>{site}<br /><strong>[Headline]</strong><br />[Summary]<br/><a href='{site}' target='_blank'>Read more</a><br /></li>
                    </ul>
                """

                instructions = (
                    "You are a news summarization assistant. Your job is to analyze a screenshot of a news website. "
                    f"{visible_instruction} Only report what's visible. Do not make assumptions. Be factual and concise. Return output in HTML list format"
                )

                response = client.responses.create(
                    model=MODEL,
                    tools=[{
                        "type": "computer_use_preview",
                        "display_width": DISPLAY_WIDTH,
                        "display_height": DISPLAY_HEIGHT,
                        "environment": "browser"
                    }],
                    instructions=instructions,
                    input=[{
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "image_url": f"data:image/png;base64,{screenshot_base64}"}
                        ]
                    }],
                    tool_choice="auto",
                    truncation="auto"
                )
                
                print("Tool response", response)
                if response.output and response.output[0].content:
                    html_content = response.output[0].content[0].text
                    site_findings = html_content.strip()
                    successful_check = True
                else:
                    site_findings = "No tool output"

                if site_findings != "No tool output":
                    successful_check = True

                all_findings.append(site_findings)


                if site_findings:
                    all_findings.append(f"<h2>{site}</h2>\n{site_findings}")
                else:
                    all_findings.append(f"<h2>{site}</h2>\nNo tool output")

            except TimeoutError:
                print(f"⏰ Timeout while loading {site}")
                continue
            except Exception as e:
                print(f"❌ Error checking {site}: {str(e)}")
                all_findings.append(f"<h2>{site}</h2>\n<p>Error: {str(e)}</p>")

            await asyncio.sleep(2)

        await browser.close()

    print(all_findings)
    print("FINAL STEPSSS")

    if not successful_check:
        return "<html><body><p>Unable to complete news check. Please try again later.</p></body></html>"

    classification_prompt = (
        f"Here are the headlines and summaries collected.\n"
        f"Group each article under the tech-related keyword(s) it relates to **without repeating the original lines**.\n"
        "Return as HTML like this (omit <html><body>):\n"
        "Here are the headlines identified:<br /><strong>Keyword</strong><ul><li>Site<br />Headline<br />Summary<br/><a href='URL'>Read more</a></li></ul>\n\n"
        + "\n\n".join(all_findings)
    )
    result = await llm.ainvoke([HumanMessage(content=classification_prompt)])
    return f"<html><body>{result.content.strip()}</body></html>"
