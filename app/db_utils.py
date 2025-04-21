# app/db_utils.py
import streamlit as st
import logging
import pandas as pd
import sqlalchemy
import datetime
from sqlalchemy import create_engine, select, func, distinct, text, and_, or_, true, false, update
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from typing import List, Optional, Tuple, Dict, Any
from app.models import Base, Station, HourlyCount

logger = logging.getLogger(__name__)

# --- NEW HELPER FUNCTION ---
def _get_database_url() -> Optional[str]:
    """Gets the database URL, trying Streamlit secrets first, then environment variables."""
    db_url = None
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets'):
            db_url = st.secrets.get("environment", {}).get("DATABASE_URL")
            if db_url:
                logger.debug("Database URL retrieved from Streamlit secrets.")
                return db_url
    except Exception as e: # Catch potential errors during secrets access
        logger.warning(f"Could not retrieve DATABASE_URL from Streamlit secrets ({type(e).__name__}). Falling back to environment variable.")

    # Fallback to environment variable
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        logger.debug("Database URL retrieved from environment variable.")
        return db_url

    logger.error("DATABASE_URL not found in Streamlit secrets or environment variable.")
    return None
# --- END HELPER FUNCTION ---

@st.cache_resource
def get_engine():
    """Creates and returns a SQLAlchemy engine, caching the result."""
    try:
        # --- MODIFIED: Use helper function ---
        db_url = _get_database_url()
        # --- END MODIFICATION ---

        if not db_url:
            # Error logged in _get_database_url
            st.error("Database configuration error: DATABASE_URL not found.")
            return None

        logger.info("Attempting to create database engine...")
        engine = create_engine(db_url)

        try:
            with engine.connect() as connection:
                logger.info("Database engine created and connection tested successfully.")
            return engine
        except Exception as conn_err:
            logger.error(f"Failed to connect using the engine: {conn_err}", exc_info=True)
            st.error(f"Database connection failed: {conn_err}")
            return None

    except Exception as e:
        logger.error(f"An unexpected error occurred during engine creation: {e}", exc_info=True)
        st.error(f"An unexpected error occurred during database setup: {e}")
        return None

engine = get_engine()

@st.cache_resource
def get_session_factory(_engine):
    """Creates and returns a session factory, caching the result."""
    if _engine is None:
        logger.error("Cannot create session factory because the engine is None.")
        return None
    logger.info("Creating session factory...")
    try:
        factory = sessionmaker(bind=_engine)
        logger.info("Session factory created successfully.")
        return factory
    except Exception as e:
        logger.error(f"Failed to create session factory: {e}", exc_info=True)
        st.error(f"Failed to create database session factory: {e}")
        return None

SessionFactory = get_session_factory(engine)

# --- FIX: Ensure rollback on exception in get_db_session ---
@contextmanager
def get_db_session() -> Session:
    """Provides a transactional scope around a series of operations."""
    engine = get_engine()
    if engine is None:
        logger.error("Cannot get DB session: Engine is None.")
        raise ConnectionError("Database engine is not available.") # Raise specific error

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    session_id = id(session) # Get session ID for logging
    logger.debug(f"DB Session {session_id} opened.")
    try:
        yield session
        session.commit() # Commit if yield succeeds
        logger.debug(f"DB Session {session_id} committed successfully.")
    except Exception as e:
        logger.error(f"DB Session {session_id} failed: {e}", exc_info=True)
        session.rollback() # Rollback on any exception during yield
        logger.debug(f"DB Session {session_id} rolled back due to exception.")
        raise # Re-raise the exception after rollback
    finally:
        session.close()
        logger.debug(f"DB Session {session_id} closed.")
# --- END FIX ---

# --- Query Functions ---
# Use @st.cache_data for functions that return data based on inputs

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_all_station_metadata() -> pd.DataFrame:
    """Fetches essential metadata for all stations."""
    with get_db_session() as session:
        if not session: return pd.DataFrame()
        stmt = select(
            Station.station_key,
            Station.station_id,
            Station.name,
            Station.road_name,
            Station.lga,
            Station.suburb,
            Station.wgs84_latitude,
            Station.wgs84_longitude,
            Station.road_functional_hierarchy,
            Station.vehicle_classifier,
            Station.permanent_station,
            Station.quality_rating,
            Station.device_type
        ).order_by(Station.lga, Station.suburb, Station.road_name)
        try:
            df = pd.read_sql(stmt, session.bind)
            return df
        except Exception as e:
            st.error(f"Error fetching all station metadata: {e}")
            return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_station_details(station_key: int) -> Optional[Dict[str, Any]]:
    """Fetches a single station's full details by station_key as a dictionary."""
    logger.debug(f"Fetching details for station_key: {station_key}")
    with get_db_session() as session:
        if not session:
            logger.error("get_station_details: No DB session available.")
            return None
        try:
            stmt = select(Station).where(Station.station_key == station_key)
            station = session.execute(stmt).scalar_one_or_none()

            if station:
                logger.debug(f"Found station: {station.station_id}")
                # Convert ORM object to dict *within the session*
                station_dict = {c.name: getattr(station, c.name) for c in station.__table__.columns}
                logger.debug(f"Converted station {station.station_id} to dict.")
                return station_dict
            else:
                logger.warning(f"No station found for station_key: {station_key}")
                return None
        except Exception as e:
            logger.error(f"Error fetching or converting station details for key {station_key}: {e}", exc_info=True)
            return None

