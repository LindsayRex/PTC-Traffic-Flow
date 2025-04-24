import pytest
from app.models import Station, HourlyCount


def test_station_composite_index_exists():
    """Ensure a composite index on (lga, suburb, road_name) is defined"""
    table = Station.__table__
    index_names = {idx.name: idx for idx in table.indexes}
    # Composite index should be named 'idx_station_composite'
    assert 'idx_station_composite' in index_names
    idx = index_names['idx_station_composite']
    columns = [col.name for col in idx.columns]
    assert set(columns) == {'lga', 'suburb', 'road_name'}


def test_hourlycount_indexes_exist_and_columns():
    """Ensure indexes on HourlyCount match __table_args__ definitions"""
    table = HourlyCount.__table__
    index_names = {idx.name: idx for idx in table.indexes}
    expected_indexes = {
        'ix_hourly_counts_station_key': ['station_key'],
        'ix_hourly_counts_count_date': ['count_date'],
        'ix_hourly_counts_classification_seq': ['classification_seq'],
        'ix_hourly_counts_year': ['year'],
        'ix_hourly_counts_month': ['month'],
        'ix_hourly_counts_day_of_week': ['day_of_week'],
        'idx_hourly_composite': ['station_key', 'count_date', 'classification_seq'],
    }
    for idx_name, cols in expected_indexes.items():
        assert idx_name in index_names, f"Missing index {idx_name}"
        idx = index_names[idx_name]
        column_names = [col.name for col in idx.columns]
        assert column_names == cols

    # Also ensure the index count matches expected
    assert set(index_names.keys()) == set(expected_indexes.keys())
