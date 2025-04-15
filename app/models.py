# app/models.py
# This file defines Python classes that map directly to your 
# PostgreSQL tables using SQLAlchemy's ORM (Object Relational Mapper). 
# We use the modern SQLAlchemy 2.0 style syntax.

import datetime
from sqlalchemy import (
    create_engine, Integer, String, Float, Boolean, Date, ForeignKey, MetaData
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import GEOMETRY # Use PostgreSQL specific type

# Define a base class for declarative models
class Base(DeclarativeBase):
    pass

# --- Station Model ---
class Station(Base):
    __tablename__ = 'stations'

    station_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    road_name: Mapped[str] = mapped_column(String, nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    common_road_name: Mapped[str] = mapped_column(String, nullable=True)
    lga: Mapped[str] = mapped_column(String, nullable=True, index=True)
    suburb: Mapped[str] = mapped_column(String, nullable=True, index=True)
    post_code: Mapped[str] = mapped_column(String, nullable=True)
    road_functional_hierarchy: Mapped[str] = mapped_column(String, nullable=True, index=True)
    lane_count: Mapped[str] = mapped_column(String, nullable=True)
    road_classification_type: Mapped[str] = mapped_column(String, nullable=True)
    device_type: Mapped[str] = mapped_column(String, nullable=True)
    permanent_station: Mapped[bool] = mapped_column(Boolean, nullable=True)
    vehicle_classifier: Mapped[bool] = mapped_column(Boolean, nullable=True)
    heavy_vehicle_checking_station: Mapped[bool] = mapped_column(Boolean, nullable=True)
    quality_rating: Mapped[int] = mapped_column(Integer, nullable=True)
    wgs84_latitude: Mapped[float] = mapped_column(Float, nullable=True)
    wgs84_longitude: Mapped[float] = mapped_column(Float, nullable=True)
    # Use GEOMETRY type, specify Point and SRID 4326 (WGS84)
    # Ensure PostGIS extension is enabled in your PostgreSQL database: CREATE EXTENSION postgis;
    location_geom = mapped_column(GEOMETRY(geometry_type='POINT', srid=4326), nullable=True, index=True)

    # Define the relationship to HourlyCount (one station has many counts)
    hourly_counts: Mapped[list["HourlyCount"]] = relationship(back_populates="station")

    def __repr__(self):
        return f"<Station(station_key={self.station_key}, station_id='{self.station_id}', road_name='{self.road_name}')>"

# --- Hourly Count Model ---
class HourlyCount(Base):
    __tablename__ = 'hourly_counts'

    count_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_key: Mapped[int] = mapped_column(ForeignKey('stations.station_key'), index=True)
    traffic_direction_seq: Mapped[int] = mapped_column(Integer, nullable=True)
    cardinal_direction_seq: Mapped[int] = mapped_column(Integer, nullable=True)
    classification_seq: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    count_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=True, index=True) # 1=Mon, 7=Sun
    is_public_holiday: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_school_holiday: Mapped[bool] = mapped_column(Boolean, nullable=True) # Needs external data source usually

    # Map hourly columns
    hour_00: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_01: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_02: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_03: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_04: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_05: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_06: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_07: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_08: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_09: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_10: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_11: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_12: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_13: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_14: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_15: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_16: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_17: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_18: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_19: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_20: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_21: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_22: Mapped[int] = mapped_column(Integer, nullable=True)
    hour_23: Mapped[int] = mapped_column(Integer, nullable=True)
    daily_total: Mapped[int] = mapped_column(Integer, nullable=True)

    # Define the relationship back to Station (many counts belong to one station)
    station: Mapped["Station"] = relationship(back_populates="hourly_counts")

    def __repr__(self):
        return f"<HourlyCount(count_id={self.count_id}, station_key={self.station_key}, date='{self.count_date}', class={self.classification_seq})>"