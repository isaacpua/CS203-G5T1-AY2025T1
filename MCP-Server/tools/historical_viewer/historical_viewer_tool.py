# In: MCP-Server/tools/historical_viewer/historical_viewer_tool.py

import os
import logging
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import create_engine, text
from typing import Optional
from datetime import date

# --- Configuration ---
logger = logging.getLogger(__name__)

# 1. Read Database Credentials from .env
# (This is loaded by your main.py/mcp_server.py)
DB_URL = os.getenv("DB_URL")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Check if credentials are loaded
if not (DB_URL and DB_USERNAME and DB_PASSWORD):
    logger.error("Database credentials (DB_URL, DB_USERNAME, DB_PASSWORD) not found in .env file.")
    # We don't raise an error here, but the engine will fail to create
    engine = None
else:
    try:
        connection_string = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}'
        engine = create_engine(connection_string)
        logger.info("SQLAlchemy engine created successfully for historical viewer.")
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy engine: {e}")
        engine = None

# This is the router your main.py will import
router = APIRouter(
    prefix="/tools/historical_viewer",
    tags=["Historical Tariff Viewer"] 
)

# --- API Endpoint ---

@router.get("/data")
async def get_historical_tariff_data(
    # --- UPDATED: We now use integer IDs to match the database ---
    reporter_country: int = Query(..., description="Numeric ID for the reporter country (e.g., 188 for USA)."),
    partner_country: int = Query(..., description="Numeric ID for the partner country (e.g., 33 for Canada)."),
    category: Optional[str] = Query(None, description="e.g., 'AD_VALOREM' or 'FREE'"),
    start_date: Optional[date] = Query(None, description="Format: YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="Format: YYYY-MM-DD")
):
    """
    Fetches historical tariff data directly from the tariff_master database.
    """
    if engine is None:
        raise HTTPException(
            status_code=503, 
            detail="Database connection is not configured. Check server logs."
        )

    # 2. Build the SQL Query
    # We use parameterized queries (e.g., :reporter) to prevent SQL injection
    query_params = {
        "reporter": reporter_country,
        "partner": partner_country
    }
    
    # Select the columns you want to plot
    # Your `tariff_master` table has `advalorem` and `specificperunit`
    sql_query = """
        SELECT 
            effectivedate, 
            advalorem, 
            specificperunit,
            category,
            unitname
        FROM tariffs.tariff_master
        WHERE 
            reportercountry = :reporter AND 
            partnercountry = :partner
    """
    
    # 3. Add Optional Filters
    if category:
        sql_query += " AND category = :category"
        query_params["category"] = category
    if start_date:
        sql_query += " AND effectivedate >= :start_date"
        query_params["start_date"] = start_date
    if end_date:
        sql_query += " AND effectivedate <= :end_date"
        query_params["end_date"] = end_date
    
    sql_query += " ORDER BY effectivedate ASC;"

    # 4. Execute the Query
    try:
        with engine.connect() as conn:
            # Use pandas to read the SQL query directly into a DataFrame
            # This is the same method used in your forecast.py
            df = pd.read_sql(text(sql_query), conn, params=query_params)
        
        # Convert DataFrame to the JSON format FastAPI expects
        # (a list of dictionaries, one for each row)
        return df.to_dict('records')

    except Exception as e:
        logger.error(f"Error executing tariff query: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")