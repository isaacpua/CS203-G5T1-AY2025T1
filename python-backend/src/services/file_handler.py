import pandas as pd
import pdfplumber
import re
from collections import defaultdict
from fastapi import UploadFile
from typing import Union
import io

def summarize_text(text: str, max_sentences: int = 5) -> str:
    """
    Summarize the given text by extracting the first few sentences.

    Args:
        text (str): The text to summarize.
        max_sentences (int): Maximum number of sentences to include in the summary.

    Returns:
        str: Summarized text.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    return " ".join(sentences[:max_sentences])

def load_data(upload_file: UploadFile):
    filename = upload_file.filename.lower()
    file_obj = upload_file.file  # Safe: UploadFile exposes a file-like object

    if filename.endswith(".csv"):
        print("[DEBUG] Reading CSV file.")
        return pd.read_csv(file_obj)

    elif filename.endswith((".tsv", ".txt")):
        print("[DEBUG] Reading TSV file.")
        return pd.read_csv(file_obj, sep="\t")

    elif filename.endswith((".xlsx", ".xls")):
        print("[DEBUG] Reading Excel file.")
        file_bytes = file_obj.read()  # read once
        return pd.read_excel(io.BytesIO(file_bytes))

    elif filename.endswith(".pdf"):
        print("[DEBUG] Reading PDF file.")
        full_text = []

        with pdfplumber.open(file_obj) as pdf:
            print(f"[DEBUG] PDF has {len(pdf.pages)} page(s).")
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    print(f"[DEBUG] Extracted text from page {page_num}.")
                    full_text.append(text)

        if not full_text:
            raise ValueError("No text content found in PDF.")

        # Combine all text and summarize
        combined_text = " ".join(full_text)
        summarized_text = summarize_text(combined_text)

        print(f"[DEBUG] Summarized text:\n{summarized_text}")
        return {"summary": summarized_text, "full_text": combined_text}

    else:
        raise ValueError("Unsupported file format.")