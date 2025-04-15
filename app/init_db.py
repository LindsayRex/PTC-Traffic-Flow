import os
import logging
from log_config import setup_logging
from sqlalchemy.exc import SQLAlchemyError
from models import Base, Station
import pandas as pd
from geoalchemy2 import WKTElement
from db_utils import get_engine, get_db_session
from sqlalchemy import text

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Set console handler to WARNING level only
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
        handler.setLevel(logging.WARNING)

def init_db():
    """Initialize the database with station reference data"""
    logger.info("Starting database initialization process")

    engine = get_engine()
    if not engine:
        logger.error("Failed to create database engine")
        return

    try:
        with engine.connect() as connection:
            try:
                print("\nInitializing PostGIS extension...")
                logger.info("Initializing PostGIS extension")
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                connection.commit()
                print("PostGIS extension initialized successfully")
            except SQLAlchemyError as e:
                error_msg = f"SQLAlchemy error during PostGIS initialization: {str(e)}"
                print(f"\nERROR: {error_msg}")
                logger.error(error_msg)
                raise

            print("\nCreating new tables...")
            logger.info("Creating new database tables")
            Base.metadata.create_all(engine)
            print("New tables created successfully")

            print("\nImporting station reference data...")
            logger.info("Starting station reference data import")

            try:
                df_stations = pd.read_csv('app/data/road_traffic_counts_station_reference.csv')
                logger.info(f"Read {len(df_stations)} station records from CSV")
                print(f"Processing {len(df_stations)} station records...")
                stations_count = 0

                with get_db_session() as session:
                    if not session:
                        logger.error("Failed to create database session")
                        return

                    for idx, row in df_stations.iterrows():
                        try:
                            if idx % 500 == 0:
                                print(f"Processed {idx}/{len(df_stations)} records...")

                            existing = session.query(Station).filter_by(station_key=row.get('station_key')).first()
                            if existing:
                                continue

                            latitude = row.get('wgs84_latitude')
                            longitude = row.get('wgs84_longitude')

                            if latitude is None or longitude is None:
                                logger.warning(f"Skipping row due to invalid latitude or longitude: {row}")
                                continue

                            try:
                                latitude = float(latitude)
                                longitude = float(longitude)
                            except (ValueError, TypeError) as e:
                                logger.error(f"Invalid latitude or longitude format in row {idx}: {e}")
                                continue

                            wkt_point = f"POINT({round(longitude, 6)} {round(latitude, 6)})"
                            location_geom = WKTElement(wkt_point, srid=4326)

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
                                wgs84_latitude=latitude,
                                wgs84_longitude=longitude,
                                location_geom=location_geom
                            )
                            session.add(station)
                            stations_count += 1

                            if stations_count % 500 == 0:
                                session.commit()
                                print(f"Committed {stations_count} stations")

                        except Exception as row_error:
                            logger.error(f"Error processing station record {idx}: {row_error}")
                            print(f"Error processing station record {idx}: {row_error}")
                            session.rollback()
                            continue

                    session.commit()
                    print(f"Successfully imported {stations_count} stations")
                    logger.info(f"Imported {stations_count} stations")

            except Exception as e:
                error_msg = f"Error during station data import: {str(e)}"
                print(f"\nERROR: {error_msg}")
                logger.error(error_msg)
                raise

            print("\nDatabase initialization completed successfully!")
            logger.info("Database initialization completed successfully")

    except SQLAlchemyError as e:
        error_msg = f"SQLAlchemy error during database operations: {str(e)}"
        print(f"\nCRITICAL ERROR: {error_msg}")
        logger.critical(error_msg)
    except Exception as e:
        error_msg = f"Fatal error during database initialization: {str(e)}"
        print(f"\nCRITICAL ERROR: {error_msg}")
        logger.critical(error_msg)
    finally:
        if engine:
            engine.dispose()
            logger.info("Database engine disposed")

if __name__ == '__main__':
    init_db()