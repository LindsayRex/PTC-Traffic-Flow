"""
Tests for database query-related functions in db_utils.py.

This module focuses on testing the following functions:
- get_all_station_metadata()
- get_station_details()
- get_latest_data_date()
- get_hourly_data_for_stations()
- get_distinct_values()
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Mock streamlit and other dependencies BEFORE importing the module under test
mock_st = MagicMock()
mock_st.cache_data = lambda func: func  # Mock streamlit cache decorator
mock_st.cache_resource = lambda func: func  # Mock streamlit cache decorator

# Create mock classes for models
class MockStation:
    pass

class MockHourlyCount:
    pass

# Mock the models module
mock_models = MagicMock()
mock_models.Station = MockStation
mock_models.HourlyCount = MockHourlyCount

# Set up module mocks
modules = {
    'streamlit': mock_st,
    'app.models': mock_models
}

# Apply mocks using patch.dict before importing the module under test
with patch.dict(sys.modules, modules):
    from app.db_utils import (
        get_all_station_metadata,
        get_station_details,
        get_latest_data_date,
        get_hourly_data_for_stations,
        get_distinct_values
    )


class MockQuery:
    """Mock class for simulating SQLAlchemy query objects."""
    
    def __init__(self, results=None):
        self.results = results if results is not None else []
        self.filters = []
        self.statement = "MOCK SQL STATEMENT"
    
    def filter(self, *args):
        self.filters.extend(args)
        return self
    
    def first(self):
        return self.results[0] if self.results else None
    
    def all(self):
        return self.results
    
    def scalar(self):
        return self.results[0] if self.results else None


class TestDbQueries(unittest.TestCase):
    """Tests for database query functions."""

    def setUp(self):
        """Set up test environment before each test."""
        self.mock_session = MagicMock(spec=Session)
        self.mock_session.bind = MagicMock()
        
        # Create sample station objects
        self.sample_stations = [
            Mock(
                station_key=1,
                station_id="ST001",
                name="Station 1",
                road_name="Main Road",
                full_name="Station 1 on Main Road",
                lga="City Council",
                suburb="Downtown"
            ),
            Mock(
                station_key=2,
                station_id="ST002",
                name="Station 2",
                road_name="Highway Ave",
                full_name="Station 2 on Highway Ave",
                lga="County Council",
                suburb="Uptown"
            )
        ]
        
        # Create sample hourly count objects
        self.sample_hourly_counts = [
            Mock(
                count_id=1,
                station_key=1,
                traffic_direction_seq=1,
                classification_seq=1,
                count_date=datetime.date(2025, 4, 1),
                daily_total=1000,
                hour_08=120,
                hour_17=150
            ),
            Mock(
                count_id=2,
                station_key=1,
                traffic_direction_seq=2,
                classification_seq=1,
                count_date=datetime.date(2025, 4, 1),
                daily_total=900,
                hour_08=100,
                hour_17=130
            )
        ]

    def test_get_all_station_metadata_successful(self):
        """Test successful retrieval of all station metadata."""
        # Arrange
        expected_df = pd.DataFrame({
            'station_key': [1, 2],
            'station_id': ['ST001', 'ST002'],
            'name': ['Station 1', 'Station 2']
        })
        with patch("pandas.read_sql", return_value=expected_df):
            self.mock_session.query.return_value = MockQuery(self.sample_stations)
            
            # Act
            result = get_all_station_metadata(self.mock_session)
            
            # Assert
            self.assertIsInstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, expected_df)
            self.mock_session.query.assert_called_once_with(MockStation)
    
    def test_get_all_station_metadata_none_session(self):
        """Test handling of None session."""
        # Act
        result = get_all_station_metadata(None)
        
        # Assert
        self.assertIsNone(result)
    
    def test_get_all_station_metadata_exception_handled(self):
        """Test handling of exceptions during data retrieval."""
        # Arrange
        with patch("pandas.read_sql", side_effect=Exception("Test error")):
            self.mock_session.query.return_value = MockQuery()
            
            # Act
            result = get_all_station_metadata(self.mock_session)
            
            # Assert
            self.assertIsNone(result)
            self.mock_session.query.assert_called_once_with(MockStation)

    def test_get_station_details_successful(self):
        """Test successful retrieval of station details."""
        # Arrange
        station_key = 1
        expected_station = self.sample_stations[0]
        mock_query = MockQuery([expected_station])
        self.mock_session.query.return_value = mock_query
        
        # Act
        result = get_station_details(self.mock_session, station_key)
        
        # Assert
        self.assertEqual(result, expected_station)
        self.mock_session.query.assert_called_once_with(MockStation)
    
    def test_get_station_details_none_session(self):
        """Test handling of None session."""
        # Act
        result = get_station_details(None, 1)
        
        # Assert
        self.assertIsNone(result)
    
    def test_get_station_details_not_found(self):
        """Test handling when station is not found."""
        # Arrange
        station_key = 999
        mock_query = MockQuery([])
        self.mock_session.query.return_value = mock_query
        
        # Act
        result = get_station_details(self.mock_session, station_key)
        
        # Assert
        self.assertIsNone(result)
        self.mock_session.query.assert_called_once_with(MockStation)
    
    def test_get_station_details_exception_handled(self):
        """Test handling of exceptions during data retrieval."""
        # Arrange
        station_key = 1
        self.mock_session.query.side_effect = Exception("Test error")
        
        # Act
        result = get_station_details(self.mock_session, station_key)
        
        # Assert
        self.assertIsNone(result)
        self.mock_session.query.assert_called_once_with(MockStation)

    def test_get_latest_data_date_successful(self):
        """Test successful retrieval of latest data date."""
        # Arrange
        station_key = 1
        direction = 1
        expected_date = datetime.date(2025, 4, 15)
        mock_query = MagicMock()
        mock_query.scalar.return_value = expected_date
        self.mock_session.query.return_value.filter.return_value = mock_query
        
        # Act
        result = get_latest_data_date(self.mock_session, station_key, direction)
        
        # Assert
        self.assertEqual(result, expected_date)
        self.mock_session.query.assert_called_once()
        self.mock_session.query.return_value.filter.assert_called_once()
    
    def test_get_latest_data_date_none_session(self):
        """Test handling of None session."""
        # Act
        result = get_latest_data_date(None, 1, 1)
        
        # Assert
        self.assertIsNone(result)
    
    def test_get_latest_data_date_exception_handled(self):
        """Test handling of exceptions during data retrieval."""
        # Arrange
        station_key = 1
        direction = 1
        self.mock_session.query.side_effect = Exception("Test error")
        
        # Act
        result = get_latest_data_date(self.mock_session, station_key, direction)
        
        # Assert
        self.assertIsNone(result)
        self.mock_session.query.assert_called_once()

    def test_get_hourly_data_for_stations_successful(self):
        """Test successful retrieval of hourly data for stations."""
        # Arrange
        station_keys = [1]
        start_date = datetime.date(2025, 4, 1)
        end_date = datetime.date(2025, 4, 15)
        directions = [1]
        expected_df = pd.DataFrame({
            'count_id': [1],
            'station_key': [1],
            'traffic_direction_seq': [1],
            'daily_total': [1000]
        })
        with patch("pandas.read_sql", return_value=expected_df):
            self.mock_session.query.return_value.filter.return_value = MockQuery(self.sample_hourly_counts)
            
            # Act
            result = get_hourly_data_for_stations(self.mock_session, station_keys, start_date, end_date, directions)
            
            # Assert
            self.assertIsInstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, expected_df)
            self.mock_session.query.assert_called_once_with(MockHourlyCount)
    
    def test_get_hourly_data_for_stations_none_session(self):
        """Test handling of None session."""
        # Act
        result = get_hourly_data_for_stations(
            None, [1], datetime.date(2025, 4, 1), datetime.date(2025, 4, 15)
        )
        
        # Assert
        self.assertIsNone(result)
    
    def test_get_hourly_data_for_stations_with_all_directions(self):
        """Test handling when directions include both 1, 2 and 3."""
        # Arrange
        station_keys = [1]
        start_date = datetime.date(2025, 4, 1)
        end_date = datetime.date(2025, 4, 15)
        directions = [1, 2, 3]
        empty_df = pd.DataFrame()
        with patch("pandas.read_sql", return_value=empty_df):
            # Act
            result = get_hourly_data_for_stations(self.mock_session, station_keys, start_date, end_date, directions)
            
            # Assert
            self.assertIsInstance(result, pd.DataFrame)
            self.mock_session.query.assert_called_once_with(MockHourlyCount)
    
    def test_get_hourly_data_for_stations_exception_handled(self):
        """Test handling of exceptions during data retrieval."""
        # Arrange
        station_keys = [1]
        start_date = datetime.date(2025, 4, 1)
        end_date = datetime.date(2025, 4, 15)
        with patch("pandas.read_sql", side_effect=Exception("Test error")):
            # Act
            result = get_hourly_data_for_stations(self.mock_session, station_keys, start_date, end_date)
            
            # Assert
            self.assertIsInstance(result, pd.DataFrame)
            self.assertTrue(result.empty)
            self.mock_session.query.assert_called_once_with(MockHourlyCount)

    def test_get_distinct_values_successful(self):
        """Test successful retrieval of distinct values."""
        # Arrange
        column_name = "lga"
        expected_values = ["City Council", "County Council"]
        mock_execute = MagicMock()
        mock_execute.scalars.return_value.all.return_value = expected_values
        self.mock_session.execute.return_value = mock_execute
        
        # Act
        result = get_distinct_values(self.mock_session, column_name)
        
        # Assert
        self.assertEqual(result, expected_values)
        self.mock_session.execute.assert_called_once()
    
    def test_get_distinct_values_none_session(self):
        """Test handling of None session."""
        # Act
        result = get_distinct_values(None, "lga")
        
        # Assert
        self.assertIsNone(result)
    
    def test_get_distinct_values_invalid_column(self):
        """Test handling of invalid column name."""
        # Arrange
        column_name = "invalid_column"
        
        # Act
        result = get_distinct_values(self.mock_session, column_name)
        
        # Assert
        self.assertIsNone(result)
        self.mock_session.execute.assert_not_called()
    
    def test_get_distinct_values_exception_handled(self):
        """Test handling of exceptions during data retrieval."""
        # Arrange
        column_name = "lga"
        self.mock_session.execute.side_effect = Exception("Test error")
        
        # Act
        result = get_distinct_values(self.mock_session, column_name)
        
        # Assert
        self.assertIsNone(result)
        self.mock_session.execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()