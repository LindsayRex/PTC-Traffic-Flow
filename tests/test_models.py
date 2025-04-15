import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Station, HourlyCount
from sqlalchemy.exc import IntegrityError
import datetime

# test_models.py
# Unit tests for the models defined in app/models.py using pytest and SQLAlchemy's in-memory SQLite database.


# Create a fixture for the database session
@pytest.fixture
def session():
    # Use an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)  # Create all tables
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)  # Drop all tables after tests

def test_create_station(session):
    # Test creating a Station instance
    station = Station(
        station_id="ST001",
        name="Test Station",
        road_name="Main Road",
        full_name="Test Station on Main Road",
        common_road_name="Main Rd",
        lga="Test LGA",
        suburb="Test Suburb",
        post_code="1234",
        road_functional_hierarchy="Arterial",
        lane_count="2",
        road_classification_type="Urban",
        device_type="Counter",
        permanent_station=True,
        vehicle_classifier=True,
        heavy_vehicle_checking_station=False,
        quality_rating=5,
        wgs84_latitude=-37.8136,
        wgs84_longitude=144.9631,
    )
    session.add(station)
    session.commit()

    # Verify the station was added
    retrieved_station = session.query(Station).filter_by(station_id="ST001").first()
    assert retrieved_station is not None
    assert retrieved_station.name == "Test Station"
    assert retrieved_station.road_name == "Main Road"

def test_create_hourly_count(session):
    # Create a Station instance first
    station = Station(
        station_id="ST002",
        name="Another Station",
        road_name="Second Road",
    )
    session.add(station)
    session.commit()

    # Test creating an HourlyCount instance
    hourly_count = HourlyCount(
        station_key=station.station_key,
        traffic_direction_seq=1,
        cardinal_direction_seq=2,
        classification_seq=3,
        count_date=datetime.date(2023, 1, 1),
        year=2023,
        month=1,
        day_of_week=7,
        is_public_holiday=True,
        is_school_holiday=False,
        hour_00=10,
        hour_01=20,
        daily_total=100,
    )
    session.add(hourly_count)
    session.commit()

    # Verify the hourly count was added
    retrieved_count = session.query(HourlyCount).filter_by(station_key=station.station_key).first()
    assert retrieved_count is not None
    assert retrieved_count.count_date == datetime.date(2023, 1, 1)
    assert retrieved_count.daily_total == 100

def test_relationship_between_station_and_hourly_count(session):
    # Create a Station instance
    station = Station(
        station_id="ST003",
        name="Station with Counts",
        road_name="Third Road",
    )
    session.add(station)
    session.commit()

    # Create HourlyCount instances related to the station
    hourly_count1 = HourlyCount(
        station_key=station.station_key,
        count_date=datetime.date(2023, 1, 2),
        daily_total=200,
    )
    hourly_count2 = HourlyCount(
        station_key=station.station_key,
        count_date=datetime.date(2023, 1, 3),
        daily_total=300,
    )
    session.add_all([hourly_count1, hourly_count2])
    session.commit()

    # Verify the relationship
    retrieved_station = session.query(Station).filter_by(station_id="ST003").first()
    assert len(retrieved_station.hourly_counts) == 2
    assert retrieved_station.hourly_counts[0].daily_total == 200
    assert retrieved_station.hourly_counts[1].daily_total == 300

def test_station_without_required_fields(session):
    # Test creating a Station without required fields
    station = Station()
    session.add(station)
    with pytest.raises(IntegrityError):
        session.commit()