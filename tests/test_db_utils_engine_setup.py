import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.db_utils import get_engine


class TestEngineSetup:
    """Tests for engine setup in db_utils.get_engine"""

    @patch('app.db_utils.create_engine', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_engine_success(self, mock_logger, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch('app.db_utils.st') as mock_st:
            mock_st.secrets = {'environment': {'DATABASE_URL': 'postgresql://user:password@localhost/testdb'}}

            result = get_engine()

            assert result == mock_engine
            mock_create_engine.assert_called_once_with(
                'postgresql://user:password@localhost/testdb',
                pool_pre_ping=True
            )
            mock_logger.debug.assert_called_once_with("Database engine created successfully")
            mock_st.error.assert_not_called()

    @patch('app.db_utils.logger', autospec=True)
    def test_get_engine_missing_config(self, mock_logger):
        with patch('app.db_utils.st') as mock_st:
            mock_st.secrets = {'environment': {}}

            result = get_engine()

            assert result is None
            mock_logger.error.assert_called_once_with(
                "DATABASE_URL not found in st.secrets['environment']"
            )
            mock_st.error.assert_called_once_with(
                "Database configuration (DATABASE_URL) is missing in secrets."
            )

    @patch('app.db_utils.create_engine', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_engine_sqlalchemy_error(self, mock_logger, mock_create_engine):
        mock_create_engine.side_effect = SQLAlchemyError("Connection failed")

        with patch('app.db_utils.st') as mock_st:
            mock_st.secrets = {'environment': {'DATABASE_URL': 'postgresql://user:password@localhost/testdb'}}

            result = get_engine()

            assert result is None
            mock_logger.error.assert_called_once()
            mock_st.error.assert_called_once_with(
                "Database connection failed: Connection failed"
            )
