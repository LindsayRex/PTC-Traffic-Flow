"""
Tests for database operation-related functions in db_utils.py.

This module focuses on testing the following functions:
- session_scope()
- update_station_geometries()
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
from sqlalchemy.orm import Session
from sqlalchemy import func, update
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Optional, Any, Generator

# Mock streamlit and other dependencies BEFORE importing the module under test
mock_st = MagicMock()
mock_st.cache_data = lambda func: func  # Mock streamlit cache decorator
mock_st.cache_resource = lambda func: func  # Mock streamlit cache decorator

# Create mock classes for models
class MockStation:
    pass

# Mock the models module
mock_models = MagicMock()
mock_models.Station = MockStation

# Set up module mocks
modules = {
    'streamlit': mock_st,
    'app.models': mock_models
}

# Apply mocks using patch.dict before importing the module under test
with patch.dict(sys.modules, modules):
    from app.db_utils import session_scope, update_station_geometries


class TestDbOperations(unittest.TestCase):
    """Tests for database operation functions."""

    def setUp(self):
        """Set up test environment before each test."""
        self.mock_db_session = MagicMock(spec=Session)
        self.mock_get_db_session_patcher = patch("app.db_utils.get_db_session")
        self.mock_get_db_session = self.mock_get_db_session_patcher.start()
        
    def tearDown(self):
        """Clean up after each test."""
        self.mock_get_db_session_patcher.stop()
    
    def test_session_scope_successful_transaction(self):
        """Test successful transaction with commit."""
        # Arrange
        self.mock_get_db_session.return_value = self.mock_db_session
        
        # Act
        with session_scope() as session:
            # Simulate some database operation
            session.query(MockStation).all()
        
        # Assert
        self.mock_get_db_session.assert_called_once()
        self.mock_db_session.commit.assert_called_once()
        self.mock_db_session.rollback.assert_not_called()
        self.mock_db_session.close.assert_called_once()
    
    def test_session_scope_exception_in_transaction(self):
        """Test transaction with an exception, ensuring rollback is called."""
        # Arrange
        self.mock_get_db_session.return_value = self.mock_db_session
        
        # Act & Assert
        with self.assertRaises(ValueError):
            with session_scope() as session:
                # Simulate some database operation
                session.query(MockStation).all()
                raise ValueError("Test exception")
        
        # Assert
        self.mock_get_db_session.assert_called_once()
        self.mock_db_session.commit.assert_not_called()
        self.mock_db_session.rollback.assert_called_once()
        self.mock_db_session.close.assert_called_once()
    
    def test_session_scope_none_session(self):
        """Test handling of None session."""
        # Arrange
        self.mock_get_db_session.return_value = None
        
        # Act
        with session_scope() as session:
            self.assertIsNone(session)
        
        # Assert
        self.mock_get_db_session.assert_called_once()
    
    @patch("app.db_utils.session_scope")
    def test_update_station_geometries_successful(self, mock_session_scope):
        """Test successful update of station geometries."""
        # Arrange
        @contextmanager
        def mock_context_manager():
            yield self.mock_db_session
        
        mock_session_scope.return_value = mock_context_manager()
        
        # Act
        update_station_geometries()
        
        # Assert
        mock_session_scope.assert_called_once()
        self.mock_db_session.execute.assert_called_once()
        # Verify the update statement was constructed correctly
        args, kwargs = self.mock_db_session.execute.call_args
        self.assertIsInstance(args[0], update().__class__)
    
    @patch("app.db_utils.session_scope")
    def test_update_station_geometries_none_session(self, mock_session_scope):
        """Test handling when session is None."""
        # Arrange
        @contextmanager
        def mock_context_manager():
            yield None
        
        mock_session_scope.return_value = mock_context_manager()
        
        # Act
        update_station_geometries()
        
        # Assert
        mock_session_scope.assert_called_once()
        
    @patch("app.db_utils.session_scope")
    @patch("streamlit.error")
    def test_update_station_geometries_exception_handled(self, mock_st_error, mock_session_scope):
        """Test handling of exceptions during geometry update."""
        # Arrange
        @contextmanager
        def mock_context_manager():
            yield self.mock_db_session
        
        mock_session_scope.return_value = mock_context_manager()
        self.mock_db_session.execute.side_effect = SQLAlchemyError("Test error")
        
        # Act - this should not raise an exception due to the session_scope context manager
        update_station_geometries()
        
        # Assert
        mock_session_scope.assert_called_once()
        self.mock_db_session.execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()