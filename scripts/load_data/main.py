import os
from helpers import get_csv_from_usitc, process_csv, load_into_db
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

YEAR = 2016

def main():
    df = get_csv_from_usitc(YEAR)
    df = process_csv(df)
    connection_string = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}"
    load_into_db(df, connection_string, year=YEAR)
    

if __name__ == "__main__":
    main()
