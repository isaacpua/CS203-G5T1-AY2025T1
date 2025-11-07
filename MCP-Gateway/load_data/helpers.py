import requests
import zipfile
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, Column, Text, Float, Date, text
from sqlalchemy.ext.declarative import declarative_base
import re

Base = declarative_base()


class Tariff(Base):
    __tablename__ = 'tariff_htsYYYY'
    __table_args__ = {"extend_existing": True, "schema": "tariffs"}

    # id = Column(Integer, autoincrement=True)
    tariffid = Column(Text, primary_key=True, nullable=False)
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

    # Transform category column based on advalorem and specificperunit values
    def categorize_tariff(row):
        adval = row['advalorem']
        specific = row['specificperunit']

        # Check if values are empty (null) or zero
        adval_empty = pd.isna(adval) or adval == 0
        specific_empty = pd.isna(specific) or specific == 0

        if adval_empty and specific_empty:
            return 'FREE'
        elif not adval_empty and specific_empty:
            return 'AD_VALOREM'
        elif adval_empty and not specific_empty:
            return 'SPECIFIC_PER_UNIT'
        else:  # both present
            return 'COMPOSITE'
    result_df.loc[result_df['category'] == 'AD_VALOREM', 'specificperunit'] = np.nan
    result_df.loc[result_df['category'] == 'SPECIFIC_PER_UNIT', 'advalorem'] = np.nan
    result_df['advalorem'] = result_df['advalorem'].replace(0, np.nan)
    result_df['specificperunit'] = result_df['specificperunit'].replace(0, np.nan)
    result_df['category'] = result_df.apply(categorize_tariff, axis=1)

    # Transform unitname column
    def transform_unitname(unit):
        if pd.isna(unit):
            return unit
        unit_str = str(unit).strip()
        if unit_str == 'KG':
            return 'Kilogram'
        elif unit_str == 'L':
            return 'Litre'
        else:
            return unit

    result_df['unitname'] = result_df['unitname'].apply(transform_unitname)

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
        advalorem = float(pct_match.group(1)) / 100

    # Extract specific rate (dollars or cents per unit)

    # Try dollar format first
    dollar_match = re.search(r'\$\s*([\d.]+)\s*/\s*\w+', rate_str)
    if dollar_match:
        specificperunit = float(dollar_match.group(1))

    # Try cents format (including ¢ symbol)
    cents_match = re.search(r'([\d.]+)\s*(?:cents?|¢)', rate_str)
    if cents_match and not dollar_match:
        specificperunit = float(cents_match.group(1)) / 100

    final_advalorem = advalorem
    if (advalorem is not None):
        final_advalorem = np.round(advalorem, 4)

    final_specificperunit = specificperunit
    if (specificperunit is not None):
        final_specificperunit = np.round(specificperunit, 4)

    return (final_advalorem, final_specificperunit)


