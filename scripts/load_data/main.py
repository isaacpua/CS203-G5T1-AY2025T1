import os
from helpers import get_csv_from_usitc, process_csv, load_into_master
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.getenv("DB_URL")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# YEAR = 2025

def main():
    for YEAR in range(2002, 2026):
        df = get_csv_from_usitc(YEAR)
        df = process_csv(df, YEAR)
        connection_string = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}"
        load_into_master(df, connection_string, year=YEAR)
    

if __name__ == "__main__":
    main()
