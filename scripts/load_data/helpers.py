import requests
import zipfile
import tempfile
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, Column, Text, Float, Date, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Tariff(Base):
    __tablename__ = 'tariff_htsYYYY'
    __table_args__ = {"extend_existing": True, "schema": "tariffs"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tariffid = Column(Text, nullable=False)
    descriptionwcountry = Column(Text)
    unitname = Column(Text)
    category = Column(Text)
    advalorem = Column(Float)
    specificperunit = Column(Float)
    col1_special_text = Column(Text)
    effectivedate = Column(Date)
    expirydate = Column(Date)
    partnercountry = Column(Text)
    reportercountry = Column(Text)
    datasource = Column(Text)


def get_csv_from_usitc(year: int) -> pd.DataFrame:
    """
    Download and extract tariff data from USITC for a specific year.
    """
    # Construct download URL
    url = f"https://www.usitc.gov/tariff_affairs/documents/tariff_data/tariff_data_{year}.zip"
    
    extract_path = Path(tempfile.mkdtemp())
    
    zip_path = extract_path / f"tariff_data_{year}.zip"
    
    print(f"Downloading tariff data for {year} from USITC...")
    
    # Download the zip file
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Save zip file
    with open(zip_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Downloaded {zip_path.name} ({zip_path.stat().st_size / 1024 / 1024:.2f} MB)")
    
    # Extract the zip file
    print("Extracting zip file...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    # Remove the zip file to save space
    zip_path.unlink()
    
    # Find the xlsx file (usually named something like tariff_data_YYYY.xlsx)
    xlsx_files = list(extract_path.glob("*.xlsx"))
    
    if not xlsx_files:
        raise FileNotFoundError(f"No .xlsx file found in the extracted zip for year {year}")
    
    # Load the xlsx file into DataFrame
    xlsx_file_path = xlsx_files[0]
    print(f"Loading {xlsx_file_path.name} into DataFrame...")
    
    df = pd.read_excel(xlsx_file_path)
    
    # Clean up: remove the xlsx file and temp directory
    xlsx_file_path.unlink()
    
    # Remove any other files that might have been extracted
    for file in extract_path.iterdir():
        if file.is_file():
            file.unlink()
    
    # Remove the temporary directory
    extract_path.rmdir()
    
    print(f"Successfully loaded {len(df)} rows and cleaned up temporary files.")
    
    return df


def process_csv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the csv from USITC
    TODO:
        1. Add logic for figuring out the different partner countries
        2. Morph tariffid into the desired UEN <first6hts><from><to><year>
    """
    columns_to_keep = {
        'hts8': 'tariffid',
        'brief_description': 'descriptionwcountry',
        'quantity_1_code': 'unitname',
        'mfn_text_rate': 'category',
        'mfn_ad_val_rate': 'advalorem',
        'mfn_specific_rate': 'specificperunit',
        'col1_special_text': 'col1_special_text',
        'begin_effect_date': 'effectivedate',
        'end_effective_date': 'expirydate'
    }
    # keep only selected columns and rename them
    df = df[list(columns_to_keep.keys())].rename(columns=columns_to_keep)
    
    # Remove rows where both advalorem AND specificperunit are empty/null
    df = df[~(df['advalorem'].isna() & df['specificperunit'].isna())]
    
    df['effectivedate'] = pd.to_datetime(df['effectivedate'], errors='coerce').dt.strftime('%Y-%m-%d')
    df['expirydate'] = pd.to_datetime(df['expirydate'], errors='coerce').dt.strftime('%Y-%m-%d')
    # default values
    df['partnercountry'] = ''
    df['reportercountry'] = 'US'
    df['datasource'] = 'USITC'
    
    print("Successfully processed the USITC csv.")
    # df.to_csv("output.csv")
    return df


def load_into_db(input_df: pd.DataFrame, db_connection_string: str, year: int):
    """
    Loads the dataframe into the AWS RDS Postgres DB
    """
    
    table_name = f'tariff_hts{year}'
    schema = 'tariffs'
    
    old_table_name = 'tariffs.tariff_htsYYYY'
    if old_table_name in Base.metadata.tables:
        Base.metadata.remove(Base.metadata.tables[old_table_name])
    
    Tariff.__tablename__ = table_name
    Tariff.__table_args__ = {"extend_existing": True, "schema": schema}
    
    # Clear the cached table
    Tariff.__table__ = None
    
    engine = create_engine(db_connection_string)
    
    # Define explicit dtype mapping for pandas
    dtype_mapping = {
        'tariffid': Text,
        'descriptionwcountry': Text,
        'unitname': Text,
        'category': Text,
        'advalorem': Float,
        'specificperunit': Float,
        'col1_special_text': Text,
        'effectivedate': Date,
        'expirydate': Date,
        'partnercountry': Text,
        'reportercountry': Text,
        'datasource': Text
    }
    
    # Convert DataFrame to SQL with explicit dtypes
    input_df.to_sql(
        name=table_name,
        con=engine,
        schema=schema,
        if_exists='replace',
        index=False,
        dtype=dtype_mapping,
        method='multi',
        chunksize=1000
    )
    
    print(f"Successfully loaded {len(input_df)} rows into table '{schema}.{table_name}'.")