@st.cache_data(ttl=3600)
def get_distinct_values(column_name: str, table_model=Station) -> List[str]:
    """Fetches distinct non-null values for a given column in a table."""
    with get_db_session() as session:
        if not session: return []
        try:
            column = getattr(table_model, column_name)
            stmt = select(distinct(column)).where(column.isnot(None)).order_by(column)
            results = session.scalars(stmt).all()
            return list(results)
        except AttributeError:
            st.error(f"Column '{column_name}' not found in model '{table_model.__name__}'.")
            return []
        except Exception as e:
            st.error(f"Error fetching distinct values for {column_name}: {e}")
            return []

@st.cache_data(ttl=3600)
def get_suburbs_for_lgas(lgas: List[str]) -> List[str]:
    """Fetches distinct suburbs for a given list of LGAs."""
    with get_db_session() as session:
        if not session or not lgas: return []
        try:
            stmt = select(distinct(Station.suburb)).where(
                Station.lga.in_(lgas),
                Station.suburb.isnot(None)
            ).order_by(Station.suburb)
            results = session.scalars(stmt).all()
            return list(results)
        except Exception as e:
            st.error(f"Error fetching suburbs for LGAs {lgas}: {e}")
            return []

@st.cache_data(ttl=3600)
def get_filtered_station_keys(
    lgas: Optional[List[str]] = None,
    suburbs: Optional[List[str]] = None,
    road_names: Optional[List[str]] = None,
    hierarchies: Optional[List[str]] = None,
    is_classifier: Optional[bool] = None,
    is_permanent: Optional[bool] = None,
    min_quality: Optional[int] = None,
) -> List[int]:
    """Fetches station_keys based on multiple optional filters."""
    with get_db_session() as session:
        if not session: return []
        try:
            stmt = select(Station.station_key)
            if lgas:
                stmt = stmt.where(Station.lga.in_(lgas))
            if suburbs:
                stmt = stmt.where(Station.suburb.in_(suburbs))
            if road_names:
                stmt = stmt.where(or_(
                    Station.road_name.in_(road_names),
                    Station.common_road_name.in_(road_names)
                ))
            if hierarchies:
                stmt = stmt.where(Station.road_functional_hierarchy.in_(hierarchies))
            if is_classifier is not None:
                stmt = stmt.where(Station.vehicle_classifier == true() if is_classifier else Station.vehicle_classifier == false())
            if is_permanent is not None:
                stmt = stmt.where(Station.permanent_station == true() if is_permanent else Station.permanent_station == false())
            if min_quality is not None:
                stmt = stmt.where(Station.quality_rating >= min_quality)

            results = session.scalars(stmt).all()
            return list(results)
        except Exception as e:
            st.error(f"Error fetching filtered station keys: {e}")
            return []

