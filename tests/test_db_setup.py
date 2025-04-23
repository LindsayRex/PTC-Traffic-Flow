# Move warning suppression to the very top, before other imports
import warnings # Import warnings module first
from sqlalchemy.exc import SAWarning # Import SAWarning

# --- Suppress GeoAlchemy2 GenericFunction registration warnings ---
# These warnings occur because the test runner might load modules (like db_utils
# which imports models using GeoAlchemy2) multiple times, causing GeoAlchemy2
# to try and register its spatial functions repeatedly. This is generally
# harmless in the test context but clutters the output.
# Apply this filter *before* importing modules that might trigger the warning.
warnings.filterwarnings('ignore',
                        r"The GenericFunction '.*' is already registered and is going to be overridden.",
                        SAWarning)
# --- End Warning Suppression ---

# Now import other modules
import unittest
from unittest.mock import patch, MagicMock, ANY, call
import sys
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Keep this import
import datetime
import logging

# --- Mock Streamlit globally BEFORE importing db_utils ---
mock_st = MagicMock()
mock_st.stop.side_effect = SystemExit

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
    # Import models only if needed by setup/session tests (likely not)
    # from app.models import Station, HourlyCount

# Mock logger at the module level for convenience in patching later
mock_logger = MagicMock(spec=logging.Logger)

