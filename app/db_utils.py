# app/db_utils.py
import streamlit as st
import logging
import pandas as pd
import sqlalchemy
import datetime
from sqlalchemy import create_engine, select, func, distinct, text, and_, or_, true, false, update
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import os
from typing import List, Optional, Tuple, Dict, Any, Union
from app.models import Base, Station, HourlyCount

logger = logging.getLogger(__name__)

def get_engine():
    """
    Creates and returns a SQLAlchemy engine.
    Reads configuration from Streamlit secrets.
    Returns None if configuration is missing or connection fails.
    """
    try:
        if "environment" in st.secrets and "DATABASE_URL" in st.secrets["environment"]:
            db_url = st.secrets["environment"]["DATABASE_URL"]
            engine = create_engine(db_url, pool_pre_ping=True)
            logger.debug("Database engine created successfully")
            return engine
        else:
            logger.error("DATABASE_URL not found in st.secrets['environment']")
            st.error("Database configuration (DATABASE_URL) is missing in secrets.")
            return None
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy Error creating engine: {e}", exc_info=True)
        st.error(f"Database connection failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}", exc_info=True)
        st.error("An unexpected error occurred during database setup.")
        return None

def create_session_factory(db_engine):
    """Creates a session factory for the given engine."""
    if db_engine is None:
        logger.error("Cannot create session factory without a valid engine.")
        return None
    try:
        SessionFactory = sessionmaker(bind=db_engine)
        return SessionFactory
    except Exception as e:
        logger.error(f"Failed to create session factory: {e}", exc_info=True)
        return None

# Initializes and returns the engine and session factory with stale connection handling
def init_db_resources() -> Tuple[Optional[Any], Optional[Any]]:
    """Initializes and returns the engine and session factory."""
    logger.debug("Initializing database resources")
    engine = get_engine()
    session_factory = create_session_factory(engine)
    # Short-circuit on failure
    if engine is None or session_factory is None:
        logger.error("Failed to initialize one or more DB resources.")
        return None, None
    # Check for stale connection and retry once
    try:
        with engine.connect():
            pass
    except Exception as e:
        logger.warning(f"Stale DB connection detected: {e}")
        # Reinitialize resources
        engine = get_engine()
        session_factory = create_session_factory(engine)
        if engine is None or session_factory is None:
            logger.error("Failed to initialize one or more DB resources after retry.")
            return None, None
    return engine, session_factory

def get_db_session():
    """Gets a new database session using the initialized SessionFactory."""
    engine, session_factory = init_db_resources()
    if session_factory:
        try:
            return session_factory()
        except Exception as e:
            logger.error(f"Failed to create database session: {e}", exc_info=True)
            st.error("Could not create database session.")
            return None
    else:
        logger.error("Session Factory not available, cannot create session.")
        return None

def get_all_station_metadata(_session: Optional[Session]) -> Optional[pd.DataFrame]:
    """Fetches all station metadata from the database."""
    if _session is None:
        logger.error("Database session is None in get_all_station_metadata.")
        return None
    try:
        query = _session.query(Station)
        if _session.bind is None:
            logger.error("Session bind is None in get_all_station_metadata.")
            st.error("Database connection is not available.")
            return pd.DataFrame()
        df = pd.read_sql(query.statement, _session.bind)
        logger.debug(f"Retrieved {len(df)} station metadata records")
        return df
    except Exception as e:
        logger.error(f"Error fetching station metadata: {e}", exc_info=True)
        st.error("Failed to load station metadata from database.")
        return None

def get_station_details(_session, station_key: int):
    """Fetches details for a specific station."""
    if _session is None:
        logger.error("Database session is None in get_station_details.")
        return None
    try:
        station = _session.query(Station).filter(Station.station_key == station_key).first()
        if station:
            logger.debug(f"Retrieved details for station_key: {station_key}")
            return station
        else:
            logger.warning(f"Station with key {station_key} not found.")
            return None
    except Exception as e:
        logger.error(f"Error fetching details for station {station_key}: {e}", exc_info=True)
        st.error("Failed to load station details from database.")
        return None

