import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update # Use this standard import
from app import db_utils
from app.models import Station, HourlyCount


def make_dummy_df():
    return pd.DataFrame({'a': [1, 2, 3]})


class TestDBUtilsData:
    """Tests for data-fetching helpers, session_scope, and update_station_geometries"""

    @patch('app.db_utils.logger', autospec=True)
    def test_get_all_station_metadata_none_session(self, mock_logger):
        assert db_utils.get_all_station_metadata(None) is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_all_station_metadata."
        )

    @patch('app.db_utils.pd.read_sql')
    @patch('app.db_utils.logger', autospec=True)
    def test_get_all_station_metadata_success(self, mock_logger, mock_read_sql):
        session = MagicMock()
        dummy_df = make_dummy_df()
        mock_read_sql.return_value = dummy_df
        session.query.return_value.statement = 'stmt'
        session.bind = 'bind'

        result = db_utils.get_all_station_metadata(session)
        assert result.equals(dummy_df)
        mock_read_sql.assert_called_once_with('stmt', 'bind')

    @patch('app.db_utils.pd.read_sql', side_effect=Exception('fail'), autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    @patch('app.db_utils.st', autospec=True)
    def test_get_all_station_metadata_error(self, mock_st, mock_logger, mock_read_sql):
        session = MagicMock()
        session.query.return_value.statement = 'stmt'
        session.bind = 'bind'

        assert db_utils.get_all_station_metadata(session) is None
        mock_logger.error.assert_called_once()
        mock_st.error.assert_called_once()

    @patch('app.db_utils.logger', autospec=True)
    def test_get_station_details_none_session(self, mock_logger):
        assert db_utils.get_station_details(None, 1) is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_station_details."
        )

    def test_get_station_details_found(self):
        session = MagicMock()
        station = Station()
        session.query.return_value.filter.return_value.first.return_value = station

        result = db_utils.get_station_details(session, 42)
        assert result is station

    @patch('app.db_utils.logger', autospec=True)
    def test_get_station_details_not_found(self, mock_logger):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None

        assert db_utils.get_station_details(session, 42) is None
        mock_logger.warning.assert_called_once()

    @patch('app.db_utils.st', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_station_details_exception(self, mock_logger, mock_st):
        session = MagicMock()
        session.query.return_value.filter.return_value.first.side_effect = Exception('oops')

        assert db_utils.get_station_details(session, 99) is None
        mock_logger.error.assert_called_once()
        mock_st.error.assert_called_once()

    @patch('app.db_utils.logger', autospec=True)
    def test_get_latest_data_date_none_session(self, mock_logger):
        assert db_utils.get_latest_data_date(None, 1, 1) is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_latest_data_date."
        )

    def test_get_latest_data_date_success(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.scalar.return_value = '2025-01-01'

        result = db_utils.get_latest_data_date(session, 7, 2)
        assert result == '2025-01-01'

    @patch('app.db_utils.st', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_latest_data_date_exception(self, mock_logger, mock_st):
        session = MagicMock()
        session.query.return_value.filter.return_value.scalar.side_effect = Exception('fail')

        assert db_utils.get_latest_data_date(session, 7, 2) is None
        mock_logger.error.assert_called_once()
        mock_st.error.assert_called_once()

    @patch('app.db_utils.logger', autospec=True)
    def test_get_hourly_data_for_stations_none_session(self, mock_logger):
        assert db_utils.get_hourly_data_for_stations(None, [1], None, None) is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_hourly_data_for_stations."
        )

    @patch('app.db_utils.pd.read_sql')
    @patch('app.db_utils.logger', autospec=True)
    def test_get_hourly_data_for_stations_success(self, mock_logger, mock_read_sql):
        session = MagicMock()
        dummy_df = make_dummy_df()
        mock_read_sql.return_value = dummy_df
        # simulate query building
        query = MagicMock(statement='stmt')
        session.query.return_value.filter.return_value = query
        session.bind = 'bind'

        result = db_utils.get_hourly_data_for_stations(session, [1,2], 'start', 'end', directions=[1], required_cols=None)
        assert result.equals(dummy_df)
        mock_read_sql.assert_called_once_with('stmt', 'bind')

    @patch('app.db_utils.pd.read_sql', side_effect=Exception('fail'), autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    @patch('app.db_utils.st', autospec=True)
    def test_get_hourly_data_for_stations_exception(self, mock_st, mock_logger, mock_read_sql):
        session = MagicMock()
        session.query.return_value.filter.return_value = MagicMock()
        session.bind = 'bind'

        df = db_utils.get_hourly_data_for_stations(session, [1], 's', 'e')
        assert isinstance(df, pd.DataFrame) and df.empty
        mock_logger.error.assert_called_once()
        mock_st.error.assert_called_once()

    @patch('app.db_utils.logger', autospec=True)
    def test_get_distinct_values_none_session(self, mock_logger):
        assert db_utils.get_distinct_values(None, 'station_key') is None
        mock_logger.error.assert_called_once_with(
            "Database session is None in get_distinct_values."
        )

    def test_get_distinct_values_invalid_column(self):
        session = MagicMock()
        assert db_utils.get_distinct_values(session, 'invalid_col') is None

    def test_get_distinct_values_success(self):
        session = MagicMock()
        result_proxy = MagicMock()
        result_proxy.scalars.return_value.all.return_value = [1,2,3]
        session.execute.return_value = result_proxy

        vals = db_utils.get_distinct_values(session, 'station_key')
        assert vals == [1,2,3]

    @patch('app.db_utils.st', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_distinct_values_exception(self, mock_logger, mock_st):
        session = MagicMock()
        session.execute.side_effect = Exception('fail')
        assert db_utils.get_distinct_values(session, 'station_key') is None
        mock_logger.error.assert_called_once()
        mock_st.error.assert_called_once()

    def test_session_scope_no_session(self):
        with patch('app.db_utils.get_db_session', return_value=None):
            with db_utils.session_scope() as sess:
                assert sess is None

    def test_session_scope_commit_and_close(self):
        session = MagicMock()
        with patch('app.db_utils.get_db_session', return_value=session):
            with db_utils.session_scope() as sess:
                assert sess is session
            session.commit.assert_called_once()
            session.close.assert_called_once()

    def test_session_scope_rollback(self):
        session = MagicMock()
        with patch('app.db_utils.get_db_session', return_value=session):
            with pytest.raises(RuntimeError):
                with db_utils.session_scope() as sess:
                    raise RuntimeError("oops")
            session.rollback.assert_called_once()
            session.close.assert_called_once()

    def test_update_station_geometries_none(self):
        with patch('app.db_utils.session_scope', lambda: (yield None)):
            with patch('app.db_utils.st', autospec=True) as mock_st:
                db_utils.update_station_geometries()
                mock_st.error.assert_called_once_with(
                    "Database session not available for updating geometries."
                )

    def test_update_station_geometries_success(self):
        session = MagicMock()
        def fake_scope():
            yield session
        with patch('app.db_utils.session_scope', fake_scope):
            db_utils.update_station_geometries()
            assert session.execute.call_count == 1
