import requests
import zipfile
import tempfile
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, Column, Text, Float, Date, Integer
from sqlalchemy.ext.declarative import declarative_base
import re

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
    
    # Read Excel with proper encoding handling
    df = pd.read_excel(xlsx_file_path, engine='openpyxl')
    
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


def clean_text_encoding(text):
    """
    Clean up common encoding issues in text fields.
    """
    # if pd.isna(text) or not isinstance(text, str):
    #     return text
    
    # # Common encoding issues and their fixes
    # replacements = {
    #     'Ã‚Â¢': '¢',
    #     'Ã¢': '¢',
    #     'â€¢': '•',
    #     'â€"': '–',
    #     'â€™': "'",
    #     'Â': '',  # Remove stray Â characters
    # }
    
    # for bad, good in replacements.items():
    #     text = text.replace(bad, good)
    
    return text


def process_csv(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Processes the csv from USITC and expands rows by partner country.
    Each tariff line is duplicated for each partner country with appropriate rates.
    """
    original_num_rows = len(df)
    # All possible partner country codes (expand as needed)
    ALL_COUNTRIES = {
        'A', 'A+', 'A*', 'AU', 'B', 'BH', 'CA', 'CL', 'CO', 'D', 'E', 'IL', 
        'J', 'JO', 'JB', 'KR', 'MA', 'MX', 'OM', 'P', 'P+', 'PA', 'PE', 'R', 
        'SG', 'ET'
    }
    
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
    
    # Keep only selected columns and rename them
    df = df[list(columns_to_keep.keys())].rename(columns=columns_to_keep)
    
    # Clean encoding issues in text columns
    text_columns = ['descriptionwcountry', 'unitname', 'category', 'col1_special_text']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(clean_text_encoding)
    
    # Remove rows where both advalorem AND specificperunit are empty/null
    df = df[~(df['advalorem'].isna() & df['specificperunit'].isna())]
    
    # Filter by first 6 digits of HTS - keep only first occurrence
    df['hts6'] = df['tariffid'].astype(str).str[:6]
    visited_hts6 = set()
    rows_to_keep = []
    
    for idx, row in df.iterrows():
        hts6 = row['hts6']
        if hts6 not in visited_hts6:
            visited_hts6.add(hts6)
            rows_to_keep.append(idx)
    
    df = df.loc[rows_to_keep].copy()
    print(f"Filtered to {len(df)} unique HTS6 codes from {original_num_rows} total codes.")
    
    # Convert dates
    df['effectivedate'] = pd.to_datetime(df['effectivedate'], errors='coerce').dt.strftime('%Y-%m-%d')
    df['expirydate'] = pd.to_datetime(df['expirydate'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Default values
    df['reportercountry'] = 'US'
    df['datasource'] = 'USITC'
    
    # Process each row to extract partner countries
    expanded_rows = []
    
    for _, row in df.iterrows():
        col1_text = str(row['col1_special_text']) if pd.notna(row['col1_special_text']) else ''
        hts6 = row['hts6']
        
        # Extract special rate countries and their rates
        special_countries = {}
        
        # Pattern to match rate followed by countries in parentheses
        pattern = r'([^()]+?)\s*\(([A-Z+*,\s]+)\)(?!\s*\()'
        matches = re.findall(pattern, col1_text)
        
        for rate, countries_str in matches:
            rate = rate.strip()
            
            # Skip patterns that look like references
            if rate.lower().startswith('see ') or 'heading' in rate.lower() or 'note' in rate.lower():
                continue
            
            # Split countries by comma and clean whitespace
            countries = [c.strip() for c in countries_str.split(',') if c.strip()]
            
            # Filter to only valid country codes
            countries = [c for c in countries if c in ALL_COUNTRIES]
            
            for country in countries:
                special_countries[country] = rate
        
        # If no special countries were found, create rows for all countries (except reporter) with MFN rate
        if not special_countries:
            for country in ALL_COUNTRIES:
                # Skip if country is the reporter country
                if country == row['reportercountry']:
                    continue
                    
                new_row = row.copy()
                new_row['partnercountry'] = country
                # Create tariffid: <hts6><reporter><partner><year>
                new_row['tariffid'] = f"{hts6}{new_row['reportercountry']}{country}{year}"
                expanded_rows.append(new_row)
        else:
            # Create rows for countries with special rates
            for country, special_rate in special_countries.items():
                new_row = row.copy()
                new_row['partnercountry'] = country
                new_row['category'] = special_rate
                
                # Parse special rate for advalorem/specificperunit
                adval, specific = parse_rate(special_rate)
                new_row['advalorem'] = adval if adval is not None else row['advalorem']
                new_row['specificperunit'] = specific if specific is not None else row['specificperunit']
                
                # Create tariffid: <hts6><reporter><partner><year>
                new_row['tariffid'] = f"{hts6}{new_row['reportercountry']}{country}{year}"
                
                expanded_rows.append(new_row)
            
            # Create rows for countries WITHOUT special rates (using MFN rate)
            countries_with_special = set(special_countries.keys())
            mfn_countries = ALL_COUNTRIES - countries_with_special
            
            for country in mfn_countries:
                new_row = row.copy()
                new_row['partnercountry'] = country
                # Create tariffid: <hts6><reporter><partner><year>
                new_row['tariffid'] = f"{hts6}{new_row['reportercountry']}{country}{year}"
                expanded_rows.append(new_row)
    
    # Create new dataframe from expanded rows
    result_df = pd.DataFrame(expanded_rows)
    
    # Drop the temporary hts6 column
    result_df = result_df.drop(columns=['hts6'])
    
    print(f"Successfully processed the USITC csv. Expanded from {len(df)} to {len(result_df)} rows.")
    result_df.to_csv("output.csv")
    return result_df


def parse_rate(rate_str: str) -> tuple:
    """
    Parse a rate string to extract ad valorem and specific components.
    Returns (advalorem, specificperunit) as floats or None.
    
    Examples:
        "Free" -> (0.0, 0.0)
        "$1.00/kg" -> (None, 1.00)
        "4.6%" -> (4.6, None)
        "$1.01/kg + 4.6%" -> (4.6, 1.01)
        "11.7 cents/liter + 7.4%" -> (7.4, 11.7)
    """
    rate_str = rate_str.strip().lower()
    
    # Handle "Free"
    if rate_str == 'free':
        return (0.0, 0.0)
    
    advalorem = None
    specificperunit = None
    
    # Extract percentage (ad valorem) rate
    pct_match = re.search(r'([\d.]+)\s*%', rate_str)
    if pct_match:
        advalorem = float(pct_match.group(1))
    
    # Extract specific rate (dollars or cents per unit)
    
    # Try dollar format first
    dollar_match = re.search(r'\$\s*([\d.]+)\s*/\s*\w+', rate_str)
    if dollar_match:
        specificperunit = float(dollar_match.group(1))
    
    # Try cents format (including ¢ symbol)
    cents_match = re.search(r'([\d.]+)\s*(?:cents?|¢)', rate_str)
    if cents_match and not dollar_match:
        specificperunit = float(cents_match.group(1)) / 100
    
    return (advalorem, specificperunit)


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
