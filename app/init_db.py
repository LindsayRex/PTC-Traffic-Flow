
import os
import datetime
import logging

logger = logging.getLogger(__name__)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, Station, HourlyCount
import pandas as pd
from geoalchemy2.functions import ST_MakePoint

def init_db():
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/traffic_db')
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Load station reference data
        df_stations = pd.read_csv('app/data/road_traffic_counts_station_reference.csv')
        
        # Transform and insert stations
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

        session.commit()
        
        # Update geometries
        stmt = text("""
            UPDATE stations 
            SET location_geom = ST_SetSRID(ST_MakePoint(wgs84_longitude, wgs84_latitude), 4326)
            WHERE location_geom IS NULL
        """)
        session.execute(stmt)
        session.commit()

        # Load hourly counts data
        df_counts = pd.read_csv('app/data/hourly_counts.csv')
        
        # Process and insert hourly counts with calculations
        for _, row in df_counts.iterrows():
            count_date = pd.to_datetime(row['count_date']).date()
            
            # Calculate peaks (AM: 06-09, PM: 15-18)
            am_peak = sum(row.get(f'hour_{str(h).zfill(2)}', 0) for h in range(6, 10))
            pm_peak = sum(row.get(f'hour_{str(h).zfill(2)}', 0) for h in range(15, 19))
            
            # Calculate daily total
            hour_cols = [f'hour_{str(h).zfill(2)}' for h in range(24)]
            daily_total = sum(row.get(col, 0) for col in hour_cols)
            
            # Check data quality (at least 19 hours of data)
            valid_hours = sum(1 for col in hour_cols if row.get(col) is not None)
            
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
                is_school_holiday=bool(row.get('is_school_holiday', False)),
                daily_total=daily_total if valid_hours >= 19 else None
            )
            
            # Add hourly values
            for hour in range(24):
                hour_col = f'hour_{str(hour).zfill(2)}'
                setattr(count, hour_col, row.get(hour_col, 0))
            
            session.add(count)
            
        session.commit()
        print("Successfully imported station and hourly count data with calculations")
        
    except Exception as e:
        print(f"Error importing data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    init_db()
