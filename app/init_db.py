import os
import datetime
import logging
from log_config import setup_logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
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

    # Ask for confirmation before proceeding
    if not get_user_confirmation("Are you sure you want to initialize the database? This will create all necessary tables."):
        logger.info("Database initialization cancelled by user")
        return

    try:
        with engine.connect() as connection:
            logger.info("Initializing PostGIS extension")
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            connection.commit()
            logger.info("PostGIS extension initialized successfully")

            logger.info("Creating database tables")
            Base.metadata.create_all(engine)
            logger.info("Database tables created successfully")

            Session = sessionmaker(bind=engine)
            session = Session()

            try:
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
                logger.info(f"Successfully imported {stations_count} stations")

                logger.info("Updating station geometries")
                stmt = text("""
                    UPDATE stations 
                    SET location_geom = ST_SetSRID(ST_MakePoint(wgs84_longitude, wgs84_latitude), 4326)
                    WHERE location_geom IS NULL
                """)
                connection.execute(stmt)
                connection.commit()
                logger.info("Station geometries updated successfully")

                session.close()
                logger.info("Database initialization completed successfully")
                print("\nDatabase initialization completed successfully!")

            except SQLAlchemyError as e:
                error_msg = f"SQLAlchemy error during data import: {str(e)}"
                logger.error(error_msg)
                session.rollback()
                raise
            except Exception as e:
                error_msg = f"Error during data import: {str(e)}"
                logger.error(error_msg)
                session.rollback()
                raise
            finally:
                session.close()

    except SQLAlchemyError as e:
        error_msg = f"SQLAlchemy error during database operations: {str(e)}"
        logger.critical(error_msg)
        raise
    except Exception as e:
        error_msg = f"Fatal error during database initialization: {str(e)}"
        logger.critical(error_msg)
        raise
    finally:
        engine.dispose()
        logger.info("Database engine disposed")

if __name__ == '__main__':
    init_db()