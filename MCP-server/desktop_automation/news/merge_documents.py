from pathlib import Path
import os
import glob
import pyperclip
from playwright.async_api import async_playwright
import mammoth

def find_latest_docx(download_dir: str) -> str:
    list_of_files = glob.glob(os.path.join(download_dir, "*.docx"))
    if not list_of_files:
        raise FileNotFoundError("❌ No .docx files found in Downloads.")
    return max(list_of_files, key=os.path.getctime)

def convert_docx_to_html_text(docx_path: str, html_output: str) -> None:
    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file)
        html_content = result.value

    with open(html_output, "w", encoding="utf-8") as f:
        f.write(html_content)

async def render_and_extract_text(html_path: str) -> tuple[str, bytes]:
    uri = Path(html_path).resolve().as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(uri)
        await page.wait_for_timeout(1000)

        await page.keyboard.down("Control")
        await page.keyboard.press("a")
        await page.keyboard.press("c")
        await page.keyboard.up("Control")
        await page.wait_for_timeout(500)

        copied_text = pyperclip.paste()
        await browser.close()
        return copied_text

