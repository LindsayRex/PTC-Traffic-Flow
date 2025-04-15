import os
import datetime
import logging
from log_config import setup_logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, Station, HourlyCount
import pandas as pd
from geoalchemy2.functions import ST_MakePoint

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def get_user_confirmation(message):
    while True:
        response = input(f"{message} (yes/no): ").lower().strip()
        if response in ['yes', 'no']:
            return response == 'yes'
        print("Please answer 'yes' or 'no'")
        logger.warning(f"Invalid user input: {response}. Expected 'yes' or 'no'.")

def init_db():
    logger.info("Starting database initialization process")
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/traffic_db')
    logger.info(f"Using database URL: {DATABASE_URL}")
    
    engine = create_engine(DATABASE_URL)
    logger.info("Database engine created")

    try:
        print("\nInitializing PostGIS extension...")
        logger.info("Initializing PostGIS extension")
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
        print("PostGIS extension initialized successfully")

        print("\nWARNING: This will drop all existing tables in the database.")
        print("All data will be lost and tables will be recreated.")
        logger.warning("User prompted for database reset confirmation")

        if not get_user_confirmation("Are you sure you want to proceed?"):
            logger.info("Database initialization cancelled by user at first prompt")
            print("Database initialization cancelled.")
            return

        print("\nDropping all tables...")
        logger.info("Dropping all existing tables")
        Base.metadata.drop_all(engine)
        print("All tables dropped successfully")

        print("Creating new tables...")
        logger.info("Creating new database tables")
        Base.metadata.create_all(engine)
        print("New tables created successfully")

        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            print("\nImporting station reference data...")
            logger.info("Starting station reference data import")
            df_stations = pd.read_csv('app/data/road_traffic_counts_station_reference.csv')
            stations_count = 0

            for _, row in df_stations.iterrows():
                existing = session.query(Station).filter_by(station_key=row.get('station_key')).first()
                if existing:
                    continue

                station = Station(
                    station_key=row.get('station_key'),
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
                    quality_rating=int(row.get('quality_rating', 0)),
                    wgs84_latitude=float(row.get('wgs84_latitude', 0)),
                    wgs84_longitude=float(row.get('wgs84_longitude', 0))
                )
                session.add(station)
                stations_count += 1

            session.commit()
            print(f"Successfully imported {stations_count} stations")
            logger.info(f"Imported {stations_count} stations")

            print("\nUpdating station geometries...")
            logger.info("Updating station geometries")
            stmt = text("""
                UPDATE stations 
                SET location_geom = ST_SetSRID(ST_MakePoint(wgs84_longitude, wgs84_latitude), 4326)
                WHERE location_geom IS NULL
            """)
            session.execute(stmt)
            session.commit()
            print("Station geometries updated successfully")

            print("\nImporting hourly counts data...")
            logger.info("Starting hourly counts import")
            df_counts = pd.read_csv('app/data/hourly_counts.csv')
            counts_processed = 0

            for _, row in df_counts.iterrows():
                count_date = pd.to_datetime(row['count_date']).date()

                count = HourlyCount(
                    station_key=row['station_key'],
                    traffic_direction_seq=row['traffic_direction_seq'],
                    cardinal_direction_seq=row.get('cardinal_direction_seq'),
                    classification_seq=row['classification_seq'],
                    count_date=count_date,
                    year=count_date.year,
                    month=count_date.month,
                    day_of_week=count_date.isoweekday(),
                    is_public_holiday=bool(row.get('is_public_holiday', False)),
                    is_school_holiday=bool(row.get('is_school_holiday', False))
                )

                # Add hourly values
                hour_cols = [f'hour_{str(h).zfill(2)}' for h in range(24)]
                daily_total = 0
                valid_hours = 0

                for hour in range(24):
                    hour_col = f'hour_{str(hour).zfill(2)}'
                    value = row.get(hour_col, 0)
                    setattr(count, hour_col, value)
                    if value is not None:
                        daily_total += value
                        valid_hours += 1

                count.daily_total = daily_total if valid_hours >= 19 else None
                session.add(count)
                counts_processed += 1

                if counts_processed % 1000 == 0:
                    print(f"Processed {counts_processed} hourly count records...")
                    logger.info(f"Processed {counts_processed} hourly count records")
                    session.commit()

            session.commit()
            print(f"\nSuccessfully imported {counts_processed} hourly count records")
            logger.info(f"Completed importing {counts_processed} hourly count records")
            print("\nDatabase initialization completed successfully!")
            logger.info("Database initialization completed successfully")

        except Exception as e:
            error_msg = f"Error importing data: {str(e)}"
            print(f"\nERROR: {error_msg}")
            logger.error(error_msg)
            session.rollback()
        finally:
            session.close()

    except Exception as e:
        error_msg = f"Fatal error during database initialization: {str(e)}"
        print(f"\nCRITICAL ERROR: {error_msg}")
        logger.critical(error_msg)

if __name__ == '__main__':
    init_db()
