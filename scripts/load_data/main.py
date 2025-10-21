import os
from helpers import process_csv, load_into_db
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def main():
    df = process_csv("input/trade_tariff_database_202307.txt")
    connection_string = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}"
    load_into_db(df, connection_string, year=2023)
    

if __name__ == "__main__":
    main()
