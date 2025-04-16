import os
import logging
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from log_config import setup_logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base, Station, HourlyCount
from geoalchemy2 import WKTElement
from db_utils import get_db_session, get_engine  # Import get_engine
from tqdm import tqdm  # Import tqdm
from data_load_checker import validate_station_data, validate_hourly_count_data

# --- CONFIGURABLE PARAMETERS ---
MAX_ROWS_TO_PROCESS = 'all'  # Set to a number to limit rows, or 'all' to process the entire file
COMMIT_BATCH_SIZE = 10000  # Increase commit batch size
# -----------------------------

# Set up logging
setup_logging(script_name="ingestion")  # Pass the script name
logger = logging.getLogger(__name__)

# Set up skipped data logging
skipped_data_logger = logging.getLogger('skipped_data')
skipped_data_logger.setLevel(logging.INFO)
os.makedirs('logs', exist_ok=True)  # Ensure the 'logs' directory exists
skipped_data_handler = logging.FileHandler('logs/skipped_data.log')
skipped_data_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
skipped_data_handler.setFormatter(skipped_data_formatter)
skipped_data_logger.addHandler(skipped_data_handler)

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

def load_station_reference_data(session):
    """Loads station reference data from CSV into the database."""
    try:
        # Load station reference data
        df_stations = pd.read_csv('app/data/road_traffic_counts_station_reference.csv')
        logger.info(f"Read {len(df_stations)} station records from CSV")

        # Limit the number of rows to process
        if MAX_ROWS_TO_PROCESS != 'all':
            try:
                max_rows = int(MAX_ROWS_TO_PROCESS)
                df_stations = df_stations.head(max_rows)
                logger.info(f"Limiting processing to the first {max_rows} rows.")
            except ValueError:
                logger.error("Invalid value for MAX_ROWS_TO_PROCESS. Please set to a number or 'all'. Processing all rows.")
        else:
            logger.info("Processing all rows in the CSV file.")

        # Validate station data
        if not validate_station_data(df_stations):
            logger.error("Station data validation failed. Aborting data load.")
            return False

        # Data Type Conversions
        for col in ['wgs84_latitude', 'wgs84_longitude', 'quality_rating', 'station_key']:
            if col in df_stations.columns:
                if col in ['wgs84_latitude', 'wgs84_longitude']:
                    df_stations[col] = pd.to_numeric(df_stations[col], errors='coerce')
                else:
                    df_stations[col] = pd.to_numeric(df_stations[col], errors='coerce').fillna(0).astype(int)

        # Data Type Conversions and Geometry Creation
        stations_to_insert = []
        skipped_stations = 0
        for idx, row in tqdm(df_stations.iterrows(), total=len(df_stations), desc="Processing Stations"):
            try:
                latitude = safe_float(row.get('wgs84_latitude'))
                longitude = safe_float(row.get('wgs84_longitude'))

                if pd.isna(latitude) or pd.isna(longitude):
                    logger.warning(f"Skipping row due to invalid latitude or longitude: {row}")
                    skipped_data_logger.info(f"Skipped station record {idx}: Invalid latitude or longitude - {row.to_dict()}")
                    skipped_stations += 1
                    continue

                # Geometry Creation (Optimized)
                wkt_point = f"POINT({round(longitude, 6)} {round(latitude, 6)})"
                location_geom = WKTElement(wkt_point, srid=4326)

                station = Station(
                    station_key=int(row.get('station_key')),
                    station_id=str(row.get('station_id')) if not isinstance(row.get('station_id'), str) else row.get('station_id'),
                    name=str(row.get('name')) if not isinstance(row.get('name'), str) else row.get('name'),
                    road_name=str(row.get('road_name')) if not isinstance(row.get('road_name'), str) else row.get('road_name'),
                    full_name=str(row.get('full_name')) if not isinstance(row.get('full_name'), str) else row.get('full_name'),
                    common_road_name=str(row.get('common_road_name')) if not isinstance(row.get('common_road_name'), str) else row.get('common_road_name'),
                    lga=str(row.get('lga')) if not isinstance(row.get('lga'), str) else row.get('lga'),
                    suburb=str(row.get('suburb')) if not isinstance(row.get('suburb'), str) else row.get('suburb'),
                    post_code=str(row.get('post_code')) if not isinstance(row.get('post_code'), str) else row.get('post_code'),
                    road_functional_hierarchy=str(row.get('road_functional_hierarchy')) if not isinstance(row.get('road_functional_hierarchy'), str) else row.get('road_functional_hierarchy'),
                    lane_count=str(row.get('lane_count')) if not isinstance(row.get('lane_count'), str) else row.get('lane_count'),
                    road_classification_type=str(row.get('road_classification_type')) if not isinstance(row.get('road_classification_type'), str) else row.get('road_classification_type'),
                    device_type=str(row.get('device_type')) if not isinstance(row.get('device_type'), str) else row.get('device_type'),
                    permanent_station=bool(row.get('permanent_station', False)),
                    vehicle_classifier=bool(row.get('vehicle_classifier', False)),
                    heavy_vehicle_checking_station=bool(row.get('heavy_vehicle_checking_station', False)),
                    quality_rating=int(row.get('quality_rating', 0)),
                    wgs84_latitude=str(latitude),
                    wgs84_longitude=str(longitude),
                    location_geom=location_geom
                )
                stations_to_insert.append(station)

            except Exception as row_error:
                logger.error(f"Error processing station record {idx}: {row_error}")
                skipped_data_logger.info(f"Skipped station record {idx}: Processing error - {row_error} - {row.to_dict()}")
                skipped_stations += 1
                continue

        # Bulk insert using SQLAlchemy
        logger.info("Inserting station data in bulk...")
        session.add_all(stations_to_insert)
        session.commit()
        logger.info(f"Successfully imported {len(stations_to_insert)} stations")
        if skipped_stations > 0:
            logger.warning(f"Skipped {skipped_stations} station records due to data issues. See logs/skipped_data.log for details.")

        return True

    except Exception as e:
        logger.error(f"Error loading station reference data: {e}")
        session.rollback()
        return False