@st.cache_data(ttl=900) # Cache data for 15 minutes
def get_hourly_data_for_stations(
    station_keys: List[int],
    start_date: datetime.date,
    end_date: datetime.date,
    directions: Optional[List[int]] = None,
    classifications: Optional[List[int]] = None,
    include_holidays: bool = True,
    include_weekends: bool = True,
    required_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """Fetches hourly count data for a list of stations and date range."""
    if not station_keys:
        return pd.DataFrame()

    with get_db_session() as session:
        if not session: return pd.DataFrame()

        if required_cols:
            cols_to_select = [getattr(HourlyCount, col) for col in required_cols if hasattr(HourlyCount, col)]
            if HourlyCount.station_key not in cols_to_select:
                cols_to_select.insert(0, HourlyCount.station_key)
            if HourlyCount.count_date not in cols_to_select:
                cols_to_select.insert(1, HourlyCount.count_date)
            if HourlyCount.day_of_week not in cols_to_select:
                cols_to_select.insert(2, HourlyCount.day_of_week)
            if HourlyCount.is_public_holiday not in cols_to_select:
                cols_to_select.insert(3, HourlyCount.is_public_holiday)
        else:
            cols_to_select = [
                HourlyCount.station_key, HourlyCount.count_date, HourlyCount.day_of_week,
                HourlyCount.is_public_holiday, HourlyCount.is_school_holiday,
                HourlyCount.classification_seq, HourlyCount.traffic_direction_seq, HourlyCount.cardinal_direction_seq,
                HourlyCount.daily_total
            ] + [getattr(HourlyCount, f'hour_{h:02d}') for h in range(24)]

        stmt = select(*cols_to_select).where(
            HourlyCount.station_key.in_(station_keys),
            HourlyCount.count_date.between(start_date, end_date)
        )

        if directions:
            stmt = stmt.where(HourlyCount.traffic_direction_seq.in_(directions))
        if classifications:
            stmt = stmt.where(HourlyCount.classification_seq.in_(classifications))

        try:
            df = pd.read_sql(stmt, session.bind)
            return df
        except Exception as e:
            st.error(f"Error fetching hourly data: {e}")
            return pd.DataFrame()

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_latest_data_date(station_key: int, direction_seq: int) -> Optional[datetime.date]:
    """Fetches the latest count_date for a specific station and direction."""
    with get_db_session() as session:
        if not session:
            return None
        try:
            stmt = select(func.max(HourlyCount.count_date)).where(
                and_(
                    HourlyCount.station_key == station_key,
                    HourlyCount.traffic_direction_seq == direction_seq
                )
            )
            latest_date = session.scalar(stmt)
            logger.debug(f"Latest date for station {station_key}, direction {direction_seq}: {latest_date}")
            return latest_date
        except Exception as e:
            st.error(f"Error fetching latest date for station {station_key}, direction {direction_seq}: {e}")
            logger.error(f"Error fetching latest date for station {station_key}, direction {direction_seq}: {e}")
            return None

# --- Data Transformation Functions ---

@st.cache_data(ttl=3600)
def calculate_peak_volumes(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate AM and PM peak volumes."""
    am_cols = [f'hour_{str(h).zfill(2)}' for h in range(6, 10)]
    pm_cols = [f'hour_{str(h).zfill(2)}' for h in range(15, 19)]
    
    return {
        'am_peak': df[am_cols].sum().sum() / len(df) if not df.empty else 0,
        'pm_peak': df[pm_cols].sum().sum() / len(df) if not df.empty else 0
    }

@st.cache_data(ttl=3600)
def calculate_hourly_profile(df: pd.DataFrame, weekdays_only: bool = False) -> pd.DataFrame:
    """Calculate average hourly profile."""
    if weekdays_only:
        df = df[df['day_of_week'].between(1, 5)]
    
    hour_cols = [f'hour_{str(h).zfill(2)}' for h in range(24)]
    hourly_means = df[hour_cols].mean()
    
    return pd.DataFrame({
        'hour': range(24),
        'average_volume': hourly_means.values
    })

@st.cache_data(ttl=3600)
def calculate_aadt(conn, station_key: int, year: int) -> float:
    """Calculate Annual Average Daily Traffic."""
    with get_db_session() as session:
        if not session: return 0.0
        
        stmt = select(HourlyCount.daily_total).where(
            and_(
                HourlyCount.station_key == station_key,
                HourlyCount.year == year,
                HourlyCount.classification_seq == 1,
                func.count(*(getattr(HourlyCount, f'hour_{str(h).zfill(2)}') 
                           for h in range(24))) >= 19
            )
        ).group_by(HourlyCount.count_date)
        
        df = pd.read_sql(stmt, session.bind)
        return df['daily_total'].mean() if not df.empty else 0.0

@st.cache_data(ttl=3600)
def calculate_aawt(conn, station_key: int, year: int) -> float:
    """Calculate Average Annual Weekday Traffic."""
    with get_db_session() as session:
        if not session: return 0.0
        
        stmt = select(HourlyCount.daily_total).where(
            and_(
                HourlyCount.station_key == station_key,
                HourlyCount.year == year,
                HourlyCount.classification_seq == 1,
                HourlyCount.day_of_week.between(1, 5),
                HourlyCount.is_public_holiday == false()
            )
        )
        
        df = pd.read_sql(stmt, session.bind)
        return df['daily_total'].mean() if not df.empty else 0.0

@st.cache_data(ttl=3600)
def calculate_heavy_vehicle_percentage(conn, station_key: int, start_date: datetime.date, end_date: datetime.date) -> float:
    """Calculate Heavy Vehicle Percentage for a period."""
    with get_db_session() as session:
        if not session: return 0.0
        
        volumes = {}
        for seq in [1, 3]:
            stmt = select(func.sum(HourlyCount.daily_total)).where(
                and_(
                    HourlyCount.station_key == station_key,
                    HourlyCount.classification_seq == seq,
                    HourlyCount.count_date.between(start_date, end_date)
                )
            )
            result = session.scalar(stmt)
            volumes[seq] = float(result) if result else 0.0
            
        return (volumes[3] / volumes[1] * 100) if volumes[1] > 0 else 0.0

def update_station_geometries(conn):
    """Update PostGIS geometries for all stations."""
    with get_db_session() as session:
        if not session: return
        
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
        session.commit()