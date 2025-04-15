
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Date, ForeignKey,
    Index, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

Base = declarative_base()

class Station(Base):
    __tablename__ = 'stations'
    
    station_key = Column(Integer, primary_key=True)
    station_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    road_name = Column(String, nullable=False, index=True)
    full_name = Column(String)
    common_road_name = Column(String, index=True)
    lga = Column(String, index=True)
    suburb = Column(String, index=True)
    post_code = Column(String)
    road_functional_hierarchy = Column(String, index=True)
    lane_count = Column(String)
    road_classification_type = Column(String)
    device_type = Column(String)
    permanent_station = Column(Boolean, default=False)
    vehicle_classifier = Column(Boolean, default=False)
    heavy_vehicle_checking_station = Column(Boolean, default=False)
    quality_rating = Column(Integer)
    wgs84_latitude = Column(Float)
    wgs84_longitude = Column(Float)
    location_geom = Column(Geometry('POINT', srid=4326), index=True)

    # Relationship with HourlyCount
    hourly_counts = relationship("HourlyCount", back_populates="station")

class HourlyCount(Base):
    __tablename__ = 'hourly_counts'
    
    count_id = Column(BigInteger, primary_key=True)
    station_key = Column(Integer, ForeignKey('stations.station_key'), nullable=False, index=True)
    traffic_direction_seq = Column(Integer, nullable=False)
    cardinal_direction_seq = Column(Integer)
    classification_seq = Column(Integer, nullable=False, index=True)
    count_date = Column(Date, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False, index=True)
    is_public_holiday = Column(Boolean, default=False)
    is_school_holiday = Column(Boolean, default=False)
    
    # Hourly volume columns
    hour_00 = Column(Integer)
    hour_01 = Column(Integer)
    hour_02 = Column(Integer)
    hour_03 = Column(Integer)
    hour_04 = Column(Integer)
    hour_05 = Column(Integer)
    hour_06 = Column(Integer)
    hour_07 = Column(Integer)
    hour_08 = Column(Integer)
    hour_09 = Column(Integer)
    hour_10 = Column(Integer)
    hour_11 = Column(Integer)
    hour_12 = Column(Integer)
    hour_13 = Column(Integer)
    hour_14 = Column(Integer)
    hour_15 = Column(Integer)
    hour_16 = Column(Integer)
    hour_17 = Column(Integer)
    hour_18 = Column(Integer)
    hour_19 = Column(Integer)
    hour_20 = Column(Integer)
    hour_21 = Column(Integer)
    hour_22 = Column(Integer)
    hour_23 = Column(Integer)
    
    daily_total = Column(Integer)
    
    # Relationship with Station
    station = relationship("Station", back_populates="hourly_counts")

# Create indexes
Index('idx_station_composite', Station.lga, Station.suburb, Station.road_name)
Index('idx_hourly_composite', HourlyCount.station_key, HourlyCount.count_date, 
      HourlyCount.classification_seq)
