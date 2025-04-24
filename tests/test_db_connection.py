import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.db_utils import get_engine, create_session_factory, init_db_resources, get_db_session

# filepath: /workspaces/ptc_traffic_flow/tests/test_db_connection.py

@pytest.fixture
def reset_mocks():
    """Fixture to reset mocks and shared state."""
    with patch('app.db_utils.get_engine') as mock_get_engine, \
         patch('app.db_utils.create_session_factory') as mock_create_session_factory, \
         patch('app.db_utils.logger') as mock_logger:
        yield mock_get_engine, mock_create_session_factory, mock_logger

class TestDatabaseConnection:
    """Tests for database connection functionality."""

    @patch('app.db_utils.create_engine', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_engine_success(self, mock_logger, mock_create_engine):
        """Test get_engine when database URL is properly configured."""
        # Arrange
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        with patch('app.db_utils.st') as mock_st:
            mock_st.secrets = {
                'environment': {
                    'DATABASE_URL': 'postgresql://user:password@localhost/testdb'
                }
            }

            # Act
            result = get_engine()

            # Assert
            assert result == mock_engine
            mock_create_engine.assert_called_once_with(
                'postgresql://user:password@localhost/testdb',
                pool_pre_ping=True
            )
            mock_logger.debug.assert_called_once_with("Database engine created successfully")
            mock_st.error.assert_not_called()

    @patch('app.db_utils.logger', autospec=True)
    def test_get_engine_missing_config(self, mock_logger):
        """Test get_engine when DATABASE_URL is missing in configuration."""
        with patch('app.db_utils.st') as mock_st:
            mock_st.secrets = {'environment': {}}

            # Act
            result = get_engine()

            # Assert
            assert result is None
            mock_logger.error.assert_called_once_with("DATABASE_URL not found in st.secrets['environment']")
            mock_st.error.assert_called_once_with("Database configuration (DATABASE_URL) is missing in secrets.")

    @patch('app.db_utils.create_engine', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_engine_sqlalchemy_error(self, mock_logger, mock_create_engine):
        """Test get_engine when SQLAlchemy raises an error."""
        mock_create_engine.side_effect = SQLAlchemyError("Connection failed")

        with patch('app.db_utils.st') as mock_st:
            mock_st.secrets = {
                'environment': {
                    'DATABASE_URL': 'postgresql://user:password@localhost/testdb'
                }
            }

            # Act
            result = get_engine()

            # Assert
            assert result is None
            mock_logger.error.assert_called_once()
            mock_st.error.assert_called_once_with("Database connection failed: Connection failed")

    @patch('app.db_utils.logger', autospec=True)
    def test_create_session_factory_success(self, mock_logger):
        """Test create_session_factory when a valid engine is provided."""
        mock_engine = MagicMock()

        # Act
        session_factory = create_session_factory(mock_engine)

        # Assert
        assert session_factory is not None
        mock_logger.error.assert_not_called()

    @patch('app.db_utils.logger', autospec=True)
    def test_create_session_factory_failure(self, mock_logger):
        """Test create_session_factory when no engine is provided."""
        # Act
        session_factory = create_session_factory(None)

        # Assert
        assert session_factory is None
        mock_logger.error.assert_called_once_with("Cannot create session factory without a valid engine.")

    @patch('app.db_utils.get_engine', autospec=True)
    @patch('app.db_utils.create_session_factory', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_init_db_resources_success(self, mock_logger, mock_create_session_factory, mock_get_engine):
        """Test init_db_resources when engine and session factory are initialized successfully."""
        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_create_session_factory.return_value = mock_session_factory

        # Act
        engine, session_factory = init_db_resources()

        # Assert
        assert engine == mock_engine
        assert session_factory == mock_session_factory
        mock_logger.error.assert_not_called()

    @patch('app.db_utils.get_engine', return_value=None, autospec=True)
    @patch('app.db_utils.create_session_factory', return_value=None, autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_init_db_resources_failure(self, mock_logger, mock_create_session_factory, mock_get_engine):
        """Test init_db_resources when engine or session factory initialization fails."""
        # Act
        engine, session_factory = init_db_resources()

        # Assert
        assert engine is None
        assert session_factory is None
        mock_logger.error.assert_called_once_with("Failed to initialize one or more DB resources.")

    @patch('app.db_utils.create_session_factory', autospec=True)
    @patch('app.db_utils.get_engine', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_init_db_resources_stale_connection(self, mock_logger, mock_get_engine, mock_create_session_factory):
        """Test init_db_resources retries on stale DB connection."""
        # First engine connects raises, second succeeds
        engine1 = MagicMock()
        engine1.connect.side_effect = Exception("stale")
        session_factory1 = MagicMock()
        engine2 = MagicMock()
        # engine2.connect returns a context manager
        engine2.connect.return_value = MagicMock()
        session_factory2 = MagicMock()
        # Setup side effects
        mock_get_engine.side_effect = [engine1, engine2]
        mock_create_session_factory.side_effect = [session_factory1, session_factory2]

        # Act
        engine, session_factory = init_db_resources()

        # Assert returns the second engine and factory
        assert engine is engine2
        assert session_factory is session_factory2
        mock_logger.warning.assert_called_once()

    @patch('app.db_utils.init_db_resources', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_db_session_success(self, mock_logger, mock_init_db_resources):
        """Test get_db_session when session factory is available."""
        mock_engine = MagicMock()
        mock_session_factory = MagicMock()
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session
        mock_init_db_resources.return_value = (mock_engine, mock_session_factory)

        # Act
        session = get_db_session()

        # Assert
        assert session == mock_session
        mock_logger.error.assert_not_called()

    @patch('app.db_utils.init_db_resources', autospec=True)
    @patch('app.db_utils.logger', autospec=True)
    def test_get_db_session_failure(self, mock_logger, mock_init_db_resources):
        """Test get_db_session when session factory is not available."""
        mock_init_db_resources.return_value = (None, None)

        # Act
        session = get_db_session()

        # Assert
        assert session is None
        mock_logger.error.assert_called_once_with("Session Factory not available, cannot create session.")