class TestDbSetup(unittest.TestCase): # Renamed class

    def setUp(self):
        """Reset mocks before each test."""
        mock_st.reset_mock()
        mock_logger.reset_mock()
        mock_st.stop.side_effect = SystemExit # Reset side effect if needed

    # === Test get_engine ===

    def test_get_engine_success(self):
        """Test get_engine successfully creates an engine."""
        mock_engine_inst = MagicMock(name="engine_instance")
        
        with patch('logging.getLogger', return_value=mock_logger), \
             patch('app.db_utils.create_engine', return_value=mock_engine_inst) as mock_create_engine, \
             patch('app.db_utils.st.secrets', new={"environment": {"DATABASE_URL": "postgresql://mock_user:mock_pass@mock_host:5432/mock_db"}}):
            
            engine = db_utils.get_engine()

            mock_create_engine.assert_called_once_with("postgresql://mock_user:mock_pass@mock_host:5432/mock_db", pool_pre_ping=True)
            self.assertEqual(engine, mock_engine_inst)
            mock_st.error.assert_not_called()
            mock_logger.info.assert_any_call("Attempting to create database engine using URL from st.secrets...")
            mock_logger.info.assert_any_call("Database engine created successfully.")

    def test_get_engine_missing_secret(self):
        """Test get_engine when DATABASE_URL is missing."""
        with patch('logging.getLogger', return_value=mock_logger), \
             patch('app.db_utils.create_engine') as mock_create_engine, \
             patch('app.db_utils.st.secrets', new={"environment": {}}):
            
            engine = db_utils.get_engine()

            self.assertIsNone(engine)
            mock_create_engine.assert_not_called() # Check create_engine wasn't called
            mock_st.error.assert_called_once_with("Database configuration (DATABASE_URL) is missing in secrets.")
            mock_logger.error.assert_called_once_with("DATABASE_URL not found in st.secrets['environment']")

    def test_get_engine_sqlalchemy_error(self):
        """Test get_engine handles SQLAlchemyError during creation."""
        with patch('logging.getLogger', return_value=mock_logger), \
             patch('app.db_utils.create_engine', side_effect=SQLAlchemyError("Connection failed")) as mock_create_engine, \
             patch('app.db_utils.st.secrets', new={"environment": {"DATABASE_URL": "postgresql://mock_user:mock_pass@mock_host:5432/mock_db"}}):
            
            engine = db_utils.get_engine()

            self.assertIsNone(engine)
            mock_create_engine.assert_called_once_with("postgresql://mock_user:mock_pass@mock_host:5432/mock_db", pool_pre_ping=True)
            mock_st.error.assert_called_once_with("Database connection failed: Connection failed")
            mock_logger.error.assert_called_once_with(f"SQLAlchemy Error creating engine: Connection failed", exc_info=True)

    def test_get_engine_other_error(self):
        """Test get_engine handles generic exceptions during creation."""
        with patch('logging.getLogger', return_value=mock_logger), \
             patch('app.db_utils.create_engine', side_effect=Exception("Unexpected error")) as mock_create_engine, \
             patch('app.db_utils.st.secrets', new={"environment": {"DATABASE_URL": "postgresql://mock_user:mock_pass@mock_host:5432/mock_db"}}):
            
            engine = db_utils.get_engine()

            self.assertIsNone(engine)
            mock_create_engine.assert_called_once_with("postgresql://mock_user:mock_pass@mock_host:5432/mock_db", pool_pre_ping=True)
            mock_st.error.assert_called_once_with("An unexpected error occurred during database setup.")
            mock_logger.error.assert_called_once_with(f"Unexpected error during database engine initialization: Unexpected error", exc_info=True)

    # === Test create_session_factory ===

    def test_create_session_factory_success(self):
        """Test create_session_factory success."""
        # Set up our mocks
        mock_engine = MagicMock(name="engine_for_factory")
        mock_factory_inst = MagicMock(name="local_factory_instance")

        # Use patch as a context manager
        with patch('logging.getLogger', return_value=mock_logger), \
             patch('app.db_utils.sessionmaker', return_value=mock_factory_inst) as mock_sessionmaker:
            
            factory = db_utils.create_session_factory(mock_engine)

            mock_sessionmaker.assert_called_once_with(bind=mock_engine)
            self.assertEqual(factory, mock_factory_inst)
            mock_logger.info.assert_any_call("Attempting to create Session Factory...")
            mock_logger.info.assert_any_call("Session Factory created successfully.")

    def test_create_session_factory_engine_none(self):
        """Test create_session_factory when engine is None."""
        with patch('logging.getLogger', return_value=mock_logger), \
             patch('app.db_utils.sessionmaker') as mock_sessionmaker:
            
            factory = db_utils.create_session_factory(None)

            self.assertIsNone(factory)
            mock_sessionmaker.assert_not_called()
            mock_logger.error.assert_called_once_with("Cannot create session factory without a valid engine.")

    def test_create_session_factory_exception(self):
        """Test create_session_factory handles exceptions."""
        mock_engine = MagicMock(name="engine_for_factory_fail")

        with patch('logging.getLogger', return_value=mock_logger), \
             patch('app.db_utils.sessionmaker', side_effect=Exception("Factory creation failed")) as mock_sessionmaker:

            factory = db_utils.create_session_factory(mock_engine)

            self.assertIsNone(factory)
            mock_sessionmaker.assert_called_once_with(bind=mock_engine)
            mock_logger.error.assert_called_once_with("Failed to create session factory: Factory creation failed", exc_info=True)

    # === Test init_db_resources ===
    # Note: We patch the functions *called by* init_db_resources
    # AND disable the cache decorator for these tests

    def test_init_db_resources_success(self):
        """Test init_db_resources success path."""
        mock_eng = MagicMock(name="Engine")
        mock_fact = MagicMock(name="Factory")
        
        with patch('logging.getLogger', return_value=mock_logger), \
             patch('app.db_utils.get_engine', return_value=mock_eng) as mock_get_engine, \
             patch('app.db_utils.create_session_factory', return_value=mock_fact) as mock_create_factory, \
             patch('app.db_utils.st.cache_resource', lambda func: func): # Disable cache
            
            # Call the function directly (mocked decorator runs it)
            engine, factory = db_utils.init_db_resources()

            mock_get_engine.assert_called_once()
            mock_create_factory.assert_called_once_with(mock_eng)
            self.assertEqual(engine, mock_eng)
            self.assertEqual(factory, mock_fact)
            mock_logger.info.assert_any_call("Initializing DB resources (engine and session factory)...")
            mock_logger.info.assert_any_call("DB resources initialized successfully.")
            mock_logger.error.assert_not_called()

    def test_init_db_resources_engine_fail(self):
        """Test init_db_resources when get_engine fails."""
        with patch('app.db_utils.get_engine', return_value=None) as mock_get_engine, \
             patch('app.db_utils.create_session_factory', return_value=None) as mock_create_factory, \
             patch('app.db_utils.logger', new=mock_logger), \
             patch('app.db_utils.st.cache_resource', lambda func: func): # Disable cache
            
            # Call the function directly
            engine, factory = db_utils.init_db_resources()

            self.assertIsNone(engine)
            self.assertIsNone(factory)
            mock_get_engine.assert_called_once()
            # create_session_factory is called with None when engine fails
            mock_create_factory.assert_called_once_with(None)
            mock_logger.error.assert_called_once_with("Failed to initialize one or more DB resources.")

    def test_init_db_resources_factory_fail(self):
        """Test init_db_resources when create_session_factory fails."""
        mock_eng = MagicMock(name="Engine")
        
        with patch('app.db_utils.get_engine', return_value=mock_eng) as mock_get_engine, \
             patch('app.db_utils.create_session_factory', return_value=None) as mock_create_factory, \
             patch('app.db_utils.logger', new=mock_logger), \
             patch('app.db_utils.st.cache_resource', lambda func: func): # Disable cache
            
            # Call the function directly
            engine, factory = db_utils.init_db_resources()

            # If factory fails, the function returns (None, None)
            self.assertIsNone(engine)
            self.assertIsNone(factory)
            mock_get_engine.assert_called_once()
            mock_create_factory.assert_called_once_with(mock_eng)
            mock_logger.error.assert_called_once_with("Failed to initialize one or more DB resources.")


    # === Test get_db_session ===
    # Patch init_db_resources AND disable cache for it when called inside get_db_session

    def test_get_db_session_success(self):
        """Test get_db_session success."""
        mock_eng = MagicMock(name="Engine")
        mock_fact = MagicMock(name="Factory")
        mock_sess_inst = MagicMock(spec=Session, name="SessionInstance")
        mock_fact.return_value = mock_sess_inst # Factory call returns session instance
        
        with patch('app.db_utils.init_db_resources', return_value=(mock_eng, mock_fact)) as mock_init_db, \
             patch('app.db_utils.logger', new=mock_logger), \
             patch('app.db_utils.st.cache_resource', lambda func: func): # Disable cache for init_db_resources
            
            session = db_utils.get_db_session()

            mock_init_db.assert_called_once()
            mock_fact.assert_called_once() # Check that the factory was called
            self.assertEqual(session, mock_sess_inst)
            mock_logger.debug.assert_called_once_with("Database session created.")
            mock_st.error.assert_not_called()

    def test_get_db_session_factory_none(self):
        """Test get_db_session when SessionFactory is None."""
        mock_eng = MagicMock(name="Engine")
        
        with patch('app.db_utils.init_db_resources', return_value=(mock_eng, None)) as mock_init_db, \
             patch('app.db_utils.logger', new=mock_logger), \
             patch('app.db_utils.st.cache_resource', lambda func: func): # Disable cache for init_db_resources
            
            session = db_utils.get_db_session()

            mock_init_db.assert_called_once()
            self.assertIsNone(session)
            mock_logger.error.assert_called_once_with("Session Factory not available, cannot create session.")
            # No st.error expected here based on current code
            mock_st.error.assert_not_called()

    def test_get_db_session_creation_exception(self):
        """Test get_db_session handles exception during session creation."""
        mock_eng = MagicMock(name="Engine")
        mock_fact = MagicMock(name="Factory", side_effect=Exception("Session creation failed"))
        
        with patch('app.db_utils.init_db_resources', return_value=(mock_eng, mock_fact)) as mock_init_db, \
             patch('app.db_utils.logger', new=mock_logger), \
             patch('app.db_utils.st.cache_resource', lambda func: func): # Disable cache for init_db_resources
            
            session = db_utils.get_db_session()

            mock_init_db.assert_called_once()
            mock_fact.assert_called_once() # Factory was called but raised exception
            self.assertIsNone(session)
            mock_logger.error.assert_called_once_with("Failed to create database session: Session creation failed", exc_info=True)
            mock_st.error.assert_called_once_with("Could not create database session.")

    # === Test session_scope ===

    def test_session_scope_success(self):
        """Test session_scope commits and closes on success."""
        mock_sess_inst = MagicMock(spec=Session, name="SessionForScope")
        
        with patch('app.db_utils.get_db_session', return_value=mock_sess_inst) as mock_get_session, \
             patch('app.db_utils.logger', new=mock_logger):
            
            yielded_session = None
            with db_utils.session_scope() as session:
                yielded_session = session
                # Simulate work - check if session is not None before using
                self.assertIsNotNone(session, "Session yielded by scope should not be None")
                session.add(MagicMock())

            mock_get_session.assert_called_once()
            self.assertEqual(yielded_session, mock_sess_inst)
            mock_sess_inst.commit.assert_called_once()
            mock_sess_inst.rollback.assert_not_called()
            mock_sess_inst.close.assert_called_once()
            mock_logger.debug.assert_called_once_with("Database session closed.")

    def test_session_scope_exception(self):
        """Test session_scope rollbacks and closes on exception."""
        mock_sess_inst = MagicMock(spec=Session, name="SessionForScopeFail")
        error_message = "Operation failed in scope"
        
        with patch('app.db_utils.get_db_session', return_value=mock_sess_inst) as mock_get_session, \
             patch('app.db_utils.logger', new=mock_logger):
            
            yielded_session = None
            with self.assertRaisesRegex(Exception, error_message):
                with db_utils.session_scope() as session:
                    yielded_session = session
                    # Check if session is not None before using
                    self.assertIsNotNone(session, "Session yielded by scope should not be None on entry")
                    raise Exception(error_message)

            mock_get_session.assert_called_once()
            self.assertEqual(yielded_session, mock_sess_inst)
            mock_sess_inst.commit.assert_not_called()
            mock_sess_inst.rollback.assert_called_once()
            mock_sess_inst.close.assert_called_once()
            mock_logger.error.assert_called_once_with(f"Session rollback due to error: {error_message}", exc_info=True)
            mock_logger.debug.assert_called_once_with("Database session closed.")

    def test_session_scope_session_none(self):
        """Test session_scope when get_db_session returns None."""
        with patch('app.db_utils.get_db_session', return_value=None) as mock_get_session, \
             patch('app.db_utils.logger', new=mock_logger):
            
            yielded_session = "initial_value"  # Should not be assigned if loop doesn't run
            with db_utils.session_scope() as session:
                yielded_session = session  # session will be None here

            mock_get_session.assert_called_once()
            self.assertIsNone(yielded_session)  # Check that None was yielded
            # Assert that commit/rollback/close were NOT called on None
            # (No need to mock session instance here as it's None)
            mock_logger.debug.assert_not_called()


if __name__ == '__main__':
    unittest.main()