"""
Database models for the PTC Traffic Flow application.

This module defines the SQLAlchemy ORM models that represent the database schema.
For file path operations related to these models (such as data import/export),
use the path utilities from app.utils.path_utils.
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Date, ForeignKey,
    Index, BigInteger
)
from sqlalchemy.orm import relationship, declarative_base
from geoalchemy2 import Geometry
from app.utils.path_utils import get_data_path, normalize_path

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
    hour_00 = Column(BigInteger)
    hour_01 = Column(BigInteger)
    hour_02 = Column(BigInteger)
    hour_03 = Column(BigInteger)
    hour_04 = Column(BigInteger)
    hour_05 = Column(BigInteger)
    hour_06 = Column(BigInteger)
    hour_07 = Column(BigInteger)
    hour_08 = Column(BigInteger)
    hour_09 = Column(BigInteger)
    hour_10 = Column(BigInteger)
    hour_11 = Column(BigInteger)
    hour_12 = Column(BigInteger)
    hour_13 = Column(BigInteger)
    hour_14 = Column(BigInteger)
    hour_15 = Column(BigInteger)
    hour_16 = Column(BigInteger)
    hour_17 = Column(BigInteger)
    hour_18 = Column(BigInteger)
    hour_19 = Column(BigInteger)
    hour_20 = Column(BigInteger)
    hour_21 = Column(BigInteger)
    hour_22 = Column(BigInteger)
    hour_23 = Column(BigInteger)
    
    daily_total = Column(BigInteger)
    
    # Relationship with Station
    station = relationship("Station", back_populates="hourly_counts")

    # Add indexes if desired (optional, but good practice to match DB)
    __table_args__ = (
        Index('ix_hourly_counts_station_key', 'station_key'),
        Index('ix_hourly_counts_count_date', 'count_date'),
        Index('ix_hourly_counts_classification_seq', 'classification_seq'),
        Index('ix_hourly_counts_year', 'year'),
        Index('ix_hourly_counts_month', 'month'),
        Index('ix_hourly_counts_day_of_week', 'day_of_week'),
        Index('idx_hourly_composite', 'station_key', 'count_date', 'classification_seq'),
    )

# Create indexes
Index('idx_station_composite', Station.lga, Station.suburb, Station.road_name)