COUNTRY_MAP = {
    "SG": 1, "AF": 2, "AL": 3, "DZ": 4, "AD": 5, "AO": 6, "AG": 7, "AR": 8, "AM": 9, "AU": 10,
    "AT": 11, "AZ": 12, "BS": 13, "BH": 14, "BD": 15, "BB": 16, "BY": 17, "BE": 18, "BZ": 19, "BJ": 20,
    "BT": 21, "BO": 22, "BA": 23, "BW": 24, "BR": 25, "BN": 26, "BG": 27, "BF": 28, "BI": 29, "CV": 30,
    "KH": 31, "CM": 32, "CA": 33, "CF": 34, "TD": 35, "CL": 36, "CN": 37, "CO": 38, "KM": 39, "CG": 40,
    "CD": 41, "CR": 42, "HR": 43, "CU": 44, "CY": 45, "CZ": 46, "DK": 47, "DJ": 48, "DM": 49, "DO": 50,
    "EC": 51, "EG": 52, "SV": 53, "GQ": 54, "ER": 55, "EE": 56, "SZ": 57, "ET": 58, "FJ": 59, "FI": 60,
    "FR": 61, "GA": 62, "GM": 63, "GE": 64, "DE": 65, "GH": 66, "GR": 67, "GD": 68, "GT": 69, "GN": 70,
    "GW": 71, "GY": 72, "HT": 73, "VA": 74, "HN": 75, "HU": 76, "IS": 77, "IN": 78, "ID": 79, "IR": 80,
    "IQ": 81, "IE": 82, "IL": 83, "IT": 84, "CI": 85, "JM": 86, "JP": 87, "JO": 88, "KZ": 89, "KE": 90,
    "KI": 91, "KW": 92, "KG": 93, "LA": 94, "LV": 95, "LB": 96, "LS": 97, "LR": 98, "LY": 99, "LI": 100,
    "LT": 101, "LU": 102, "MG": 103, "MW": 104, "MY": 105, "MV": 106, "ML": 107, "MT": 108, "MH": 109, "MR": 110,
    "MU": 111, "MX": 112, "FM": 113, "MD": 114, "MC": 115, "MN": 116, "ME": 117, "MA": 118, "MZ": 119, "MM": 120,
    "NA": 121, "NR": 122, "NP": 123, "NL": 124, "NZ": 125, "NI": 126, "NE": 127, "NG": 128, "KP": 129, "MK": 130,
    "NO": 131, "OM": 132, "PK": 133, "PW": 134, "PS": 135, "PA": 136, "PG": 137, "PY": 138, "PE": 139, "PH": 140,
    "PL": 141, "PT": 142, "QA": 143, "RO": 144, "RU": 145, "RW": 146, "KN": 147, "LC": 148, "VC": 149, "WS": 150,
    "SM": 151, "ST": 152, "SA": 153, "SN": 154, "RS": 155, "SC": 156, "SL": 157, "SK": 158, "SI": 159, "SB": 160,
    "SO": 161, "ZA": 162, "KR": 163, "SS": 164, "ES": 165, "LK": 166, "SD": 167, "SR": 168, "SE": 169, "CH": 170,
    "SY": 171, "TW": 172, "TJ": 173, "TZ": 174, "TH": 175, "TL": 176, "TG": 177, "TO": 178, "TT": 179, "TN": 180,
    "TR": 181, "TM": 182, "TV": 183, "UG": 184, "UA": 185, "AE": 186, "GB": 187, "US": 188, "UY": 189, "UZ": 190,
    "VU": 191, "VE": 192, "VN": 193, "YE": 194, "ZM": 195, "ZW": 196, "AS": 197, "AI": 198, "AQ": 199, "AW": 200,
    "BM": 201, "BQ": 202, "BV": 203, "IO": 204, "KY": 205, "CX": 206, "CC": 207, "CK": 208, "CW": 209, "FK": 210,
    "FO": 211, "GF": 212, "PF": 213, "TF": 214, "GI": 215, "GL": 216, "GP": 217, "GU": 218, "GG": 219, "HM": 220,
    "HK": 221, "IM": 222, "JE": 223, "MO": 224, "MQ": 225, "YT": 226, "MS": 227, "NC": 229, "NU": 230, "NF": 231,
    "MP": 232, "PN": 233, "PR": 234, "RE": 235, "BL": 236, "SH": 237, "MF": 238, "PM": 239, "SX": 240, "GS": 241,
    "SJ": 242, "TK": 243, "TC": 244, "UM": 245, "VG": 246, "VI": 247, "WF": 248, "EH": 249, "AX": 250
}



COUNTRY_SCHEMA = "tariffs"
COUNTRY_TABLE  = "country"
COUNTRY_FQN    = f'{COUNTRY_SCHEMA}."{COUNTRY_TABLE}"'  # -> tariffs."country"

MASTER_SCHEMA = "tariffs"
MASTER_TABLE  = "tariff_master"

MASTER_DDL_FK = f"""
CREATE SCHEMA IF NOT EXISTS {MASTER_SCHEMA};

CREATE TABLE IF NOT EXISTS {MASTER_SCHEMA}.{MASTER_TABLE} (
    tariffid            TEXT PRIMARY KEY,
    descriptionwcountry TEXT,
    unitname            TEXT,
    category            TEXT,
    advalorem           DOUBLE PRECISION,
    specificperunit     DOUBLE PRECISION,
    effectivedate       DATE,
    expirydate          DATE,
    partnercountry      INTEGER REFERENCES {COUNTRY_FQN}(countryid),
    reportercountry     INTEGER REFERENCES {COUNTRY_FQN}(countryid),
    datasource          TEXT,
    year                INTEGER
);
CREATE INDEX IF NOT EXISTS idx_{MASTER_TABLE}_year ON {MASTER_SCHEMA}.{MASTER_TABLE}(year);
"""


