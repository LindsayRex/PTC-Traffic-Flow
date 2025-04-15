
import os
from sqlalchemy import create_engine
from models import Base, Station, HourlyCount
import pandas as pd
from geoalchemy2.functions import ST_MakePoint
from sqlalchemy.sql import text

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL', 'holy-dream-78726213')

def init_db():
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Enable PostGIS
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

    # Create tables
    Base.metadata.create_all(engine)
    
    # Load station reference data
    df_stations = pd.read_csv('app/data/road_traffic_counts_station_reference.csv')
    
    # Transform data for database insertion
    stations_data = []
    for _, row in df_stations.iterrows():
        station = {
            'station_id': row['station_id'],
            'name': row['name'],
            'road_name': row['road_name'],
            'lga': row['lga'],
            'suburb': row['suburb'],
            'road_functional_hierarchy': row['road_functional_hierarchy'],
            'permanent_station': row.get('permanent_station', False),
            'vehicle_classifier': row.get('vehicle_classifier', False),
            'wgs84_latitude': row['latitude'],
            'wgs84_longitude': row['longitude'],
        }
        stations_data.append(station)
    
    # Insert stations
    df_stations_clean = pd.DataFrame(stations_data)
    df_stations_clean.to_sql('stations', engine, if_exists='append', index=False)

if __name__ == '__main__':
    init_db()
