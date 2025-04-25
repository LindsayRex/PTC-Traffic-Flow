"""
Tests for log output management in log_config.py.

These tests verify:
1. Configuration of output handlers (console and file)
2. Log file path construction and directory creation
3. Conditional enabling/disabling of file logging
4. Proper formatter configuration (format strings, date formats)
5. Error handling when file operations fail
"""
import os
import sys
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call, mock_open

# Add the project root to path if not already added by conftest
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import the module being tested
from app.log_config import setup_logging


class TestLogOutputManagement:
    """Test the log output management in log_config module."""

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit module for testing."""
        with patch("app.log_config.st", autospec=True) as mock_st:
            yield mock_st

    @pytest.fixture
    def mock_logging_dictconfig(self):
        """Mock logging.config.dictConfig to capture configuration."""
        with patch("app.log_config.logging.config.dictConfig") as mock_dict_config:
            yield mock_dict_config
    
    @pytest.fixture
    def mock_path_mkdir(self):
        """Mock Path.mkdir to track directory creation."""
        with patch("app.log_config.Path") as mock_path_cls:
            # Configure the mock to properly return the correct path instance
            mock_path_instance = MagicMock()
            mock_path_cls.return_value = mock_path_instance
            
            # Create a specific parent path that will be used for the mkdir
            log_dir_path = MagicMock()
            mock_path_instance.parent = MagicMock()
            mock_path_instance.parent.__truediv__.return_value = log_dir_path
            
            # Mock the mkdir function that will be called
            log_dir_path.mkdir = MagicMock()
            
            yield log_dir_path.mkdir

    @pytest.fixture
    def mock_path(self):
        """Mock Path to control path behavior."""
        with patch("app.log_config.Path") as mock_path_cls:
            # Create a mock for the Path instance
            mock_path_instance = MagicMock()
            # Configure the mock to return itself for parent
            mock_path_instance.parent = mock_path_instance
            # Configure __file__ lookup to return predefined path
            mock_path_cls.return_value = mock_path_instance
            
            yield mock_path_cls

    @pytest.fixture
    def mock_datetime(self):
        """Mock datetime to control timestamp generation."""
        with patch("app.log_config.datetime") as mock_dt:
            # Configure mock datetime to return fixed timestamp
            mock_dt.datetime.now.return_value.strftime.return_value = "20250424_120000"
            yield mock_dt

    @pytest.fixture
    def mock_inspect_stack(self):
        """Mock inspect.stack to control stack frame information."""
        with patch("app.log_config.inspect.stack") as mock_stack:
            mock_frame = MagicMock()
            mock_frame.filename = "/test/path.py"
            mock_stack.return_value = [mock_frame]
            yield mock_stack

    @pytest.fixture
    def clean_env_vars(self):
        """Remove environment variables that might interfere with tests."""
        # Save original environment variables
        original_log_to_file = os.environ.get("LOG_TO_FILE")
        
        # Remove them for clean testing
        if "LOG_TO_FILE" in os.environ:
            del os.environ["LOG_TO_FILE"]
        
        yield
        
        # Restore original environment variables
        if original_log_to_file is not None:
            os.environ["LOG_TO_FILE"] = original_log_to_file
        elif "LOG_TO_FILE" in os.environ:
            del os.environ["LOG_TO_FILE"]

    def test_configures_console_handler(self, mock_streamlit, mock_logging_dictconfig):
        """Test that setup_logging configures a console handler correctly."""
        # Configure mock Streamlit secrets
        mock_streamlit.secrets = {
            "logging": {
                "level": "INFO", 
                "log_to_file": False  # No file handler
            }
        }
        
        # Run the function being tested
        setup_logging()
        
        # Verify that dictConfig was called with console handler
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert console handler is properly configured
        assert "console" in config["handlers"]
        assert config["handlers"]["console"]["class"] == "logging.StreamHandler"
        assert config["handlers"]["console"]["stream"] == sys.stdout
        assert config["handlers"]["console"]["level"] == "INFO"
        assert config["root"]["handlers"] == ["console"]  # Only console handler

    def test_creates_file_handler_when_enabled(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack):
        """Test that setup_logging creates a file handler when file logging is enabled."""
        # Configure mock Streamlit secrets
        mock_streamlit.secrets = {
            "logging": {
                "level": "INFO",
                "log_to_file": True
            }
        }
        
        # Patch Path.mkdir directly to verify it gets called
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            # Run the function being tested
            setup_logging()
            
            # Verify directory creation
            mock_mkdir.assert_called_once_with(exist_ok=True)
        
        # Verify that dictConfig was called with file handler
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert file handler is properly configured
        assert "file" in config["handlers"]
        assert config["handlers"]["file"]["class"] == "logging.FileHandler"
        assert "encoding" in config["handlers"]["file"]
        assert config["handlers"]["file"]["encoding"] == "utf-8"
        assert "console" in config["root"]["handlers"]
        assert "file" in config["root"]["handlers"]

    def test_disables_file_handler_when_configured(self, mock_streamlit, mock_logging_dictconfig):
        """Test that setup_logging doesn't create a file handler when disabled."""
        # Configure mock Streamlit secrets
        mock_streamlit.secrets = {
            "logging": {
                "level": "INFO",
                "log_to_file": False  # Explicitly disable file logging
            }
        }
        
        # Run the function being tested
        setup_logging()
        
        # Verify that dictConfig was called with only console handler
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert file handler is not created
        assert "file" not in config["handlers"]
        assert config["root"]["handlers"] == ["console"]  # Only console handler

    def test_handles_file_creation_errors(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack):
        """Test that setup_logging handles errors when creating log directory."""
        # Configure mock Streamlit secrets
        mock_streamlit.secrets = {
            "logging": {
                "level": "INFO",
                "log_to_file": True
            }
        }
        
        # Patch Path.mkdir to raise an OSError
        with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
            # Run the function being tested
            setup_logging()
        
        # Verify that dictConfig was called with only console handler
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert file handler was not added due to error
        assert "file" not in config["handlers"]
        assert config["root"]["handlers"] == ["console"]  # Only console handler

    def test_applies_format_and_date_format(self, mock_streamlit, mock_logging_dictconfig):
        """Test that setup_logging applies the format and date format correctly."""
        # Configure mock Streamlit secrets with custom formats
        custom_format = "%(levelname)s - %(name)s - %(message)s"
        custom_date_format = "%H:%M:%S"
        mock_streamlit.secrets = {
            "logging": {
                "format": custom_format,
                "date_format": custom_date_format
            }
        }
        
        # Run the function being tested
        setup_logging()
        
        # Verify that dictConfig was called with custom formats
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert formats are correctly applied
        assert config["formatters"]["standard"]["format"] == custom_format
        assert config["formatters"]["standard"]["datefmt"] == custom_date_format