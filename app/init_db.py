
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Station, HourlyCount
import pandas as pd
from geoalchemy2.functions import ST_MakePoint
from sqlalchemy.sql import text

def init_db():
    # Get database URL from environment or use default
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/traffic_db')
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Enable PostGIS
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

    # Create tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Load station reference data
        df_stations = pd.read_csv('app/data/road_traffic_counts_station_reference.csv')
        
        # Transform and insert stations
        for _, row in df_stations.iterrows():
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
        
        # Commit the changes
        session.commit()
        print("Successfully imported station data")
        
    except Exception as e:
        print(f"Error importing data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    init_db()
