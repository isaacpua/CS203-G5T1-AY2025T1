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


# Country mappings for special program codes
PROGRAM_COUNTRIES = {
    # GSP - Generalized System of Preferences (A, A+, A*)
    'A': {'AR', 'BD', 'BO', 'BR', 'BW', 'KH', 'CM', 'CV', 'TD', 'CO', 'KM', 'CG', 'CD',
          'CR', 'CI', 'DJ', 'DO', 'EC', 'EG', 'GQ', 'ER', 'ET', 'FJ', 'GA', 'GM', 'GE',
          'GH', 'GD', 'GT', 'GN', 'GW', 'GY', 'HT', 'HN', 'IN', 'ID', 'IQ', 'JM', 'JO',
          'KZ', 'KE', 'KI', 'KG', 'LB', 'LS', 'MW', 'ML', 'MR', 'MU', 'MD', 'MN', 'MZ',
          'NA', 'NP', 'NE', 'NG', 'OM', 'PK', 'PA', 'PG', 'PY', 'PH', 'RO', 'RU', 'RW',
          'WS', 'ST', 'SN', 'RS', 'SC', 'SL', 'SB', 'SO', 'ZA', 'LK', 'SR', 'SZ', 'TZ',
          'TH', 'TG', 'TO', 'TT', 'TN', 'TR', 'TV', 'UG', 'UY', 'UZ', 'VU', 'VE', 'YE',
          'ZM', 'ZW'},

    # GSP Least Developed (A+)
    'A+': {'AF', 'AO', 'BD', 'BJ', 'BT', 'BF', 'BI', 'KH', 'CV', 'CF', 'TD', 'KM', 'CD',
           'DJ', 'GQ', 'ER', 'ET', 'GM', 'GN', 'GW', 'HT', 'KI', 'LS', 'MW', 'ML', 'MR',
           'MZ', 'NP', 'NE', 'RW', 'WS', 'ST', 'SL', 'SB', 'SO', 'TZ', 'TG', 'TV', 'UG',
           'VU', 'YE', 'ZM'},

    # FTA Countries
    'AU': {'AU'},  # Australia
    'CA': {'CA'},  # Canada (NAFTA)
    'MX': {'MX'},  # Mexico (NAFTA)
    'CL': {'CL'},  # Chile
    'IL': {'IL'},  # Israel
    'JO': {'JO'},  # Jordan
    'MA': {'MA'},  # Morocco
    'SG': {'SG'},  # Singapore

    # African Growth and Opportunity Act (D)
    'D': {'AO', 'BJ', 'BW', 'BF', 'BI', 'CM', 'CV', 'CF', 'TD', 'KM', 'CG', 'CD', 'CI',
          'DJ', 'GQ', 'ER', 'ET', 'GA', 'GM', 'GH', 'GN', 'GW', 'KE', 'LS', 'LR', 'MG',
          'MW', 'ML', 'MR', 'MU', 'MZ', 'NA', 'NE', 'NG', 'RW', 'ST', 'SN', 'SC', 'SL',
          'SO', 'ZA', 'TZ', 'TG', 'UG', 'ZM'},

    # Caribbean Basin Economic Recovery Act (E, E*)
    'E': {'AG', 'AW', 'BS', 'BB', 'BZ', 'CR', 'DM', 'DO', 'GD', 'GT', 'GY', 'HT', 'HN',
          'JM', 'MS', 'AN', 'NI', 'PA', 'KN', 'LC', 'VC', 'TT', 'VG'},

    # Andean Trade Preference Act (J, J+)
    'J': {'BO', 'CO', 'EC', 'PE'},

    # CAFTA-DR (P, P+)
    'P': {'CR', 'DO', 'SV', 'GT', 'HN', 'NI'},

    # Caribbean Basin Trade Partnership Act (R)
    'R': {'AG', 'AW', 'BS', 'BB', 'BZ', 'DM', 'GD', 'GY', 'JM', 'MS', 'AN', 'KN', 'LC',
          'VC', 'TT', 'VG'},

    # Automotive Products Trade Act (B) - Canada only
    'B': {'CA'},
}

