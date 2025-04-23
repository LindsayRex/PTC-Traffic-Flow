import unittest
from unittest.mock import patch, MagicMock, ANY, call
import sys
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, SAWarning  # Add SAWarning import
import datetime
import logging
import warnings  # Add warnings import

# --- Suppress GeoAlchemy2 GenericFunction registration warnings ---
# These warnings occur because the test runner might load modules (like db_utils
# which imports models using GeoAlchemy2) multiple times, causing GeoAlchemy2
# to try and register its spatial functions repeatedly. This is generally
# harmless in the test context but clutters the output.
# Note: conftest.py should handle this globally, but adding here as a backup
warnings.filterwarnings('ignore',
                        r"The GenericFunction '.*' is already registered and is going to be overridden.",
                        SAWarning)
# --- End Warning Suppression ---

# --- Mock Streamlit globally BEFORE importing db_utils ---
mock_st = MagicMock()
mock_st.stop.side_effect = SystemExit
# Provide a default secrets structure
mock_st.secrets = {
    "environment": {
        "DATABASE_URL": "mock_db_url_string"
    }
}
# Mock cache decorators to just run the function
mock_st.cache_resource = lambda func: func
mock_st.cache_data = lambda func: func

# Use patch.dict to insert mocks into sys.modules
modules_to_patch = {
    'streamlit': mock_st,
    # We don't mock logging globally here, patch getLogger specifically per test if needed
}

# Apply mocks using patch.dict before importing the app
# This ensures the app imports the mocks, not the real modules
with patch.dict(sys.modules, modules_to_patch):
    # --- Now import the module under test ---
    from app import db_utils
    from app.models import Station, HourlyCount # Import models needed for tests

# Mock logger at the module level for convenience in patching later
mock_logger = MagicMock(spec=logging.Logger)

