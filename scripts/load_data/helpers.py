import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, Date, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Tariff(Base):
    __tablename__ = 'tariffs_htsYYYY'
    __table_args__ = {"extend_existing": True, "schema": "tariffs"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tariffid = Column(String(255), nullable=False)
    descriptionwcountry = Column(String(255))
    unitname = Column(String(255))
    category = Column(String(255))
    advalorem = Column(Float)
    specificperunit = Column(Float)
    col1_special_text = Column(String(255))
    effectivedate = Column(Date)
    expirydate = Column(Date)
    partnercountry = Column(String(255))
    reportercountry = Column(String(255))
    datasource = Column(String(255))


def get_csv_from_usitc():
    """
    Get the "csv" from the USITC. It is actually just a txt.
    
    Link to view all: https://dataweb.usitc.gov/tariff/annual
    
    TODO:
        1. Download the zip
        2. Unzip
        3. Load the txt file
    """
    raise NotImplementedError


def process_csv(input_filepath: str) -> pd.DataFrame:
    """
    Processes the csv from USITC
    TODO:
        1. Add logic for figuring out the different partner countries
        2. Morph tariffid into the desired UEN <first6hts><from><to><year>
    """
    df = pd.read_csv(input_filepath)
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
    return df


def load_into_db(input_df: pd.DataFrame, db_connection_string: str, year: int):
    """
    Loads the dataframe into the AWS RDS Postgres DB
    """
    
    table_name = f'tariffs_hts{year}'
    schema = 'tariffs'
    
    old_table_name = 'tariffs.tariffs_htsYYYY'
    if old_table_name in Base.metadata.tables:
        Base.metadata.remove(Base.metadata.tables[old_table_name])
    
    Tariff.__tablename__ = table_name
    Tariff.__table_args__ = {"extend_existing": True, "schema": schema}
    
    # Clear the cached table
    Tariff.__table__ = None
    
    engine = create_engine(db_connection_string)
    
    # Define explicit dtype mapping for pandas
    dtype_mapping = {
        'tariffid': String(255),
        'descriptionwcountry': String(255),
        'unitname': String(255),
        'category': String(255),
        'advalorem': Float,
        'specificperunit': Float,
        'col1_special_text': String(255),
        'effectivedate': Date,
        'expirydate': Date,
        'partnercountry': String(255),
        'reportercountry': String(255),
        'datasource': String(255)
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
