import pytest
from sqlalchemy import inspect
from app.models import Station, HourlyCount


def test_station_hourly_counts_relationship():
    """Station.hourly_counts is a one-to-many relationship back_populates='station'"""
    station_rel = inspect(Station).relationships.get('hourly_counts')
    assert station_rel is not None
    assert station_rel.mapper.class_ is HourlyCount
    assert station_rel.direction.name == 'ONETOMANY'
    assert station_rel.back_populates == 'station'


def test_hourlycount_station_relationship():
    """HourlyCount.station is a many-to-one relationship back_populates='hourly_counts'"""
    count_rel = inspect(HourlyCount).relationships.get('station')
    assert count_rel is not None
    assert count_rel.mapper.class_ is Station
    assert count_rel.direction.name == 'MANYTOONE'
    assert count_rel.back_populates == 'hourly_counts'


def test_relationship_assignment_bidirectional():
    """Assigning via one side populates the other side as expected"""
    s = Station(station_key=123)
    hc = HourlyCount(count_id=456)

    # assign from parent side
    s.hourly_counts = [hc]
    assert hc.station is s
    # assign from child side
    hc2 = HourlyCount(count_id=789)
    hc2.station = s
    assert hc2 in s.hourly_counts
