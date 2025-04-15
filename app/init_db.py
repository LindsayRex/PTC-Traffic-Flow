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
from geoalchemy2 import WKTElement

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

            Session = sessionmaker(bind=engine)
            session = Session(bind=connection)

            try:
                print("\nImporting station reference data...")
                logger.info("Starting station reference data import")
                try:
                    df_stations = pd.read_csv('app/data/road_traffic_counts_station_reference.csv')
                    logger.info(f"Read {len(df_stations)} station records from CSV")
                    print(f"Processing {len(df_stations)} station records...")
                    stations_count = 0

                    for idx, row in df_stations.iterrows():
                        try:
                            if idx % 500 == 0:
                                print(f"Processed {idx}/{len(df_stations)} records...")
                                
                            existing = session.query(Station).filter_by(station_key=row.get('station_key')).first()
                            if existing:
                                continue
                            
                            # Extract lat/lon and create WKT representation
                            latitude = row.get('wgs84_latitude')
                            longitude = row.get('wgs84_longitude')

                            # Skip if lat or lon is missing or invalid
                            if latitude is None or longitude is None:
                                logger.warning(f"Skipping row due to invalid latitude or longitude: {row}")
                                continue

                            try:
                                latitude = float(latitude)
                                longitude = float(longitude)
                            except (ValueError, TypeError) as e:
                                logger.error(f"Invalid latitude or longitude format in row {idx}: {e}")
                                continue

                            # Create WKT representation of the point geometry
                            # Rounding to reduce precision
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
                            logger.debug(f"Added station {station.station_key} to session")  # Log station key

                            # Commit in smaller batches to avoid memory issues
                            if stations_count % 500 == 0:
                                session.commit()
                                print(f"Committed {stations_count} stations")
                                logger.info(f"Committed {stations_count} stations")
                                
                        except Exception as row_error:
                            logger.error(f"Error processing station record {idx}: {row_error}")
                            print(f"Error processing station record {idx}: {row_error}")
                            session.rollback()  # Rollback on individual row error
                            continue

                    # Final commit for remaining records
                    session.commit()
                    print(f"Successfully imported {stations_count} stations")
                    logger.info(f"Imported {stations_count} stations")
                    
                except Exception as e:
                    error_msg = f"Error during station data import: {str(e)}"
                    print(f"\nERROR: {error_msg}")
                    logger.error(error_msg)
                    session.rollback()
                    raise

                print("\nUpdating station geometries...")
                logger.info("Updating station geometries")
                try:
                    for station in session.query(Station).filter(Station.location_geom == None).all():
                        try:
                            # Ensure latitude and longitude are valid floats
                            latitude = float(station.wgs84_latitude)
                            longitude = float(station.wgs84_longitude)

                            # Create WKT representation of the point geometry
                            wkt_point = f"POINT({round(longitude, 6)} {round(latitude, 6)})"
                            station.location_geom = WKTElement(wkt_point, srid=4326)
                            
                        except (ValueError, TypeError) as e:
                            logger.error(f"Invalid lat/lon for station {station.station_key}: {e}")
                            continue  # Skip to the next station

                    session.commit()
                    print("Station geometries updated successfully")
                    logger.info("Station geometries updated successfully")
                except SQLAlchemyError as e:
                    error_msg = f"SQLAlchemy error during geometry update: {str(e)}"
                    print(f"\nERROR: {error_msg}")
                    logger.error(error_msg)
                    session.rollback()

                print("\nDatabase initialization completed successfully!")
                logger.info("Database initialization completed successfully")

            except SQLAlchemyError as e:
                error_msg = f"SQLAlchemy error during data import: {str(e)}"
                print(f"\nERROR: {error_msg}")
                logger.error(error_msg)
                session.rollback()
            except Exception as e:
                error_msg = f"Error during data import: {str(e)}"
                print(f"\nERROR: {error_msg}")
                logger.error(error_msg)
                session.rollback()
            finally:
                session.close()

    except SQLAlchemyError as e:
        error_msg = f"SQLAlchemy error during database operations: {str(e)}"
        print(f"\nCRITICAL ERROR: {error_msg}")
        logger.critical(error_msg)
    except Exception as e:
        error_msg = f"Fatal error during database initialization: {str(e)}"
        print(f"\nCRITICAL ERROR: {error_msg}")
        logger.critical(error_msg)
    finally:
        engine.dispose()
        logger.info("Database engine disposed")

if __name__ == '__main__':
    init_db()
