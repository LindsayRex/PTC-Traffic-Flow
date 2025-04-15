import pandas as pd
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)
from sqlalchemy.orm import sessionmaker
import os
from models import Base, Station, HourlyCount
from datetime import datetime

def ingest_hourly_data():
    # Get database URL from environment or use default
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/traffic_db')

    # Create engine
    engine = create_engine(DATABASE_URL)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Read CSV file
        df = pd.read_csv('/app/data/road_traffic_counts_hourly_sample_0.csv')

        # Process each row
        records_processed = 0

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

        # Final commit
        session.commit()
        print(f"Successfully imported {records_processed} hourly count records")
        return True

    except Exception as e:
        print(f"Error importing data: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == '__main__':
    success = ingest_hourly_data()
    exit(0 if success else 1)