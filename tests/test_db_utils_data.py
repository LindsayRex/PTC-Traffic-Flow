import pytest
from unittest.mock import patch, MagicMock, call
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update, text # Use this standard import
from contextlib import contextmanager  # added for session_scope tests
from app import db_utils
from app.models import Station, HourlyCount

# Add helper contextmanagers for session_scope patching
@contextmanager
def fake_scope_none():
    """Context manager yielding None."""
    yield None

@contextmanager
def make_fake_scope(session: MagicMock):
    """
    Context manager yielding the provided mock session.

    This function is intended for testing purposes. It is used to mock
    the `session_scope` context manager in tests, allowing a mock session
    to be injected and controlled during test execution.
    """
    yield session


def make_dummy_df() -> pd.DataFrame:
    """Creates a simple dummy DataFrame for testing."""
    return pd.DataFrame({'a': [1, 2, 3]})


class TestDBUtilsData:
    """Tests for data-fetching helpers, session_scope, and update_station_geometries"""

    @patch('app.db_utils.logger', autospec=True)
    def test_get_all_station_metadata_none_session(self, mock_logger: MagicMock):
        """Test get_all_station_metadata with None session."""
        assert db_utils.get_all_station_metadata(None) is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_all_station_metadata."
        )

    @patch('app.db_utils.pd.read_sql')
    @patch('app.db_utils.logger', autospec=True)
    def test_get_all_station_metadata_success(self, mock_logger: MagicMock, mock_read_sql: MagicMock):
        """Test get_all_station_metadata successful execution."""
        session = MagicMock()
        dummy_df = make_dummy_df()
        mock_read_sql.return_value = dummy_df
        # Mock the statement and bind attributes needed by read_sql
        mock_query = MagicMock()
        mock_query.statement = 'mock_statement'
        session.query.return_value = mock_query
        session.bind = 'mock_bind'

        result = db_utils.get_all_station_metadata(session)

        assert result is not None
        pd.testing.assert_frame_equal(result, dummy_df)
        session.query.assert_called_once_with(Station)
        mock_read_sql.assert_called_once_with(mock_query.statement, 'mock_bind')
        mock_logger.debug.assert_called_once() # Check for success log

    @patch('app.db_utils.pd.read_sql', side_effect=SQLAlchemyError('DB Read Fail'), autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    @patch('app.db_utils.st', autospec=True)
    def test_get_all_station_metadata_read_sql_error(self, mock_st: MagicMock, mock_logger: MagicMock, mock_read_sql: MagicMock):
        """Test get_all_station_metadata handling read_sql error."""
        session = MagicMock()
        mock_query = MagicMock()
        mock_query.statement = 'mock_statement'
        session.query.return_value = mock_query
        session.bind = 'mock_bind'

        result = db_utils.get_all_station_metadata(session)

        assert result is None
        mock_logger.error.assert_called_once_with(
            "Error fetching station metadata: DB Read Fail", exc_info=True
        )
        mock_st.error.assert_called_once_with(
            "Failed to load station metadata from database."
        )

    @patch('app.db_utils.logger', autospec=True)
    def test_get_station_details_none_session(self, mock_logger: MagicMock):
        """Test get_station_details with None session."""
        assert db_utils.get_station_details(None, 1) is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_station_details."
        )

    def test_get_station_details_found(self):
        """Test get_station_details when station is found."""
        session = MagicMock()
        station = Station(station_key=42, name="Test Station")
        # Mock the query chain
        mock_filter = MagicMock()
        mock_filter.first.return_value = station
        session.query.return_value.filter.return_value = mock_filter

        result = db_utils.get_station_details(session, 42)

        assert result is station
        session.query.assert_called_once_with(Station)
        # Check that filter was called correctly (using call_args)
        filter_call_args = session.query.return_value.filter.call_args
        assert str(filter_call_args[0][0]) == str(Station.station_key == 42) # Compare SQL expression strings
        mock_filter.first.assert_called_once()

    @patch('app.db_utils.logger', autospec=True)
    def test_get_station_details_not_found_warning(self, mock_logger: MagicMock):
        """Test get_station_details when station is not found (checks warning log)."""
        session = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        session.query.return_value.filter.return_value = mock_filter

        result = db_utils.get_station_details(session, 42)

        assert result is None
        mock_logger.warning.assert_called_once_with("Station with key 42 not found.")
        session.query.assert_called_once_with(Station)
        filter_call_args = session.query.return_value.filter.call_args
        assert str(filter_call_args[0][0]) == str(Station.station_key == 42)
        mock_filter.first.assert_called_once()

    @patch('app.db_utils.st', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_station_details_sqlalchemy_exception(self, mock_logger: MagicMock, mock_st: MagicMock):
        """Test get_station_details handling SQLAlchemy database exception."""
        session = MagicMock()
        db_error = SQLAlchemyError("DB Query Fail")
        session.query.return_value.filter.return_value.first.side_effect = db_error

        result = db_utils.get_station_details(session, 99)

        assert result is None
        mock_logger.error.assert_called_once_with(
            "Error fetching details for station 99: DB Query Fail", exc_info=True
        )
        mock_st.error.assert_called_once_with(
            "Failed to load station details from database."
        )

    @patch('app.db_utils.logger', autospec=True)
    def test_get_latest_data_date_none_session_class(self, mock_logger: MagicMock):
        """Test get_latest_data_date with None session (class-based test)."""
        assert db_utils.get_latest_data_date(None, 1, 1) is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_latest_data_date."
        )

    def test_get_latest_data_date_success_with_timestamp(self):
        """Test get_latest_data_date successful execution returning pd.Timestamp."""
        session = MagicMock()
        expected_date = pd.Timestamp("2025-01-01")
        # Chain two filter calls before scalar() is called
        session.query.return_value.filter.return_value.filter.return_value.scalar.return_value = expected_date

        result = db_utils.get_latest_data_date(session, 7, 2)

        assert result == expected_date

    @patch('app.db_utils.st', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_latest_data_date_sqlalchemy_exception(self, mock_logger: MagicMock, mock_st: MagicMock):
        """Test get_latest_data_date handling database exception."""
        session = MagicMock()
        db_error = SQLAlchemyError("DB Scalar Fail")
        session.query.return_value.filter.return_value.scalar.side_effect = db_error

        result = db_utils.get_latest_data_date(session, 7, 2)

        assert result is None
        mock_logger.error.assert_called_once_with(
            "Error fetching latest data date for station 7, direction 2: DB Scalar Fail",
            exc_info=True
        )
        mock_st.error.assert_called_once_with(
            "Failed to load latest data date from database."
        )

    @patch('app.db_utils.logger', autospec=True)
    def test_get_hourly_data_for_stations_none_session_returns_empty_df(self, mock_logger: MagicMock):
        """Test get_hourly_data_for_stations with None session returns empty DataFrame."""
        result = db_utils.get_hourly_data_for_stations(None, [1], None, None)
        assert isinstance(result, pd.DataFrame) and result.empty # Should return empty DF
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_hourly_data_for_stations."
        )

    @patch('app.db_utils.pd.read_sql')
    @patch('app.db_utils.logger', autospec=True)
    def test_get_hourly_data_for_stations_success_full_query(self, mock_logger: MagicMock, mock_read_sql: MagicMock):
        """Test get_hourly_data_for_stations successful execution with full query chain."""
        session = MagicMock()
        dummy_df = make_dummy_df()
        mock_read_sql.return_value = dummy_df
        # simulate query building
        query_mock = MagicMock()
        query_mock.statement = 'mock_statement'  # Set before assignment to ensure correct reference
        # Mock the chain of query calls
        session.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value = query_mock
        session.bind = 'mock_bind'

        result = db_utils.get_hourly_data_for_stations(
            session, [1, 2], '2023-01-01', '2023-01-31', directions=[1], required_cols=['count']
        )

        assert result is not None
        pd.testing.assert_frame_equal(result, dummy_df)
        mock_read_sql.assert_called_once_with(query_mock.statement, 'mock_bind')
        mock_logger.debug.assert_called_once() # Check for success log
        # Add more specific assertions on query filters if needed

    @patch('app.db_utils.pd.read_sql', side_effect=SQLAlchemyError('DB Read Fail'), autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    @patch('app.db_utils.st', autospec=True)
    def test_get_hourly_data_for_stations_sqlalchemy_exception(self, mock_st: MagicMock, mock_logger: MagicMock, mock_read_sql: MagicMock):
        """Test get_hourly_data_for_stations handling SQLAlchemy database exception."""
        session = MagicMock()
        # Mock query chain up to the point where read_sql is called
        query_mock = MagicMock()
        query_mock.statement = 'mock_statement'
        session.query.return_value.filter.return_value = query_mock # Simplified chain for error test
        session.bind = 'mock_bind'

        df = db_utils.get_hourly_data_for_stations(session, [1], 's', 'e')

        assert isinstance(df, pd.DataFrame) and df.empty
        mock_logger.error.assert_called_once_with(
            "Error fetching hourly data: DB Read Fail", exc_info=True
        )
        mock_st.error.assert_called_once_with(
            "Failed to load hourly count data from database."
        )

    @patch('app.db_utils.logger', autospec=True)
    def test_get_distinct_values_none_session_class(self, mock_logger: MagicMock):
        """Test get_distinct_values with None session (class-based test)."""
        assert db_utils.get_distinct_values(None, 'station_key') is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_distinct_values."
        )

    @patch('app.db_utils.logger', autospec=True)
    def test_get_distinct_values_invalid_column_with_logger(self, mock_logger: MagicMock):
        """Test get_distinct_values with an invalid column name (with logger mock)."""
        session = MagicMock()
        result = db_utils.get_distinct_values(session, 'invalid_col')
        assert result is None
        mock_logger.error.assert_called_once_with(
            "Invalid column name 'invalid_col' requested for distinct values."
        )
        session.execute.assert_not_called() # Ensure no DB interaction

    @pytest.mark.parametrize(
        "column_name, expected_values",
        [
            ('station_key', [1, 2, 3]),
            ('direction_key', [1, 2, 3]),
            ('year', [2022, 2023]),
        ]
    )
    def test_get_distinct_values_success_parametrized(self, column_name: str, expected_values):
        """Test get_distinct_values returns correct list for valid columns (parametrized)."""
        session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = expected_values
        session.execute.return_value = mock_result

        vals = db_utils.get_distinct_values(session, column_name)

        assert vals == expected_values
        session.execute.assert_called_once()

    @patch('app.db_utils.st', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_distinct_values_sqlalchemy_exception(self, mock_logger: MagicMock, mock_st: MagicMock):
        """Test get_distinct_values handling SQLAlchemy database exception."""
        session = MagicMock()
        db_error = SQLAlchemyError("DB Execute Fail")
        session.execute.side_effect = db_error

        result = db_utils.get_distinct_values(session, 'station_key')

        assert result is None
        mock_logger.error.assert_called_once_with(
            "Error fetching distinct values for station_key: DB Execute Fail", exc_info=True
        )
        mock_st.error.assert_called_once_with(
            "Failed to load distinct values from database."
        )

    def test_session_scope_no_session_factory_result(self):
        """Test session_scope when the session factory returns None."""
        with patch('app.db_utils.get_db_session', return_value=None) as mock_get_session:
            with db_utils.session_scope() as sess:
                assert sess is None
            mock_get_session.assert_called_once()
            # No commit/rollback/close should be called on None

    def test_session_scope_commit_and_close_with_operation(self):
        """Test session_scope commits and closes on success (with operation)."""
        session = MagicMock()
        with patch('app.db_utils.get_db_session', return_value=session) as mock_get_session:
            with db_utils.session_scope() as sess:
                assert sess is session
                # Simulate some operation
                if sess is not None:
                    sess.add(MagicMock())
            mock_get_session.assert_called_once()
            session.add.assert_called_once()
            session.commit.assert_called_once()
            session.rollback.assert_not_called() # Ensure rollback wasn't called
            session.close.assert_called_once()

    def test_session_scope_rollback_on_exception(self):
        """Test session_scope rolls back and closes on exception."""
        session = MagicMock()
        with patch('app.db_utils.get_db_session', return_value=session) as mock_get_session:
            with pytest.raises(RuntimeError, match="oops"):
                with db_utils.session_scope() as sess:
                    assert sess is session
                    raise RuntimeError("oops")
            mock_get_session.assert_called_once()
            session.commit.assert_not_called() # Ensure commit wasn't called
            session.rollback.assert_called_once()
            session.close.assert_called_once()

    @patch('app.db_utils.st', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_update_station_geometries_no_session(self, mock_logger: MagicMock, mock_st: MagicMock):
        """Test update_station_geometries when session_scope yields None."""
        # Use the helper context manager directly for patching session_scope
        with patch('app.db_utils.session_scope', fake_scope_none):
            db_utils.update_station_geometries()
            mock_logger.error.assert_called_once_with(
                "Database session not available for updating geometries."
            )
            mock_st.error.assert_called_once_with(
                "Database session not available for updating geometries."
            )

    @patch('app.db_utils.logger', autospec=True)
    def test_update_station_geometries_success_with_logger(self, mock_logger: MagicMock):
        """Test update_station_geometries successful execution with logger mock."""
        session = MagicMock()
        # Use the helper context manager with the mock session
        with patch('app.db_utils.session_scope', lambda: make_fake_scope(session)):
            db_utils.update_station_geometries()

            # Check that execute was called once with a text statement
            assert session.execute.call_count == 1
            args, kwargs = session.execute.call_args
            # Ensure the statement is a SQL text clause
            assert hasattr(args[0], 'text')
            assert "UPDATE stations" in str(args[0])
            assert "ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)" in str(args[0])
            mock_logger.info.assert_has_calls([
                call("Updating station geometries..."),
                call("Station geometries updated successfully.")
            ])
            # Commit is implicitly tested by session_scope test

    @patch('app.db_utils.st', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_update_station_geometries_exception(self, mock_logger: MagicMock, mock_st: MagicMock):
        """Test update_station_geometries handling database exception."""
        session = MagicMock()
        db_error = SQLAlchemyError("DB Update Fail")
        session.execute.side_effect = db_error
        # Use the helper context manager with the mock session
        with patch('app.db_utils.session_scope', lambda: make_fake_scope(session)):
            # Exception is caught within the function, so it shouldn't propagate
            db_utils.update_station_geometries()

            assert session.execute.call_count == 1 # Execute was attempted
            mock_logger.info.assert_called_once_with("Updating station geometries...")
            mock_logger.error.assert_called_once_with(
                "Error updating station geometries: DB Update Fail", exc_info=True
            )
            mock_st.error.assert_called_once_with(
                "Failed to update station geometries in database."
            )
            # Rollback/close is implicitly tested by session_scope test
