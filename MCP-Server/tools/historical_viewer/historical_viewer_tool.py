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
DB_URL = os.getenv("DB_URL")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not (DB_URL and DB_USERNAME and DB_PASSWORD):
    logger.error("Database credentials (DB_URL, DB_USERNAME, DB_PASSWORD) not found in .env file.")
    engine = None
else:
    try:
        connection_string = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}'
        engine = create_engine(connection_string)
        logger.info("SQLAlchemy engine created successfully for historical viewer.")
    except Exception as e:
        logger.error(f"Failed to create SQLAlchemy engine: {e}")
        engine = None

router = APIRouter(
    prefix="/tools/historical_viewer",
    tags=["Historical Tariff Viewer"] 
)

# --- API Endpoint ---

@router.get("/data")
async def get_historical_tariff_data(
    # --- NEW: Search by full ID ---
    full_tariff_id: Optional[str] = Query(None, description="A single, complete tariffid."),
    
    # --- UPDATED: Search by parameters ---
    reporter_country: Optional[int] = Query(None, description="Numeric ID for the reporter country (e.g., 188 for USA)."),
    partner_country: Optional[int] = Query(None, description="Numeric ID for the partner country (e.g., 33 for Canada)."),
    hts6: Optional[str] = Query(None, description="First 6 digits of the HTS code (e.g., '170211')"),

    # --- Optional Filters ---
    category: Optional[str] = Query(None, description="e.g., 'AD_VALOREM' or 'FREE'"),
    start_date: Optional[date] = Query(None, description="Format: YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="Format: YYYY-MM-DD")
):
    """
    Fetches historical tariff data directly from the tariff_master database
    using either a full tariff ID or a combination of parameters.
    """
    if engine is None:
        raise HTTPException(
            status_code=503, 
            detail="Database connection is not configured. Check server logs."
        )

    query_params = {}
    sql_query = """
        SELECT 
            tariffid,
            effectivedate, 
            advalorem, 
            specificperunit,
            category,
            unitname
        FROM tariffs.tariff_master
    """
    
    where_clauses = []

    if full_tariff_id:
        # --- Mode 1: Search by Full Tariff ID ---
        where_clauses.append("tariffid = :full_tariff_id")
        query_params["full_tariff_id"] = full_tariff_id
        
    else:
        # --- Mode 2: Search by Parameters ---
        if reporter_country:
            where_clauses.append("reportercountry = :reporter")
            query_params["reporter"] = reporter_country
        if partner_country:
            where_clauses.append("partnercountry = :partner")
            query_params["partner"] = partner_country
        if hts6:
            # Use LIKE to match the first 6 digits of the tariffid
            # This assumes tariffid format is like '123456...'
            where_clauses.append("tariffid LIKE :hts6_pattern")
            query_params["hts6_pattern"] = f"{hts6}%"
        
        # Add optional filters
        if category:
            where_clauses.append("category = :category")
            query_params["category"] = category
        if start_date:
            where_clauses.append("effectivedate >= :start_date")
            query_params["start_date"] = start_date
        if end_date:
            where_clauses.append("effectivedate <= :end_date")
            query_params["end_date"] = end_date

    if not where_clauses:
        raise HTTPException(status_code=400, detail="You must provide either a full_tariff_id or a set of search parameters.")

    sql_query += " WHERE " + " AND ".join(where_clauses)
    sql_query += " ORDER BY effectivedate ASC LIMIT 1000;" # Add a limit

    # --- Execute Query ---
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql_query), conn, params=query_params)
        
        # Re-format dates for JSON
        df['effectivedate'] = pd.to_datetime(df['effectivedate']).dt.strftime('%Y-%m-%d')
        return df.to_dict('records')

    except Exception as e:
        logger.error(f"Error executing tariff query: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")