def ensure_master_table(engine):
    with engine.begin() as conn:
        conn.execute(text(MASTER_DDL_FK))

CODE_ALIASES = {"AN": "NL", "VG": "GB"}

def to_country_id(series):
    s = series.copy()

    # 1) normalize strings
    is_str = s.map(lambda x: isinstance(x, str))
    s.loc[is_str] = s.loc[is_str].str.strip().str.upper().replace(CODE_ALIASES)

    # 2) try to parse numeric (already IDs)
    numeric = pd.to_numeric(s, errors="coerce")
    already_ids_mask = numeric.notna()
    # keep parsed ints where numeric
    s.loc[already_ids_mask] = numeric.loc[already_ids_mask].astype("Int64")

    # 3) map ISO2 strings → IDs for the rest
    need_map_mask = ~already_ids_mask
    s.loc[need_map_mask] = s.loc[need_map_mask].map(COUNTRY_MAP)

    # final tidy: cast to plain int (or keep Int64 if you prefer nullable)
    return s.astype("Int64")

def load_into_master(input_df, db_connection_string: str, year: int):
    """
    Load into tariffs.tariff_master with integer FKs (ISO2 -> country.id).
    """
    engine = create_engine(db_connection_string)
    ensure_master_table(engine)

    df = input_df.copy()
    df["year"] = int(year)
    # Normalize first
    df["partnercountry"] = df["partnercountry"].astype(str).str.strip().str.upper()
    df["reportercountry"] = df["reportercountry"].astype(str).str.strip().str.upper()
    df["partnercountry"]  = to_country_id(df["partnercountry"])
    df["reportercountry"] = to_country_id(df["reportercountry"])

    missing_partner = df["partnercountry"].isna().sum()
    missing_reporter = df["reportercountry"].isna().sum()
    if missing_partner or missing_reporter:
        print(f"[helpers] WARNING: {missing_partner} partnercountry and {missing_reporter} reportercountry values did not map.")

    staging_table = f"_stg_tariff_{year}"

    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {MASTER_SCHEMA}.{staging_table};"))
        conn.execute(text(f"CREATE TABLE {MASTER_SCHEMA}.{staging_table} (LIKE {MASTER_SCHEMA}.{MASTER_TABLE} INCLUDING ALL);"))

    df.to_sql(
        name=staging_table,
        con=engine,
        schema=MASTER_SCHEMA,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    upsert_sql = f"""
    INSERT INTO {MASTER_SCHEMA}.{MASTER_TABLE} (
        tariffid, descriptionwcountry, unitname, category, advalorem, specificperunit,
        effectivedate, expirydate, partnercountry, reportercountry, datasource, year
    )
    SELECT
        tariffid, descriptionwcountry, unitname, category, advalorem, specificperunit,
        effectivedate, expirydate, partnercountry, reportercountry, datasource, year
    FROM {MASTER_SCHEMA}.{staging_table}
    ON CONFLICT (tariffid) DO UPDATE SET
        descriptionwcountry = EXCLUDED.descriptionwcountry,
        unitname            = EXCLUDED.unitname,
        category            = EXCLUDED.category,
        advalorem           = EXCLUDED.advalorem,
        specificperunit     = EXCLUDED.specificperunit,
        effectivedate       = EXCLUDED.effectivedate,
        expirydate          = EXCLUDED.expirydate,
        partnercountry      = EXCLUDED.partnercountry,
        reportercountry     = EXCLUDED.reportercountry,
        datasource          = EXCLUDED.datasource,
        year                = EXCLUDED.year;
    """

    with engine.begin() as conn:
        conn.execute(text(upsert_sql))
        conn.execute(text(f"DROP TABLE IF EXISTS {MASTER_SCHEMA}.{staging_table};"))

    print(f"[helpers] Upserted {len(df)} rows into {MASTER_SCHEMA}.{MASTER_TABLE} (FK-mapped).")
