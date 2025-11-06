"""
Tool for fetching historical tariff data directly from the tariff_master table
using SQLAlchemy ORM.

This file defines:
1. The SQLAlchemy ORM Model (TariffMaster).
2. The database connection (engine, SessionLocal).
3. The data access logic (get_historical_data).
4. The FastAPI APIRouter that exposes the logic as an endpoint.
"""

import logging
import os
import asyncio
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, String, Integer, Float, Date
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import DeclarativeBase

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SQLAlchemy Database Setup ---
DB_URL = os.getenv("DB_URL")
DB_USERNAME = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

sqlalchemy_engine = None
SessionLocal = None

try:
    if not DB_URL or not DB_USERNAME or not DB_PASSWORD:
        raise ValueError("DB_URL, DB_USER, or DB_PASSWORD is not set in .env")
    
    # Clean up the DB_URL if it's in JDBC format
    if DB_URL.startswith("jdbc:postgresql://"):
        DB_URL = DB_URL.replace("jdbc:postgresql://", "")
        
    connection_string = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_URL}"
    
    sqlalchemy_engine = create_engine(connection_string, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlalchemy_engine)
    logger.info("HistoricalViewerTool: SQLAlchemy engine and SessionLocal created.")
except Exception as e:
    logger.error(f"HistoricalViewerTool: Failed to create SQLAlchemy engine: {e}")

# --- ORM Setup (SQLAlchemy 2.0 style) ---
class Base(DeclarativeBase):
    pass

class TariffMaster(Base):
    """
    SQLAlchemy ORM Model for the 'tariff_master' table in the 'tariffs' schema.
    """
    __tablename__ = 'tariff_master'
    __table_args__ = {'schema': 'tariffs'}

    tariffid = Column(String, primary_key=True)
    description = Column(String)
    descriptionwcountry = Column(String)
    reportercountry = Column(Integer)
    partnercountry = Column(Integer)
    year = Column(Integer)
    hts6code = Column(String)
    advalorem = Column(Float)
    specificperunit = Column(Float)
    category = Column(String)
    unitname = Column(String)
    effectivedate = Column(Date)
    reporteriso = Column(String)
    partneriso = Column(String)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the ORM object to a JSON-serializable dictionary."""
        return {
            "tariffid": self.tariffid,
            "description": self.description,
            "descriptionwcountry": self.descriptionwcountry,
            "reportercountry": self.reportercountry,
            "partnercountry": self.partnercountry,
            "year": self.year,
            "hts6code": self.hts6code,
            "advalorem": self.advalorem,
            "specificperunit": self.specificperunit,
            "category": self.category,
            "unitname": self.unitname,
            "effectivedate": self.effectivedate.strftime('%Y-%m-%d') if self.effectivedate else None,
            "reporteriso": self.reporteriso,
            "partneriso": self.partneriso
        }

# --- Data Access Function ---
def get_historical_data(
    db_session: Session,
    full_tariff_id_prefix: Optional[str] = None,
    hts6: Optional[str] = None,
    reporter_id: Optional[int] = None,
    partner_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetches historical tariff data from the database using an ORM session.
    """
    query = db_session.query(TariffMaster)
    
    if full_tariff_id_prefix:
        # --- Mode 1: Search by Full Tariff ID Prefix (e.g., '170211USAU') ---
        # This will find all entries like '170211USAU2002', '170211USAU2003', etc.
        logger.info(f"Querying by full_tariff_id_prefix: {full_tariff_id_prefix}")
        query = query.filter(TariffMaster.tariffid.like(f"{full_tariff_id_prefix}%"))
        
    elif hts6 and reporter_id is not None and partner_id is not None:
        # --- Mode 2: Search by Parameters (using INT IDs and hts6code) ---
        # This uses the separate columns for a more precise search.
        logger.info(f"Querying by params: hts6={hts6}, reporter_id={reporter_id}, partner_id={partner_id}")
        query = query.filter(
            TariffMaster.hts6code == hts6,
            TariffMaster.reportercountry == reporter_id,
            TariffMaster.partnercountry == partner_id
        )
    
    else:
        # No valid search parameters provided
        logger.warning("No valid search parameters provided for historical data.")
        return []

    # Add ordering and a safety limit
    query = query.order_by(TariffMaster.year.asc(), TariffMaster.effectivedate.asc()).limit(1000)

    try:
        # Execute the query
        results = query.all()
        
        # Convert results to list of dictionaries
        data_points = [row.to_dict() for row in results]
        
        logger.info(f"Found {len(data_points)} data points.")
        return data_points

    except Exception as e:
        logger.error(f"Error executing historical tariff query: {e}")
        # Re-raise the exception so the endpoint can return a 500
        raise

# --- FastAPI Router Definition ---
#
# --- THIS IS THE FIX ---
# Removed `prefix="/api/v1"`
# The gateway strips this prefix, so the server should not expect it.
router = APIRouter()
# --- END OF FIX ---


@router.get("/historical")
async def get_historical_data_endpoint(
    full_tariff_id_prefix: Optional[str] = None,
    hts6: Optional[str] = None,
    reporter_id: Optional[int] = None,
    partner_id: Optional[int] = None
):
    """
    Endpoint to get historical tariff data.
    Accessible via: /historical
    (The gateway maps /api/v1/historical to this)
    
    Supports two search modes:
    1. ?full_tariff_id_prefix=170211USAU
    2. ?hts6=170211&reporter_id=188&partner_id=10
    """
    if SessionLocal is None:
        raise HTTPException(
            status_code=503, 
            detail="Database connection is not configured. Check server logs."
        )

    # Basic parameter validation
    is_mode_a = bool(full_tariff_id_prefix)
    is_mode_b = bool(hts6 and reporter_id is not None and partner_id is not None)

    if not is_mode_a and not is_mode_b:
        raise HTTPException(
            status_code=400, 
            detail="Invalid parameters. Provide either 'full_tariff_id_prefix' OR all of 'hts6', 'reporter_id', and 'partner_id'."
        )
    
    if is_mode_a and is_mode_b:
        raise HTTPException(
            status_code=400, 
            detail="Invalid parameters. Provide EITHER 'full_tariff_id_prefix' OR the other parameters, not both."
        )

    db_session: Session = SessionLocal()
    try:
        # Run the synchronous SQLAlchemy query in a separate thread
        # to avoid blocking the asyncio event loop.
        data_points = await asyncio.to_thread(
            get_historical_data,
            db_session,
            full_tariff_id_prefix=full_tariff_id_prefix,
            hts6=hts6,
            reporter_id=reporter_id,
            partner_id=partner_id
        )
        
        return JSONResponse(content=data_points)

    except Exception as e:
        logger.error(f"Error in /historical endpoint: {e}")
        db_session.rollback() # Rollback on error
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")
    finally:
        db_session.close() # Always close the session