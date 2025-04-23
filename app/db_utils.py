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
from typing import List, Optional, Tuple, Dict, Any
from app.models import Base, Station, HourlyCount

logger = logging.getLogger(__name__)

def get_engine():
    """
    Creates and returns a SQLAlchemy engine.
    Reads configuration from Streamlit secrets.
    Returns None if configuration is missing or connection fails.
    """
    engine = None
    try:
        if "environment" in st.secrets and "DATABASE_URL" in st.secrets["environment"]:
            db_url = st.secrets["environment"]["DATABASE_URL"]
            logger.info("Attempting to create database engine using URL from st.secrets...")
            engine = create_engine(db_url, pool_pre_ping=True)
            logger.info("Database engine created successfully.")
        else:
            logger.error("DATABASE_URL not found in st.secrets['environment']")
            st.error("Database configuration (DATABASE_URL) is missing in secrets.")

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy Error creating engine: {e}", exc_info=True)
        st.error(f"Database connection failed: {e}")
        engine = None
    except Exception as e:
        logger.error(f"Unexpected error during database engine initialization: {e}", exc_info=True)
        st.error("An unexpected error occurred during database setup.")
        engine = None

    return engine

def create_session_factory(db_engine):
    """Creates a session factory for the given engine."""
    if db_engine is None:
        logger.error("Cannot create session factory without a valid engine.")
        return None
    try:
        logger.info("Attempting to create Session Factory...")
        SessionFactory = sessionmaker(bind=db_engine)
        logger.info("Session Factory created successfully.")
        return SessionFactory
    except Exception as e:
        logger.error(f"Failed to create session factory: {e}", exc_info=True)
        return None

@st.cache_resource
def init_db_resources():
    """Initializes and returns the engine and session factory."""
    logger.info("Initializing DB resources (engine and session factory)...")
    engine = get_engine()
    session_factory = create_session_factory(engine)
    if engine is None or session_factory is None:
        logger.error("Failed to initialize one or more DB resources.")
        return None, None
    logger.info("DB resources initialized successfully.")
    return engine, session_factory

def get_db_session():
    """Gets a new database session using the initialized SessionFactory."""
    engine, session_factory = init_db_resources()
    if session_factory:
        try:
            session = session_factory()
            logger.debug("Database session created.")
            return session
        except Exception as e:
            logger.error(f"Failed to create database session: {e}", exc_info=True)
            st.error("Could not create database session.")
            return None
    else:
        logger.error("Session Factory not available, cannot create session.")
        return None

@st.cache_data
def get_all_station_metadata(_session):
    """Fetches all station metadata from the database."""
    if _session is None:
        logger.error("Database session is None in get_all_station_metadata.")
        return None
    try:
        logger.info("Querying all station metadata.")
        # Use the correct model name: Station
        query = _session.query(Station)
        df = pd.read_sql(query.statement, _session.bind)
        logger.info(f"Successfully fetched {len(df)} station metadata records.")
        return df
    except Exception as e:
        logger.error(f"Error fetching all station metadata: {e}", exc_info=True)
        st.error("Failed to load station metadata from database.")
        return None

@st.cache_data
def get_station_details(_session, station_key: int):
    """Fetches details for a specific station."""
    if _session is None:
        logger.error("Database session is None in get_station_details.")
        return None
    try:
        logger.info(f"Querying details for station_key: {station_key}")
        # Use the correct model name: Station
        station = _session.query(Station).filter(Station.station_key == station_key).first()
        if station:
            logger.info(f"Successfully fetched details for station_key: {station_key}")
            return station
        else:
            logger.warning(f"No station found with key: {station_key}")
            return None
    except Exception as e:
        logger.error(f"Error fetching station details for key {station_key}: {e}", exc_info=True)
        st.error(f"Failed to load details for station {station_key}.")
        return None

