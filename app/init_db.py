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
                            if idx % 200 == 0:
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
                                wgs84_latitude=float(row.get('wgs84_latitude', 0)),
                                wgs84_longitude=float(row.get('wgs84_longitude', 0)),
                                location_geom=location_geom
                            )
                            session.add(station)
                            stations_count += 1
                            
                            # Commit in smaller batches to avoid memory issues
                            if stations_count % 200 == 0:
                                session.commit()
                                print(f"Committed {stations_count} stations")
                                
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
                #stmt = text("""
                #    UPDATE stations 
                #    SET location_geom = ST_SetSRID(ST_MakePoint(wgs84_longitude, wgs84_latitude), 4326)
                #    WHERE location_geom IS NULL
                #""")
                #connection.execute(stmt)
                #connection.commit()
                print("Station geometries updated successfully")

                print("\nImporting hourly counts data test data")
                logger.info("Starting hourly counts import")
                df_counts = pd.read_csv('app/data/road_traffic_counts_hourly_sample_0.csv')
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

                    if counts_processed % 200 == 0:
                        print(f"Processed {counts_processed} hourly count records...")
                        logger.info(f"Processed {counts_processed} hourly count records")
                        session.commit()

                session.commit()
                print(f"\nSuccessfully imported {counts_processed} hourly count records")
                logger.info(f"Completed importing {counts_processed} hourly count records")
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
