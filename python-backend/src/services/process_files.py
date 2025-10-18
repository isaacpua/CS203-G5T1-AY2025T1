from PyPDF2 import PdfReader
import io
import pandas as pd
import json
import geopandas as gpd
from fastapi import UploadFile
from tempfile import SpooledTemporaryFile

def process_files(fileObject: UploadFile) -> str:
    extension = fileObject.filename.lower().split(".")[-1]
    text = ""

    try:
        if extension == "pdf":
            text = extract_text_from_pdf(fileObject.file)
        elif extension == "csv":
            text = extract_text_from_csv(fileObject.file)
        elif extension == "geojson":
            text = extract_text_from_geojson(fileObject.file)
        else:
            text = f"(Unsupported file type: {extension})"
    except Exception as e:
        text = f"(Error processing {fileObject.filename}: {str(e)})"
    
    return f"File: {fileObject.filename}, Content: {text}"

def extract_text_from_pdf(file: SpooledTemporaryFile) -> str:
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    
    return text.strip()

def extract_text_from_csv(file: SpooledTemporaryFile) -> str:
    df = pd.read_csv(file)
    return df.to_string(index=False)

def extract_text_from_geojson(file: SpooledTemporaryFile) -> str:
    geo_df = gpd.read_file(file).to_json()
    geo_dict = json.loads(geo_df)
    return json.dumps(geo_dict, indent=2)