def get_latest_data_date(_session, station_key: int, direction: int):
    """Fetches the latest data timestamp for a given station and direction."""
    if _session is None:
        logger.error("Database session is None in get_latest_data_date.")
        return None
    try:
        latest_date = _session.query(func.max(HourlyCount.count_date))\
                              .filter(HourlyCount.station_key == station_key)\
                              .filter(HourlyCount.traffic_direction_seq == direction)\
                              .scalar()
        logger.debug(f"Latest data date for station {station_key}, direction {direction}: {latest_date}")
        return latest_date
    except Exception as e:
        logger.error(f"Error fetching latest data date for station {station_key}, direction {direction}: {e}", exc_info=True)
        st.error("Failed to load latest data date from database.")
        return None

def get_hourly_data_for_stations(
    _session: Optional[Session],
    station_keys: list,
    start_date,
    end_date,
    directions: Optional[List[Any]] = None,
    required_cols: Optional[List[Any]] = None
) -> Optional[pd.DataFrame]:
    """Fetches hourly count data for a list of stations and date range."""
    if _session is None:
        logger.error("Database session is None in get_hourly_data_for_stations.")
        return None
    try:
        # Build query with individual filter calls for proper chaining
        query = _session.query(HourlyCount)
        query = query.filter(HourlyCount.station_key.in_(station_keys))
        query = query.filter(HourlyCount.count_date >= start_date)
        query = query.filter(HourlyCount.count_date <= end_date)
        if directions and 3 not in directions:
            query = query.filter(HourlyCount.traffic_direction_seq.in_(directions))

        if _session.bind is None:
            logger.error("Session bind is None in get_hourly_data_for_stations.")
            st.error("Database connection is not available.")
            return pd.DataFrame()
        # Ensure statement is a string for pd.read_sql
        df = pd.read_sql(str(query.statement), _session.bind)
        logger.debug(f"Retrieved {len(df)} hourly records")
        return df
    except Exception as e:
        logger.error(f"Error fetching hourly data: {e}", exc_info=True)
        st.error("Failed to load hourly count data from database.")
        return pd.DataFrame()

def get_distinct_values(_session, column_name: str, table=Station):
    """
    Fetches distinct values from a specified column in a table.
    Includes validation to ensure the column exists on the table.
    """
    if _session is None:
        logger.error("Database session is None in get_distinct_values.")
        return None

    # alias 'direction_key' to HourlyCount.traffic_direction_seq and support HourlyCount table
    if column_name == 'direction_key':
        column = HourlyCount.traffic_direction_seq
    elif hasattr(table, column_name):
        column = getattr(table, column_name)
    elif hasattr(HourlyCount, column_name):
        column = getattr(HourlyCount, column_name)
    else:
        logger.error(f"Invalid column name '{column_name}' requested for distinct values.")
        return None

    try:
        query = select(distinct(column)).order_by(column)
        results = _session.execute(query).scalars().all()
        logger.debug(f"Retrieved {len(results)} distinct values for column '{column_name}'")
        return list(results)
    except Exception as e:
        logger.error(f"Error fetching distinct values for {column_name}: {e}", exc_info=True)
        st.error("Failed to load distinct values from database.")
        return None

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_db_session()
    if session is None:
        yield None
        return

    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Session rollback due to error: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        if session:
            session.close()
            logger.debug("Database session closed.")

def update_station_geometries():
    """Update PostGIS geometries for all stations."""
    with session_scope() as session:
        if not session:
            logger.error("Database session not available for updating geometries.")
            st.error("Database session not available for updating geometries.")
            return
        # raw SQL to satisfy test expectations
        sql = text(
            "UPDATE stations SET location_geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) "
            "WHERE location_geom IS NULL"
        )
        try:
            logger.info("Updating station geometries...")
            session.execute(sql)
            logger.info("Station geometries updated successfully.")
        except Exception as e:
            logger.error(f"Error updating station geometries: {e}", exc_info=True)
            st.error("Failed to update station geometries in database.")