@st.cache_data
def get_latest_data_date(_session, station_key: int, direction: int):
    """Fetches the latest data timestamp for a given station and direction."""
    if _session is None:
        logger.error("Database session is None in get_latest_data_date.")
        return None
    try:
        logger.info(f"Querying latest data date for station {station_key}, direction {direction}")
        # Use the correct model name: HourlyCount
        latest_date = _session.query(func.max(HourlyCount.count_date))\
                              .filter(HourlyCount.station_key == station_key,
                                      # Assuming 'traffic_direction_seq' is the correct column for direction
                                      HourlyCount.traffic_direction_seq == direction)\
                              .scalar()
        logger.info(f"Latest data date found: {latest_date}")
        return latest_date
    except Exception as e:
        logger.error(f"Error fetching latest data date for station {station_key}: {e}", exc_info=True)
        st.error("Failed to determine latest data date.")
        return None

@st.cache_data
def get_hourly_data_for_stations(_session, station_keys: list, start_date, end_date, directions: list = None, required_cols: list = None):
    """Fetches hourly count data for a list of stations and date range."""
    if _session is None:
        logger.error("Database session is None in get_hourly_data_for_stations.")
        return None
    try:
        logger.info(f"Querying hourly data for stations {station_keys} from {start_date} to {end_date}")
        # Use the correct model name: HourlyCount
        query = _session.query(HourlyCount).filter(
            HourlyCount.station_key.in_(station_keys),
            HourlyCount.count_date >= start_date,
            HourlyCount.count_date <= end_date
        )
        if directions and 3 not in directions: # Assuming 3 means 'Both'
             # Use the correct column name for direction, likely 'traffic_direction_seq'
             query = query.filter(HourlyCount.traffic_direction_seq.in_(directions))

        df = pd.read_sql(query.statement, _session.bind)
        logger.info(f"Successfully fetched {len(df)} hourly records.")
        # Add column selection logic if needed based on required_cols
        return df
    except Exception as e:
        logger.error(f"Error fetching hourly data: {e}", exc_info=True)
        st.error("Failed to load hourly traffic data.")
        return pd.DataFrame() # Return empty DataFrame on error

@st.cache_data
def get_distinct_values(_session, column_name: str, table=Station):
    """
    Fetches distinct values from a specified column in a table.
    Includes validation to ensure the column exists on the table.
    """
    if _session is None:
        logger.error("Database session is None in get_distinct_values.")
        return None

    # --- Start of Added Validation ---
    if not hasattr(table, column_name):
        logger.error(f"Invalid column name '{column_name}' provided for table '{table.__tablename__}'.")
        st.error(f"Invalid column specified: {column_name}")
        return None
    # --- End of Added Validation ---

    try:
        logger.info(f"Querying distinct values for column '{column_name}' in table '{table.__tablename__}'.")
        column = getattr(table, column_name)
        query = select(distinct(column)).order_by(column)
        results = _session.execute(query).scalars().all()
        logger.info(f"Found {len(results)} distinct values for column '{column_name}'.")
        return list(results)
    except Exception as e:
        logger.error(f"Error fetching distinct values for column '{column_name}': {e}", exc_info=True)
        st.error(f"Failed to load distinct values for column '{column_name}'.")
        return None

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = get_db_session()
    if session is None:
        # Handle case where session creation failed (already logged in get_db_session)
        yield None
        return # Exit the generator

    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Session rollback due to error: {e}", exc_info=True)
        session.rollback()
        raise # Re-raise the exception after rollback
    finally:
        if session:
            session.close()
            logger.debug("Database session closed.")

def update_station_geometries():
    """Update PostGIS geometries for all stations."""
    with session_scope() as session:
        if not session:
            st.error("Database session not available for updating geometries.")
            return

        stmt = update(Station).values(
            location_geom=func.ST_SetSRID(
                func.ST_MakePoint(
                    Station.wgs84_longitude,
                    Station.wgs84_latitude
                ),
                4326
            )
        ).where(Station.location_geom.is_(None))

        session.execute(stmt)