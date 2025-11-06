import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# client will read OPENAI_API_KEY from env if not passed explicitly
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def analyze(input: str) -> dict:
    """
    The tool for analyzing tariff articles. Send the provided string of an 
    article related to tariffs to OpenAI and return a concise analysis.

    Args:
        input: A string of the article to analyze
        
    Returns:
        Dict with the success state, and error message or response markdown text for
        the analysis of the article.
    """

    
    response = {
        "success": None,
        "error": None,
        "markdown": None
    }

    if not input:
        response["success"] = False
        response["error"] = "Input markdown cannot be empty"


    prompt = (
        "Please analyze the article below"
        "Input:\n\n"
        f"{input}\n\n"
    )

    instruction = (
        "You are an AI tariff article analyzer.\n"
        "Your task is to read news articles or policy documents and extract all relevant information about tariffs, duties, and trade restrictions.\n"
        "Focus only on tariff-related changes (e.g., increases, decreases, introductions, removals, exemptions).\n\n"
        "For each article, provide a structured summary with these sections:\n\n"
        "1. **Summary Overview** - A concise summary (2-3 sentences) describing what the article is about.\n"
        "2. **Tariff Changes Detected** - A bullet list of detected changes. Each item should include:\n"
        "   * **Product of Sector** affected\n"
        "   * **Change Type** (Increase, Decrease, New Tariff, Removal, Exemption)\n"
        "   * **New Rate or Change Description** (if available)\n"
        "   * **Country or Region Involved**\n"
        "3. **Effective Dates or Timelines** - Any mentioned dates for when the tariffs take effect\n"
        "4. **Sources or References** - Extracted URLs, organization names, or government bodies mentioned.\n"
        "5. **Confidence Notes** (optional) - If the data is ambiguous, mention what part is uncertain and why.\n\n"
        "Your tone should be **professional, factual, and neutral**, suitable for analysts or policymakers.\n"
        "Do **not** include unrelated economic or political commentary unless directly linked to tariff effects.\n"
        "If the article contains **no tariff-related content**, output:\n"
        "“No tariff-related information found.”\n"
    )


    print("Asking gpt to summarize article!")
    try:
        resp = client.responses.create(
            model="gpt-4o",
            input=prompt,
            instructions=instruction,
            max_output_tokens=1024,
            temperature=0.1,
        )

        if resp.error:
            print(f"Error: {resp.error}")
            raise Exception(f"{resp.error}")


        print("gpt call success!")
        # print(resp.output[0].content[0].text)
        markdown = resp.output[0].content[0].text

        response["success"] = True
        response["markdown"] = markdown
        
        return response
    
    except Exception as e:
        print(e)
        response["success"] = False
        response["error"] = e
        return response
