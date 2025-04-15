import pandas as pd
import logging
from log_config import setup_logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from models import Base, Station, HourlyCount
from datetime import datetime
from db_utils import get_db_session  # Import the context manager
import numpy as np
from geoalchemy2 import WKTElement

import sys
# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Set console handler to WARNING level only
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
        handler.setLevel(logging.WARNING)

# Function to safely convert to float
def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# Function to safely convert to int
def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0  # Or None, depending on your requirements

def ingest_hourly_data():
    """Ingests hourly traffic data from a CSV file into the database."""

    try:
        # Read CSV file using relative path
        df = pd.read_csv('/home/runner/workspace/app/data/road_traffic_counts_hourly_sample_0.csv', low_memory=False)
        logger.info(f"Successfully read CSV file with {len(df)} rows")

        # Process each row
        records_processed = 0

        with get_db_session() as session:  # Use the context manager
            if session is None:
                logger.error("Failed to get database session.")
                print("Failed to get database session. Check logs.")
                return False

            try:
                for _, row in df.iterrows():
                    # Extract lat/lon and create WKT representation
                    latitude = safe_float(row.get('wgs84_latitude'))
                    longitude = safe_float(row.get('wgs84_longitude'))

                    # Skip if lat or lon is missing or invalid
                    if latitude is None or longitude is None:
                        logger.warning(f"Skipping row due to invalid latitude or longitude: {row}")
                        continue

                    # Create WKT representation of the point geometry
                    # Rounding to reduce precision
                    wkt_point = f"POINT({round(longitude, 6)} {round(latitude, 6)})"
                    location_geom = WKTElement(wkt_point, srid=4326)

                    # Create Station object
                    station = Station(
                        station_key=safe_int(row.get('station_key')),
                        station_id=str(row.get('station_id')),
                        name=str(row.get('name')),
                        road_name=str(row.get('road_name')),
                        full_name=str(row.get('full_name')),
                        common_road_name=str(row.get('common_road_name')),
                        lga=str(row.get('lga')),
                        suburb=str(row.get('suburb')),
                        post_code=str(row.get('post_code')),
                        road_functional_hierarchy=str(row.get('road_functional_hierarchy')),
                        lane_count=str(row.get('lane_count')),
                        road_classification_type=str(row.get('road_classification_type')),
                        device_type=str(row.get('device_type')),
                        permanent_station=bool(row.get('permanent_station', False)),
                        vehicle_classifier=bool(row.get('vehicle_classifier', False)),
                        heavy_vehicle_checking_station=bool(row.get('heavy_vehicle_checking_station', False)),
                        quality_rating=safe_int(row.get('quality_rating', 0)),
                        wgs84_latitude=str(row.get('wgs84_latitude')),  # Store as string
                        wgs84_longitude=str(row.get('wgs84_longitude')), # Store as string
                        location_geom=location_geom
                    )

                    # Add the station to the session
                    session.add(station)
                    records_processed += 1

                    # Commit in batches of 1000
                    if records_processed % 1000 == 0:
                        session.commit()
                        print(f"Processed {records_processed} station records...")
                        logger.info(f"Processed {records_processed} station records")

                # Final commit for stations
                session.commit()
                print(f"Successfully imported {records_processed} station records")
                logger.info(f"Successfully imported {records_processed} station records")

                # Reset records_processed for hourly counts
                records_processed = 0

                for _, row in df.iterrows():
                    # Convert date string to datetime
                    count_date = pd.to_datetime(row['date']).date()

                    # Create HourlyCount object
                    count = HourlyCount(
                        station_key=safe_int(row.get('station_key')),
                        traffic_direction_seq=safe_int(row.get('traffic_direction_seq')),
                        cardinal_direction_seq=safe_int(row.get('cardinal_direction_seq')),
                        classification_seq=safe_int(row.get('classification_seq')),
                        count_date=count_date,
                        year=count_date.year,
                        month=count_date.month,
                        day_of_week=count_date.isoweekday(),
                        is_public_holiday=bool(row.get('is_public_holiday', False)),
                        is_school_holiday=bool(row.get('is_school_holiday', False))
                    )

                    # Add hourly values
                    for hour in range(24):
                        hour_col = f'hour_{str(hour).zfill(2)}'
                        hour_value = safe_int(row.get(hour_col, 0))
                        setattr(count, hour_col, hour_value)

                    # Calculate daily total
                    hour_cols = [f'hour_{str(h).zfill(2)}' for h in range(24)]
                    daily_total = sum(safe_int(row.get(col, 0)) for col in hour_cols)
                    count.daily_total = daily_total

                    session.add(count)
                    records_processed += 1

                    # Commit in batches of 1000
                    if records_processed % 1000 == 0:
                        session.commit()
                        print(f"Processed {records_processed} hourly count records...")
                        logger.info(f"Processed {records_processed} hourly count records")

                # Final commit for hourly counts
                session.commit()
                print(f"Successfully imported {records_processed} hourly count records")
                logger.info(f"Successfully imported {records_processed} hourly count records")

                return True

            except Exception as e:
                logger.error(f"Error importing data: {e}")
                print(f"Error importing data: {e}")
                session.rollback()
                return False

    except Exception as e:
        logger.error(f"A fatal error occurred: {e}")
        print(f"A fatal error occurred: {e}")
        return False

if __name__ == '__main__':
    success = ingest_hourly_data()
    exit(0 if success else 1)
