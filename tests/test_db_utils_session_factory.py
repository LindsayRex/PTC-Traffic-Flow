import pytest
from unittest.mock import patch, MagicMock
from app.db_utils import create_session_factory


class TestSessionFactory:
    """Tests for session-factory creation in db_utils.create_session_factory"""

    @patch('app.db_utils.logger', autospec=True)
    def test_create_session_factory_success(self, mock_logger):
        mock_engine = MagicMock()

        session_factory = create_session_factory(mock_engine)

        assert session_factory is not None
        mock_logger.error.assert_not_called()

    @patch('app.db_utils.logger', autospec=True)
    def test_create_session_factory_failure(self, mock_logger):
        session_factory = create_session_factory(None)

        assert session_factory is None
        mock_logger.error.assert_called_once_with(
            "Cannot create session factory without a valid engine."
        )
