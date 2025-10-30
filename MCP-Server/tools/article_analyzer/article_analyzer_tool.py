import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# client will read OPENAI_API_KEY from env if not passed explicitly
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def analyze(md: str) -> dict:
    """
    The tool for analyzing tariff articles. Send the provided markdown string of an 
    article related to tariffs to OpenAI and return a concise analysis.

    Args:
        md: A string of the markdown of the article to analyze
        
    Returns:
        Dict with the success state, and error message or response markdown text for
        the analysis of the article.
    """

    
    response = {
        "success": None,
        "error": None,
        "markdown": None
    }

    if not md:
        response["success"] = False
        response["error"] = "Input markdown cannot be empty"


    prompt = (
        "You are an assistant that analyzes and summarizes articles on tariffs supplied as Markdown.\n\n"
        "Please produce:\n"
        "1) A short concise summary (2-4 sentences) of the tariff article.\n"
        "2) A bullet list of 5 key points or takeaways from the article regarding tariffs.\n"
        "Input Markdown:\n\n"
        f"{md}\n\n"
        "Return the output as plain text. Do not include extraneous commentary."
    )

    print("Asking gpt to summarize md!")
    try:
        resp = client.responses.create(
            model="gpt-4o",
            input=prompt,
            max_output_tokens=512,
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