class TestDbOperations(unittest.TestCase): # Renamed class

    def setUp(self):
        """Reset mocks before each test."""
        mock_st.reset_mock()
        mock_logger.reset_mock()

        # Ensure secrets are reset if modified by a test
        mock_st.secrets = {
            "environment": {
                "DATABASE_URL": "mock_db_url_string"
            }
        }
        mock_st.stop.side_effect = SystemExit # Reset side effect if needed

    # === Test get_all_station_metadata ===

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('pandas.read_sql')
    def test_get_all_station_metadata_success(self, mock_read_sql_pandas):
        """Test get_all_station_metadata success."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        # Simulate the statement attribute used by read_sql
        mock_query.statement = "mock_statement_all_stations"
        # Simulate the bind attribute used by read_sql
        mock_session.bind = "mock_bind_all_stations"
        expected_df = pd.DataFrame({'station_key': [1, 2], 'name': ['A', 'B']})
        mock_read_sql_pandas.return_value = expected_df

        # Call the function directly (mocked decorator runs it)
        # Pass the mock session as the argument (named _session in the function)
        df = db_utils.get_all_station_metadata(mock_session)

        mock_session.query.assert_called_once_with(Station)
        mock_read_sql_pandas.assert_called_once_with(mock_query.statement, mock_session.bind)
        pd.testing.assert_frame_equal(df, expected_df)
        mock_logger.info.assert_any_call("Querying all station metadata.")
        mock_logger.info.assert_any_call(f"Successfully fetched {len(df)} station metadata records.")
        mock_st.error.assert_not_called()

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('pandas.read_sql')
    def test_get_all_station_metadata_session_none(self, mock_read_sql_pandas):
        """Test get_all_station_metadata with None session."""
        # Call the function directly
        df = db_utils.get_all_station_metadata(None)

        self.assertIsNone(df)
        mock_logger.error.assert_called_once_with("Database session is None in get_all_station_metadata.")
        mock_read_sql_pandas.assert_not_called()

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('pandas.read_sql', side_effect=Exception("DB Read Error"))
    def test_get_all_station_metadata_exception(self, mock_read_sql_pandas):
        """Test get_all_station_metadata handles exceptions."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.statement = "mock_statement_all_stations_err"
        mock_session.bind = "mock_bind_all_stations_err"

        # Call the function directly
        df = db_utils.get_all_station_metadata(mock_session)

        self.assertIsNone(df)
        mock_session.query.assert_called_once_with(Station)
        mock_read_sql_pandas.assert_called_once_with(mock_query.statement, mock_session.bind)
        mock_logger.error.assert_called_once_with("Error fetching all station metadata: DB Read Error", exc_info=True)
        mock_st.error.assert_called_once_with("Failed to load station metadata from database.")

    # === Test get_station_details ===

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_station_details_success(self):
        """Test get_station_details success."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_station_instance = MagicMock(spec=Station, name="FoundStation")
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_station_instance
        station_key = 123

        # Call the function directly
        station = db_utils.get_station_details(mock_session, station_key)

        mock_session.query.assert_called_once_with(Station)
        # Check that filter was called (more specific check on args is complex)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
        self.assertEqual(station, mock_station_instance)
        mock_logger.info.assert_any_call(f"Querying details for station_key: {station_key}")
        mock_logger.info.assert_any_call(f"Successfully fetched details for station_key: {station_key}")
        mock_st.error.assert_not_called()

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_station_details_not_found(self):
        """Test get_station_details when station is not found."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None # Simulate not found
        station_key = 404

        # Call the function directly
        station = db_utils.get_station_details(mock_session, station_key)

        self.assertIsNone(station)
        mock_session.query.assert_called_once_with(Station)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
        mock_logger.warning.assert_called_once_with(f"No station found with key: {station_key}")
        mock_st.error.assert_not_called()

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_station_details_session_none(self):
        """Test get_station_details with None session."""
        # Call the function directly
        station = db_utils.get_station_details(None, 123)
        self.assertIsNone(station)
        mock_logger.error.assert_called_once_with("Database session is None in get_station_details.")

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_station_details_exception(self):
        """Test get_station_details handles exceptions during query."""
        mock_session = MagicMock(spec=Session)
        # Simulate exception on the query call
        mock_session.query.side_effect = Exception("DB Query Error Station")
        station_key = 500

        # Call the function directly
        station = db_utils.get_station_details(mock_session, station_key)

        self.assertIsNone(station)
        mock_session.query.assert_called_once_with(Station)
        mock_logger.error.assert_called_once_with(f"Error fetching station details for key {station_key}: DB Query Error Station", exc_info=True)
        mock_st.error.assert_called_once_with(f"Failed to load details for station {station_key}.")

    # === Test get_latest_data_date ===

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('sqlalchemy.func') # Patch func used within the function
    def test_get_latest_data_date_success(self, mock_sql_func):
        """Test get_latest_data_date success."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        expected_date = datetime.date(2024, 1, 1)
        mock_filter.scalar.return_value = expected_date # Simulate scalar result

        # Mock the specific func call (e.g., func.max)
        mock_max_obj = MagicMock(name="max_func_result")
        mock_sql_func.max.return_value = mock_max_obj

        station_key = 1
        direction = 2

        # Call the function directly
        latest_date = db_utils.get_latest_data_date(mock_session, station_key, direction)

        # Check that session.query was called with the result of func.max
        mock_session.query.assert_called_once_with(mock_max_obj)
        # Check that func.max was called with the correct column
        mock_sql_func.max.assert_called_once_with(HourlyCount.count_date)
        mock_query.filter.assert_called_once() # Check filter applied
        mock_filter.scalar.assert_called_once() # Check scalar was called
        self.assertEqual(latest_date, expected_date)
        mock_logger.info.assert_any_call(f"Querying latest data date for station {station_key}, direction {direction}")
        mock_logger.info.assert_any_call(f"Latest data date found: {expected_date}")
        mock_st.error.assert_not_called()

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('sqlalchemy.func')
    def test_get_latest_data_date_none_found(self, mock_sql_func):
        """Test get_latest_data_date when no date is found."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.scalar.return_value = None # Simulate no date found
        mock_max_obj = MagicMock(name="max_func_result")
        mock_sql_func.max.return_value = mock_max_obj
        station_key = 1
        direction = 2

        # Call the function directly
        latest_date = db_utils.get_latest_data_date(mock_session, station_key, direction)

        self.assertIsNone(latest_date)
        mock_session.query.assert_called_once_with(mock_max_obj)
        mock_sql_func.max.assert_called_once_with(HourlyCount.count_date)
        mock_query.filter.assert_called_once()
        mock_filter.scalar.assert_called_once()
        mock_logger.info.assert_any_call(f"Latest data date found: {None}")

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_latest_data_date_session_none(self):
        """Test get_latest_data_date with None session."""
        # Call the function directly
        latest_date = db_utils.get_latest_data_date(None, 1, 2)
        self.assertIsNone(latest_date)
        mock_logger.error.assert_called_once_with("Database session is None in get_latest_data_date.")

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_latest_data_date_exception(self):
        """Test get_latest_data_date handles exceptions."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.side_effect = Exception("DB Query Error Latest Date")
        station_key = 1
        direction = 2

        # Call the function directly
        latest_date = db_utils.get_latest_data_date(mock_session, station_key, direction)

        self.assertIsNone(latest_date)
        mock_session.query.assert_called_once() # Query object creation fails
        mock_logger.error.assert_called_once_with(f"Error fetching latest data date for station {station_key}: DB Query Error Latest Date", exc_info=True)
        mock_st.error.assert_called_once_with("Failed to determine latest data date.")

    # === Test get_hourly_data_for_stations ===

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('pandas.read_sql')
    def test_get_hourly_data_for_stations_success(self, mock_read_sql_pandas):
        """Test get_hourly_data_for_stations success with basic filters."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_filter_base = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter_base # First filter call
        mock_filter_base.statement = "mock_statement_hourly"
        mock_session.bind = "mock_bind_hourly"
        expected_df = pd.DataFrame({'hour': [1, 2], 'count': [10, 20]})
        mock_read_sql_pandas.return_value = expected_df

        station_keys = [1, 2]
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 1, 5)

        # Call the function directly
        df = db_utils.get_hourly_data_for_stations(mock_session, station_keys, start_date, end_date)

        mock_session.query.assert_called_once_with(HourlyCount)
        mock_query.filter.assert_called_once() # Base filter called
        # Ensure the second filter (for direction) was NOT called
        mock_filter_base.filter.assert_not_called()
        mock_read_sql_pandas.assert_called_once_with(mock_filter_base.statement, mock_session.bind)
        pd.testing.assert_frame_equal(df, expected_df)
        mock_logger.info.assert_any_call(f"Querying hourly data for stations {station_keys} from {start_date} to {end_date}")
        mock_logger.info.assert_any_call(f"Successfully fetched {len(df)} hourly records.")
        mock_st.error.assert_not_called()

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('pandas.read_sql')
    def test_get_hourly_data_for_stations_with_directions(self, mock_read_sql_pandas):
        """Test get_hourly_data_for_stations success with direction filter."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_filter_base = MagicMock()
        mock_filter_dir = MagicMock() # Result of the second filter
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter_base # First filter
        mock_filter_base.filter.return_value = mock_filter_dir # Second filter (direction)
        mock_filter_dir.statement = "mock_statement_hourly_dir" # Statement from final query obj
        mock_session.bind = "mock_bind_hourly_dir"
        expected_df = pd.DataFrame({'hour': [1], 'count': [10]})
        mock_read_sql_pandas.return_value = expected_df

        station_keys = [1]
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 1, 5)
        directions = [1, 2] # Not including 3

        # Call the function directly
        df = db_utils.get_hourly_data_for_stations(mock_session, station_keys, start_date, end_date, directions=directions)

        mock_session.query.assert_called_once_with(HourlyCount)
        mock_query.filter.assert_called_once() # Base filter
        mock_filter_base.filter.assert_called_once() # Direction filter
        mock_read_sql_pandas.assert_called_once_with(mock_filter_dir.statement, mock_session.bind)
        pd.testing.assert_frame_equal(df, expected_df)

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('pandas.read_sql')
    def test_get_hourly_data_for_stations_with_direction_both(self, mock_read_sql_pandas):
        """Test get_hourly_data_for_stations ignores direction filter for 'Both' (3)."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_filter_base = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter_base
        mock_filter_base.statement = "mock_statement_hourly_both" # Statement comes from the base filter
        mock_session.bind = "mock_bind_hourly_both"
        expected_df = pd.DataFrame({'hour': [1, 2], 'count': [10, 20]})
        mock_read_sql_pandas.return_value = expected_df

        station_keys = [1]
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 1, 5)
        directions = [3] # Contains 3

        # Call the function directly
        df = db_utils.get_hourly_data_for_stations(mock_session, station_keys, start_date, end_date, directions=directions)

        mock_session.query.assert_called_once_with(HourlyCount)
        mock_query.filter.assert_called_once() # Base filter called
        mock_filter_base.filter.assert_not_called() # Direction filter NOT called
        mock_read_sql_pandas.assert_called_once_with(mock_filter_base.statement, mock_session.bind)
        pd.testing.assert_frame_equal(df, expected_df)

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('pandas.read_sql')
    def test_get_hourly_data_for_stations_session_none(self, mock_read_sql_pandas):
        """Test get_hourly_data_for_stations with None session."""
        # Call the function directly
        df = db_utils.get_hourly_data_for_stations(None, [1], None, None)

        self.assertIsNone(df) # Function should return None if session is None
        mock_logger.error.assert_called_once_with("Database session is None in get_hourly_data_for_stations.")
        mock_read_sql_pandas.assert_not_called()

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('pandas.read_sql', side_effect=Exception("DB Read Error Hourly"))
    def test_get_hourly_data_for_stations_exception(self, mock_read_sql_pandas):
        """Test get_hourly_data_for_stations handles exceptions."""
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_filter_base = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter_base
        mock_filter_base.statement = "mock_statement_hourly_err"
        mock_session.bind = "mock_bind_hourly_err"

        station_keys = [1, 2]
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 1, 5)

        # Call the function directly
        df = db_utils.get_hourly_data_for_stations(mock_session, station_keys, start_date, end_date)

        # The function returns an empty DataFrame on exception
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        mock_session.query.assert_called_once_with(HourlyCount)
        mock_query.filter.assert_called_once()
        mock_read_sql_pandas.assert_called_once_with(mock_filter_base.statement, mock_session.bind)
        mock_logger.error.assert_called_once_with("Error fetching hourly data: DB Read Error Hourly", exc_info=True)
        mock_st.error.assert_called_once_with("Failed to load hourly traffic data.")

    # === Test get_distinct_values ===

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_distinct_values_success(self):
        """Test get_distinct_values success."""
        mock_session = MagicMock(spec=Session)
        mock_execute_result = MagicMock()
        mock_scalars_result = MagicMock()
        mock_session.execute.return_value = mock_execute_result
        mock_execute_result.scalars.return_value = mock_scalars_result
        expected_values = ['A', 'B', 'C']
        mock_scalars_result.all.return_value = expected_values

        column_name = 'road_name' # Assumed valid column on Station
        table = Station

        # Call the function directly
        values = db_utils.get_distinct_values(mock_session, column_name, table=table)

        self.assertTrue(hasattr(table, column_name))
        mock_session.execute.assert_called_once()
        mock_execute_result.scalars.assert_called_once()
        mock_scalars_result.all.assert_called_once()
        self.assertEqual(values, list(expected_values)) # Function returns a list
        mock_logger.info.assert_any_call(f"Querying distinct values for column '{column_name}' in table '{table.__tablename__}'.")
        mock_logger.info.assert_any_call(f"Found {len(values)} distinct values for column '{column_name}'.")
        mock_st.error.assert_not_called()


    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_distinct_values_invalid_column(self):
        """Test get_distinct_values with an invalid column name."""
        mock_session = MagicMock(spec=Session)
        column_name = 'invalid_column'
        table = Station

        # Call the function directly
        values = db_utils.get_distinct_values(mock_session, column_name, table=table)

        self.assertIsNone(values)
        self.assertFalse(hasattr(table, column_name)) # Check the validation logic
        mock_session.execute.assert_not_called()
        mock_logger.error.assert_called_once_with(f"Invalid column name '{column_name}' provided for table '{table.__tablename__}'.")
        mock_st.error.assert_called_once_with(f"Invalid column specified: {column_name}")

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_distinct_values_session_none(self):
        """Test get_distinct_values with None session."""
        # Call the function directly
        values = db_utils.get_distinct_values(None, 'lga', table=Station)

        self.assertIsNone(values)
        mock_logger.error.assert_called_once_with("Database session is None in get_distinct_values.")

    @patch('app.db_utils.logger', new=mock_logger)
    def test_get_distinct_values_exception(self):
        """Test get_distinct_values handles exceptions during execution."""
        mock_session = MagicMock(spec=Session)
        mock_session.execute.side_effect = Exception("DB Execute Error Distinct")
        column_name = 'lga' # Assumed valid column
        table = Station

        # Call the function directly
        values = db_utils.get_distinct_values(mock_session, column_name, table=table)

        self.assertIsNone(values)
        self.assertTrue(hasattr(table, column_name))
        mock_session.execute.assert_called_once()
        mock_logger.error.assert_called_once_with(f"Error fetching distinct values for column '{column_name}': DB Execute Error Distinct", exc_info=True)
        mock_st.error.assert_called_once_with(f"Failed to load distinct values for column '{column_name}'.")

    # === Test update_station_geometries ===

    # Patch the dependencies used *within* update_station_geometries
    @patch('app.db_utils.logger', new=mock_logger)
    @patch('app.db_utils.session_scope')
    @patch('sqlalchemy.update')
    @patch('sqlalchemy.func')
    def test_update_station_geometries_success(self, mock_sql_func, mock_update_sqlalchemy, mock_session_scope):
        """Test update_station_geometries executes update statement."""
        mock_sess_inst = MagicMock(spec=Session, name="SessionForUpdate")
        # Mock the context manager behavior provided by session_scope
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_sess_inst
        mock_context_manager.__exit__.return_value = None # Simulate no exception in 'with' block
        mock_session_scope.return_value = mock_context_manager

        # Mock the chain of SQLAlchemy calls
        mock_update_stmt = MagicMock(name="update_stmt")
        mock_values_stmt = MagicMock(name="values_stmt")
        mock_where_stmt = MagicMock(name="where_stmt") # Final statement object
        mock_point_func = MagicMock(name="st_makepoint")
        mock_srid_func = MagicMock(name="st_setsrid")

        mock_update_sqlalchemy.return_value = mock_update_stmt
        mock_update_stmt.values.return_value = mock_values_stmt
        mock_values_stmt.where.return_value = mock_where_stmt
        mock_sql_func.ST_MakePoint.return_value = mock_point_func
        mock_sql_func.ST_SetSRID.return_value = mock_srid_func

        # Call the function to test
        db_utils.update_station_geometries()

        # Assertions
        mock_session_scope.assert_called_once() # Check session_scope was used
        mock_context_manager.__enter__.assert_called_once() # Check context manager entered
        mock_update_sqlalchemy.assert_called_once_with(Station)
        mock_sql_func.ST_MakePoint.assert_called_once_with(Station.wgs84_longitude, Station.wgs84_latitude)
        mock_sql_func.ST_SetSRID.assert_called_once_with(mock_point_func, 4326)
        mock_update_stmt.values.assert_called_once_with(location_geom=mock_srid_func)
        mock_values_stmt.where.assert_called_once() # Check where clause was added
        # Check that the session's execute method was called with the final statement
        mock_sess_inst.execute.assert_called_once_with(mock_where_stmt)
        # Check context manager exited cleanly
        mock_context_manager.__exit__.assert_called_once_with(None, None, None)
        mock_st.error.assert_not_called()

    @patch('app.db_utils.logger', new=mock_logger)
    @patch('app.db_utils.session_scope')
    @patch('sqlalchemy.update') # Still need to patch update to check it wasn't called
    def test_update_station_geometries_session_none(self, mock_update_sqlalchemy, mock_session_scope):
        """Test update_station_geometries handles session being None from session_scope."""
        # Mock session_scope context manager to yield None
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = None # Simulate session_scope yielding None
        mock_context_manager.__exit__.return_value = None
        mock_session_scope.return_value = mock_context_manager

        # Call the function
        db_utils.update_station_geometries()

        mock_session_scope.assert_called_once()
        mock_context_manager.__enter__.assert_called_once()
        mock_update_sqlalchemy.assert_not_called() # Update should not be constructed
        # Check st.error was called as per the function's logic
        mock_st.error.assert_called_once_with("Database session not available for updating geometries.")
        # Check context manager exited
        mock_context_manager.__exit__.assert_called_once_with(None, None, None)


    @patch('app.db_utils.logger', new=mock_logger)
    @patch('app.db_utils.session_scope')
    @patch('sqlalchemy.update')
    @patch('sqlalchemy.func')
    def test_update_station_geometries_exception(self, mock_sql_func, mock_update_sqlalchemy, mock_session_scope):
        """Test update_station_geometries handles exceptions during execute."""
        mock_sess_inst = MagicMock(spec=Session, name="SessionForUpdateFail")
        # Simulate execute failure within the session
        mock_sess_inst.execute.side_effect = Exception("Execute failed")

        # Mock the context manager to yield the session
        # The exception will cause __exit__ to be called with error details
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_sess_inst
        # __exit__ will be called with exception info by the 'with' statement
        # We don't need to mock its return value unless we want to suppress the exception
        mock_session_scope.return_value = mock_context_manager

        # Mock the SQLAlchemy statement building as in the success case
        mock_update_stmt = MagicMock()
        mock_values_stmt = MagicMock()
        mock_where_stmt = MagicMock()
        mock_point_func = MagicMock()
        mock_srid_func = MagicMock()
        mock_update_sqlalchemy.return_value = mock_update_stmt
        mock_update_stmt.values.return_value = mock_values_stmt
        mock_values_stmt.where.return_value = mock_where_stmt
        mock_sql_func.ST_MakePoint.return_value = mock_point_func
        mock_sql_func.ST_SetSRID.return_value = mock_srid_func

        # The exception from execute should propagate out because session_scope re-raises
        with self.assertRaisesRegex(Exception, "Execute failed"):
            db_utils.update_station_geometries()

        # Assertions
        mock_session_scope.assert_called_once()
        mock_context_manager.__enter__.assert_called_once()
        mock_update_sqlalchemy.assert_called_once_with(Station) # Statement building happens before execute
        mock_sess_inst.execute.assert_called_once_with(mock_where_stmt) # Execute was called and failed

        # Check that __exit__ was called with exception details by the 'with' statement
        # This confirms the context manager handled the exception path
        mock_context_manager.__exit__.assert_called_once()
        exit_args = mock_context_manager.__exit__.call_args.args
        self.assertIsNotNone(exit_args[0]) # exc_type
        self.assertIsInstance(exit_args[1], Exception) # exc_value
        self.assertIsNotNone(exit_args[2]) # traceback

        # Check logger/st.error calls if they happen *before* the exception propagates
        # In this case, they likely don't, as the exception stops execution.
        # The error logging happens *inside* session_scope's except block.
        mock_st.error.assert_not_called() # st.error is not called directly in update_station_geometries


if __name__ == '__main__':
    unittest.main()