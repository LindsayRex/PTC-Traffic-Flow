import pytest
from sqlalchemy import Integer, String, Boolean, Float, Date, BigInteger
from app.models import Station, HourlyCount


def test_tablenames():
    assert Station.__tablename__ == 'stations'
    assert HourlyCount.__tablename__ == 'hourly_counts'


def test_station_columns_exist_with_correct_types():
    table = Station.__table__
    # station_key
    col = table.columns['station_key']
    assert isinstance(col.type, Integer)
    assert col.primary_key

    # station_id
    col = table.columns['station_id']
    assert isinstance(col.type, String)
    assert not col.nullable
    assert col.unique
    assert col.index

    # name
    col = table.columns['name']
    assert isinstance(col.type, String)
    assert not col.nullable

    # road_name
    col = table.columns['road_name']
    assert isinstance(col.type, String)
    assert not col.nullable
    assert col.index

    # location_geom
    col = table.columns['location_geom']
    from geoalchemy2 import Geometry
    assert isinstance(col.type, Geometry)
    assert col.index


def test_hourlycount_columns_exist_with_correct_types():
    table = HourlyCount.__table__
    # count_id
    col = table.columns['count_id']
    assert isinstance(col.type, BigInteger)
    assert col.primary_key

    # station_key FK
    col = table.columns['station_key']
    assert isinstance(col.type, Integer)
    assert not col.nullable
    assert col.index
    # foreign key to stations.station_key
    fks = list(col.foreign_keys)
    assert len(fks) == 1
    assert fks[0].column.table.name == 'stations'
    assert fks[0].column.name == 'station_key'

    # traffic_direction_seq
    col = table.columns['traffic_direction_seq']
    assert isinstance(col.type, Integer)
    assert not col.nullable

    # count_date
    col = table.columns['count_date']
    assert isinstance(col.type, Date)
    assert not col.nullable
    assert col.index

    # multiple hour columns
    for hour in ['hour_00', 'hour_12', 'hour_23']:
        col = table.columns[hour]
        assert isinstance(col.type, BigInteger)

    # daily_total
    col = table.columns['daily_total']
    assert isinstance(col.type, BigInteger)
