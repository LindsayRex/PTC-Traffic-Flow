import pytest
from unittest.mock import patch, MagicMock
from app.db_utils import init_db_resources, get_db_session


class TestDBResources:
    """Tests for resource initialization and session provisioning in db_utils"""

    @patch('app.db_utils.get_engine', autospec=True)
    @patch('app.db_utils.create_session_factory', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_init_db_resources_success(self, mock_logger, mock_create_session_factory, mock_get_engine):
        """Test init_db_resources when engine and session factory initialize successfully."""
        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_create_session_factory.return_value = mock_session_factory

        engine, session_factory = init_db_resources()

        assert engine == mock_engine
        assert session_factory == mock_session_factory
        mock_logger.error.assert_not_called()

    @patch('app.db_utils.get_engine', return_value=None, autospec=True)
    @patch('app.db_utils.create_session_factory', return_value=None, autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_init_db_resources_failure(self, mock_logger, mock_create_session_factory, mock_get_engine):
        """Test init_db_resources when initialization fails."""
        engine, session_factory = init_db_resources()

        assert engine is None
        assert session_factory is None
        mock_logger.error.assert_called_once_with(
            "Failed to initialize one or more DB resources."
        )

    @patch('app.db_utils.create_session_factory', autospec=True)
    @patch('app.db_utils.get_engine', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_init_db_resources_stale_connection(self, mock_logger, mock_get_engine, mock_create_session_factory):
        """Test init_db_resources retries on stale DB connection."""
        engine1 = MagicMock()
        engine1.connect.side_effect = Exception("stale")
        session_factory1 = MagicMock()
        engine2 = MagicMock()
        engine2.connect.return_value = MagicMock()
        session_factory2 = MagicMock()
        mock_get_engine.side_effect = [engine1, engine2]
        mock_create_session_factory.side_effect = [session_factory1, session_factory2]

        engine, session_factory = init_db_resources()

        assert engine is engine2
        assert session_factory is session_factory2
        mock_logger.warning.assert_called_once()

    @patch('app.db_utils.init_db_resources', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_db_session_success(self, mock_logger, mock_init_db_resources):
        """Test get_db_session when session factory is available."""
        mock_engine = MagicMock()
        mock_session_factory = MagicMock(return_value=MagicMock())
        mock_init_db_resources.return_value = (mock_engine, mock_session_factory)

        session = get_db_session()

        assert session == mock_session_factory()
        mock_logger.error.assert_not_called()

    @patch('app.db_utils.init_db_resources', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_db_session_failure(self, mock_logger, mock_init_db_resources):
        """Test get_db_session when session factory is not available."""
        mock_init_db_resources.return_value = (None, None)

        session = get_db_session()

        assert session is None
        mock_logger.error.assert_called_once_with(
            "Session Factory not available, cannot create session."
        )
