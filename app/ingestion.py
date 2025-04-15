import pandas as pd
import logging
from log_config import setup_logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from models import Base, Station, HourlyCount
from datetime import datetime
from db_utils import get_db_session  # Import the context manager

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def ingest_hourly_data():
    """Ingests hourly traffic data from a CSV file into the database."""

    try:
        # Read CSV file using relative path
        df = pd.read_csv('./app/data/road_traffic_counts_hourly_sample_0.csv', low_memory=False)

        # Process each row
        records_processed = 0

        with get_db_session() as session:  # Use the context manager
            if session is None:
                logger.error("Failed to get database session.")
                print("Failed to get database session. Check logs.")
                return False

            try:
                for _, row in df.iterrows():
                    # Convert date string to datetime
                    count_date = pd.to_datetime(row['date']).date()

                    # Create HourlyCount object
                    count = HourlyCount(
                        station_key=row['station_key'],
                        traffic_direction_seq=row['traffic_direction_seq'],
                        cardinal_direction_seq=row.get('cardinal_direction_seq'),
                        classification_seq=row['classification_seq'],
                        count_date=count_date,
                        year=count_date.year,
                        month=count_date.month,
                        day_of_week=count_date.isoweekday(),
                        is_public_holiday=bool(row.get('public_holiday', False)),
                        is_school_holiday=bool(row.get('school_holiday', False))
                    )

                    # Add hourly values
                    for hour in range(24):
                        hour_col = f'hour_{str(hour).zfill(2)}'
                        setattr(count, hour_col, row.get(hour_col, 0))

                    # Calculate daily total
                    hour_cols = [f'hour_{str(h).zfill(2)}' for h in range(24)]
                    count.daily_total = sum(row.get(col, 0) for col in hour_cols)

                    session.add(count)
                    records_processed += 1

                    # Commit in batches of 1000
                    if records_processed % 1000 == 0:
                        session.commit()
                        print(f"Processed {records_processed} records...")
                        logger.info(f"Processed {records_processed} records")

                # Final commit
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