PRODUCT_CODES = ['2011005', '2011050', '2012002', '2012030', '2012050', '2013002', '2013030',
                 '2013050', '2022002', '2031210', '2031920', '2041000', '2042100', '2071100',
                 '2071300', '2072540', '2072600', '2074100', '2074300', '2074400', '2075100',
                 '2075400', '2076010', '2076030', '2076040', '2089030', '2091000', '2099000',
                 '10011100', '10019100', '10031000', '10059020', '10061000', '10063010', '10082100',
                 '10084000', '15071000', '15081000', '15099020', '15121100', '15122100', '15141100',
                 '15151100', '15152100', '15155000', '15156005', '15161000', '15162010', '15171000',
                 '16043100',
                 '17021100', '17022022', '18050000', '19019010', '20011000', '20019010', '20021000',
                 '20031001', '20041040', '20055120', '20055900', '20056000', '20057002', '20058000',
                 '20082000', '20084000', '20085020', '20086000', '20087010', '20088000', '20089100',
                 '20089300', '20089905', '21022020', '22021000']


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

    print(
        f"Downloaded {zip_path.name} ({zip_path.stat().st_size / 1024 / 1024:.2f} MB)")

    # Extract the zip file
    print("Extracting zip file...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # Remove the zip file to save space
    zip_path.unlink()

    # Find the xlsx file (usually named something like tariff_data_YYYY.xlsx)
    xlsx_files = list(extract_path.glob("*.xlsx"))

    if not xlsx_files:
        raise FileNotFoundError(
            f"No .xlsx file found in the extracted zip for year {year}")

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

    print(
        f"Successfully loaded {len(df)} rows and cleaned up temporary files.")

    return df


def clean_text_encoding(text):
    """
    Clean up common encoding issues in text fields.
    """
    if pd.isna(text) or not isinstance(text, str):
        return text

    # Common encoding issues and their fixes
    replacements = {
        'Ã‚Â¢': '¢',
        'Ã¢': '¢',
        'â€¢': '•',
        'â€"': '–',
        'â€™': "'",
        'Â': '',  # Remove stray Â characters
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    return text


def process_csv(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Processes the csv from USITC and expands rows by partner country.
    Each tariff line is duplicated for each partner country with appropriate rates.

    Parameters:
    -----------
    df : pd.DataFrame
        Raw dataframe from USITC
    year : int
        Year for tariff data (used in tariffid generation)
    specific_product_codes : list, optional
        List of specific HTS codes to filter for (e.g., ['2011005', '2011050', ...])
        If provided, only these product codes will be processed

    Returns:
    --------
    pd.DataFrame
        Processed dataframe with partner countries expanded
    """
    # Get all unique countries from all programs
    ALL_COUNTRIES = set()
    for countries in PROGRAM_COUNTRIES.values():
        ALL_COUNTRIES.update(countries)

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

    # FILTER BY SPECIFIC PRODUCT CODES
    # Convert product codes to strings and normalize (remove any whitespace)
    specific_codes = set(str(code).strip() for code in PRODUCT_CODES)

    # Filter dataframe to only include rows where tariffid starts with one of the specific codes
    # We'll match on the first 7 digits of the HTS code
    df['tariffid_str'] = df['tariffid'].astype(str).str.replace('.', '')
    df = df[df['tariffid_str'].isin(specific_codes)].copy()
    df = df.drop(columns=['tariffid_str'])

    print(f"Filtered to specific product codes: {len(df)} products found")

    if len(df) == 0:
        print("WARNING: No products found matching the specified product codes!")
        return pd.DataFrame()

    # Clean encoding issues in text columns
    text_columns = ['descriptionwcountry',
                    'unitname', 'category', 'col1_special_text']
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
    # df.to_csv("intermediate.csv")

    # Convert dates
    df['effectivedate'] = pd.to_datetime(
        df['effectivedate'], errors='coerce').dt.strftime('%Y-%m-%d')
    df['expirydate'] = pd.to_datetime(
        df['expirydate'], errors='coerce').dt.strftime('%Y-%m-%d')

    # Default values
    df['reportercountry'] = 'US'
    df['datasource'] = 'USITC'

    # Process each row to extract partner countries
    expanded_rows = []

    for _, row in df.iterrows():
        col1_text = str(row['col1_special_text']) if pd.notna(
            row['col1_special_text']) else ''
        hts6 = row['hts6']

        # Extract special rate countries and their rates
        special_countries = {}

        # Pattern to match rate followed by countries/programs in parentheses
        pattern = r'([^()]+?)\s*\(([A-Z+*,\s]+)\)(?!\s*\()'
        matches = re.findall(pattern, col1_text)

        for rate, codes_str in matches:
            rate = rate.strip()

            # Skip patterns that look like references
            if rate.lower().startswith('see ') or 'heading' in rate.lower() or 'note' in rate.lower():
                continue

            # Split codes by comma and clean whitespace
            codes = [c.strip() for c in codes_str.split(',') if c.strip()]

            # Expand program codes to actual countries
            expanded_countries = set()
            for code in codes:
                if code in PROGRAM_COUNTRIES:
                    # It's a program code - expand to all countries in that program
                    expanded_countries.update(PROGRAM_COUNTRIES[code])
                elif code in ALL_COUNTRIES:
                    # It's an individual country code
                    expanded_countries.add(code)

            # Assign this rate to all expanded countries
            for country in expanded_countries:
                special_countries[country] = rate

        # If no special countries were found, create rows for all countries with MFN rate
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
                # Skip if country is the reporter country
                if country == row['reportercountry']:
                    continue

                new_row = row.copy()
                new_row['partnercountry'] = country
                # Create tariffid: <hts6><reporter><partner><year>
                new_row['tariffid'] = f"{hts6}{new_row['reportercountry']}{country}{year}"
                expanded_rows.append(new_row)

    # Create new dataframe from expanded rows
    result_df = pd.DataFrame(expanded_rows)

    result_df = result_df.drop(columns=['hts6', 'col1_special_text'])

    print(
        f"Successfully processed the USITC csv. Expanded from {len(df)} to {len(result_df)} rows.")
    # result_df.to_csv(f"output_{year}.csv")
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

    print(
        f"Successfully loaded {len(input_df)} rows into table '{schema}.{table_name}'.")
