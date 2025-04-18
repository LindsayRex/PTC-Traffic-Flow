# app/db_utils.py
import streamlit as st
import logging
import pandas as pd
import sqlalchemy
import datetime
from sqlalchemy import create_engine, select, func, distinct, text, and_, or_, true, false
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from typing import List, Optional, Tuple, Dict, Any
from models import Base, Station, HourlyCount

logger = logging.getLogger(__name__)

@st.cache_resource
def get_engine():
    """Creates a SQLAlchemy engine using Streamlit secrets."""
    try:
        # Use DATABASE_URL from Replit Secrets
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            st.error("DATABASE_URL not found in environment")
            return None

        debug_value = st.secrets.environment.get("debug", False)
        # Convert string "true" or "false" to boolean if necessary
        if isinstance(debug_value, str):
            debug = debug_value.lower() == "true"
        else:
            debug = bool(debug_value)  # Ensure it's a boolean

        return create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            echo=False
        )
    except Exception as e:
        st.error(f"Failed to create database engine: {e}")
        logger.error(f"Database connection error: {e}")
        return None

engine = get_engine()

@st.cache_resource
def get_session_factory():
    """Creates a session factory."""
    if engine is None:
        st.error("Database engine not initialized.")
        return None
    return sessionmaker(bind=engine)

@contextmanager
def get_db_session() -> Session:
    """Provide a transactional scope around a series of operations."""
    session = None
    if SessionFactory:
        session = SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            st.error(f"Database Error: {e}") # Show error in UI
            print(f"Database Error: {e}") # Log error to console/logs
            if session:
                session.rollback()
            raise # Re-raise the exception for potential higher-level handling
        finally:
            if session:
                session.close()
    else:
        st.error("Session Factory not available.")
        # Yield None or raise an error if session is critical
        yield None # Allows calling code to check if session is None

# --- Query Functions ---
# Use @st.cache_data for functions that return data based on inputs

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_all_station_metadata(_conn) -> pd.DataFrame:
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
            # Add other columns as needed
        ).order_by(Station.lga, Station.suburb, Station.road_name)
        try:
            # Use pandas read_sql for direct DataFrame conversion
            df = pd.read_sql(stmt, session.bind)
            return df
        except Exception as e:
            st.error(f"Error fetching all station metadata: {e}")
            return pd.DataFrame()



@st.cache_data(ttl=3600)
def get_station_details(_conn, station_key: int) -> Optional[Station]:
    """Fetches a single station's full details by station_key."""
    with get_db_session() as session:
        if not session: return None
        try:
            # Fetch the single station object
            station = session.get(Station, station_key)
            return station
        except Exception as e:
            st.error(f"Error fetching station details for key {station_key}: {e}")
            return None

@st.cache_data(ttl=3600)
def get_distinct_values(_conn, column_name: str, table_model=Station) -> List[str]:
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
def get_suburbs_for_lgas(_conn, lgas: List[str]) -> List[str]:
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
    _conn,
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
                 # Handle potential variations in road_name vs common_road_name
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
    _conn,
    station_keys: List[int],
    start_date: datetime.date,
    end_date: datetime.date,
    directions: Optional[List[int]] = None,
    classifications: Optional[List[int]] = None,
    include_holidays: bool = True, # Fetch all by default, filter later if needed
    include_weekends: bool = True, # Fetch all by default, filter later if needed
    required_cols: Optional[List[str]] = None # Specify columns to fetch
) -> pd.DataFrame:
    """Fetches hourly count data for a list of stations and date range."""
    if not station_keys:
        return pd.DataFrame()

    with get_db_session() as session:
        if not session: return pd.DataFrame()

        # Select specific columns if requested, otherwise fetch common ones
        if required_cols:
            cols_to_select = [getattr(HourlyCount, col) for col in required_cols if hasattr(HourlyCount, col)]
            if HourlyCount.station_key not in cols_to_select: # Always include key for potential joins
                 cols_to_select.insert(0, HourlyCount.station_key)
            if HourlyCount.count_date not in cols_to_select:
                 cols_to_select.insert(1, HourlyCount.count_date)
            if HourlyCount.day_of_week not in cols_to_select:
                 cols_to_select.insert(2, HourlyCount.day_of_week)
            if HourlyCount.is_public_holiday not in cols_to_select:
                 cols_to_select.insert(3, HourlyCount.is_public_holiday)
        else:
            # Default selection including necessary filter columns and hourly data
            cols_to_select = [
                HourlyCount.station_key, HourlyCount.count_date, HourlyCount.day_of_week,
                HourlyCount.is_public_holiday, HourlyCount.is_school_holiday, # Keep school holiday if needed later
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

        # We fetch all days/holidays and let Python filter, which is often
        # simpler than complex SQL date logic unless performance dictates otherwise.
        # Add filters here if DB-side filtering is essential:
        # if not include_holidays:
        #     stmt = stmt.where(HourlyCount.is_public_holiday == false())
        # if not include_weekends:
        #     stmt = stmt.where(HourlyCount.day_of_week.in_([1, 2, 3, 4, 5])) # Mon-Fri

        try:
            df = pd.read_sql(stmt, session.bind)
            return df
        except Exception as e:
            st.error(f"Error fetching hourly data: {e}")
            return pd.DataFrame()

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
        
        # Get all daily totals for the year where we have at least 19 hours of data
        stmt = select(HourlyCount.daily_total).where(
            and_(
                HourlyCount.station_key == station_key,
                HourlyCount.year == year,
                HourlyCount.classification_seq == 1,
                # Count non-null hours to ensure data quality
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
        
        # Get totals for both all vehicles (seq=1) and heavy vehicles (seq=3)
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

# Function to update geospatial data for stations
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

SessionFactory = get_session_factory()