def ingest_hourly_data():
    """Ingests hourly traffic data from a CSV file into the database."""

    try:
        with get_db_session() as session:  # Use the context manager
            if session is None:
                logger.error("Failed to get database session.")
                return False

            # Load station reference data first
            if not load_station_reference_data(session):
                logger.error("Failed to load station reference data. Aborting hourly data ingestion.")
                return False

            # Read CSV file using relative path
            csv_file_path = '/home/runner/workspace/app/data/road_traffic_counts_hourly_sample_0.csv'
            df = pd.read_csv(csv_file_path, low_memory=False)
            logger.info(f"Successfully read CSV file with {len(df)} rows")

            # Limit the number of rows to process
            if MAX_ROWS_TO_PROCESS != 'all':
                try:
                    max_rows = int(MAX_ROWS_TO_PROCESS)
                    df = df.head(max_rows)
                    logger.info(f"Limiting processing to the first {max_rows} rows.")
                except ValueError:
                    logger.error("Invalid value for MAX_ROWS_TO_PROCESS. Please set to a number or 'all'. Processing all rows.")
            else:
                logger.info("Processing all rows in the CSV file.")

            hourly_counts_processed = 0
            skipped_station_keys = 0
            skipped_hourly_counts = 0

            try:
                # Load valid station keys into a set
                valid_station_keys = {station.station_key for station in session.query(Station.station_key).all()}
                logger.info(f"Loaded {len(valid_station_keys)} valid station keys into set.")

                # Load Hourly Counts
                # Prepare data for bulk insert
                hourly_counts_to_insert = []
                for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing Hourly Counts"):
                    # Extract station_key
                    station_key = safe_int(row.get('station_key'))

                    # Check if station_key exists in stations table (using set)
                    if station_key not in valid_station_keys:
                        logger.warning(f"Skipping hourly count record due to missing station_key: {station_key}")
                        skipped_data_logger.info(f"Skipped hourly count record: Missing station_key - {station_key} - {row.to_dict()}")
                        skipped_station_keys += 1  # Increment the counter
                        skipped_hourly_counts += 1
                        continue

                    # Convert date string to datetime
                    try:
                        count_date = pd.to_datetime(row['date']).date()
                    except ValueError as e:
                        logger.error(f"Error converting date: {e}")
                        skipped_data_logger.info(f"Skipped hourly count record: Invalid date format - {row.to_dict()}")
                        skipped_hourly_counts += 1
                        continue

                    # Create HourlyCount object
                    count_data = {
                        'station_key': station_key,
                        'traffic_direction_seq': safe_int(row.get('traffic_direction_seq')),
                        'cardinal_direction_seq': safe_int(row.get('cardinal_direction_seq')),
                        'classification_seq': safe_int(row.get('classification_seq')),
                        'count_date': count_date,
                        'year': count_date.year,
                        'month': count_date.month,
                        'day_of_week': count_date.isoweekday(),
                        'is_public_holiday': bool(row.get('is_public_holiday', False)),
                        'is_school_holiday': bool(row.get('is_school_holiday', False))
                    }

                    # Add hourly values
                    for hour in range(24):
                        hour_col = f'hour_{str(hour).zfill(2)}'
                        # Use .get() with a default value of 0 and handle NaN values
                        hour_value = row.get(hour_col, 0)
                        if pd.isna(hour_value):
                            hour_value = 0
                        count_data[hour_col] = int(hour_value)

                    # Calculate daily total
                    hour_cols = [f'hour_{str(h).zfill(2)}' for h in range(24)]
                    daily_total = sum(int(row.get(col, 0)) if not pd.isna(row.get(col, 0)) else 0 for col in hour_cols)
                    count_data['daily_total'] = daily_total

                    hourly_counts_to_insert.append(count_data)
                    hourly_counts_processed += 1

                    # Commit in batches
                    if hourly_counts_processed % COMMIT_BATCH_SIZE == 0:
                        session.bulk_insert_mappings(HourlyCount, hourly_counts_to_insert)
                        session.commit()
                        hourly_counts_to_insert = []  # Clear the list after commit
                        logger.info(f"Processed {hourly_counts_processed} hourly count records...")

                # Final commit for hourly counts
                if hourly_counts_to_insert:  # Commit any remaining records
                    session.bulk_insert_mappings(HourlyCount, hourly_counts_to_insert)
                    session.commit()
                print(f"Successfully imported {hourly_counts_processed} hourly count records")
                logger.info(f"Successfully imported {hourly_counts_processed} hourly count records")

                # Log the number of skipped station keys
                logger.info(f"Skipped {skipped_station_keys} hourly count records due to missing station_key values.")

                if skipped_hourly_counts > 0:
                    logger.warning(f"Skipped {skipped_hourly_counts} hourly count records due to data issues. See logs/skipped_data.log for details.")

                # Verify counts in the database
                engine = get_engine()
                if engine:
                    try:
                        with engine.connect() as conn:
                            station_count_db = conn.execute(text("SELECT COUNT(*) FROM stations")).scalar()
                            hourly_count_db = conn.execute(text("SELECT COUNT(*) FROM hourly_counts")).scalar()

                            logger.info(f"Stations in DB: {station_count_db}")
                            logger.info(f"Hourly counts in DB: {hourly_count_db}")

                    except Exception as e:
                        logger.error(f"Error querying database counts: {e}")
                else:
                    logger.error("Failed to get database engine for count verification.")

                return True

            except Exception as e:
                logger.error(f"Error importing data: {e}")
                session.rollback()
                return False

    except Exception as e:
        logger.error(f"A fatal error occurred: {e}")
        return False

if __name__ == '__main__':
    success = ingest_hourly_data()
    exit(0 if success else 1)
