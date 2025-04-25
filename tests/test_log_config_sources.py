"""
Tests for configuration source management in log_config.py.

These tests verify:
1. Configuration retrieval from Streamlit secrets
2. Fallback to environment variables when secrets are unavailable
3. Fallback to defaults when neither secrets nor environment variables are available
4. Validation of log levels 
5. Correct application of configuration values to logging system
"""
import os
import sys
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# Add the project root to path if not already added by conftest
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import the module being tested
from app.log_config import setup_logging, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT


class TestConfigurationSources:
    """Test the configuration source handling in log_config module."""

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit module for testing secrets access."""
        with patch("app.log_config.st", autospec=True) as mock_st:
            # Create a proper mock structure instead of a side_effect
            yield mock_st

    @pytest.fixture
    def mock_logging_dictconfig(self):
        """Mock logging.config.dictConfig to capture configuration."""
        with patch("app.log_config.logging.config.dictConfig") as mock_dict_config:
            yield mock_dict_config

    @pytest.fixture
    def mock_basicconfig(self):
        """Mock logging.basicConfig to test fallback."""
        with patch("app.log_config.logging.basicConfig") as mock_basic_config:
            yield mock_basic_config
            
    @pytest.fixture
    def mock_inspect_stack(self):
        """Mock inspect.stack to control stack frame information."""
        with patch("app.log_config.inspect.stack") as mock_stack:
            yield mock_stack

    @pytest.fixture
    def clean_env_vars(self):
        """Remove environment variables that might interfere with tests."""
        # Save original environment variables
        original_log_level = os.environ.get("LOG_LEVEL")
        original_log_to_file = os.environ.get("LOG_TO_FILE")
        
        # Remove them for clean testing
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]
        if "LOG_TO_FILE" in os.environ:
            del os.environ["LOG_TO_FILE"]
        
        yield
        
        # Restore original environment variables
        if original_log_level is not None:
            os.environ["LOG_LEVEL"] = original_log_level
        elif "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]
            
        if original_log_to_file is not None:
            os.environ["LOG_TO_FILE"] = original_log_to_file
        elif "LOG_TO_FILE" in os.environ:
            del os.environ["LOG_TO_FILE"]

    def test_uses_streamlit_secrets_when_available(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack, clean_env_vars):
        """Test that logging configuration uses Streamlit secrets when available."""
        # Configure mock stack to avoid filename issues
        mock_frame = MagicMock()
        mock_frame.filename = "/test/path.py"
        mock_inspect_stack.return_value = [mock_frame]
        
        # Configure mock Streamlit secrets
        mock_streamlit.secrets = {
            "logging": {
                "level": "INFO",
                "format": "TEST_FORMAT",
                "date_format": "TEST_DATE_FORMAT",
                "log_to_file": True
            }
        }
        
        # Run the function being tested
        setup_logging()
        
        # Verify that dictConfig was called with the expected configuration
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert that values from Streamlit secrets were used
        assert config["formatters"]["standard"]["format"] == "TEST_FORMAT"
        assert config["formatters"]["standard"]["datefmt"] == "TEST_DATE_FORMAT"
        assert config["handlers"]["console"]["level"] == "INFO"
        assert "file" in config["handlers"]  # log_to_file was True
        assert config["root"]["level"] == "INFO"

    def test_falls_back_to_env_vars_when_secrets_unavailable(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack, clean_env_vars):
        """Test fallback to environment variables when Streamlit secrets are not available."""
        # Configure mock stack to avoid filename issues
        mock_frame = MagicMock()
        mock_frame.filename = "/test/path.py"
        mock_inspect_stack.return_value = [mock_frame]
        
        # Configure mock to simulate missing secrets by removing the attribute completely
        del mock_streamlit.secrets
        
        # Set environment variables
        os.environ["LOG_LEVEL"] = "WARNING"
        os.environ["LOG_TO_FILE"] = "true"
        
        # Run the function being tested
        setup_logging()
        
        # Verify that dictConfig was called with expected configuration
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert that values from environment variables were used
        assert config["handlers"]["console"]["level"] == "WARNING"
        assert config["root"]["level"] == "WARNING"
        assert "file" in config["handlers"]  # LOG_TO_FILE was "true"

    def test_falls_back_to_defaults_when_nothing_available(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack, clean_env_vars):
        """Test fallback to defaults when neither Streamlit secrets nor environment variables are available."""
        # Configure mock stack to avoid filename issues
        mock_frame = MagicMock()
        mock_frame.filename = "/test/path.py"
        mock_inspect_stack.return_value = [mock_frame]
        
        # Configure mock to simulate missing secrets by removing the attribute completely
        del mock_streamlit.secrets
        
        # Ensure no environment variables are set
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]
        if "LOG_TO_FILE" in os.environ:
            del os.environ["LOG_TO_FILE"]
        
        # Run the function being tested (with no environment variables set)
        setup_logging()
        
        # Verify that dictConfig was called with expected configuration
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert that default values were used
        assert config["formatters"]["standard"]["format"] == DEFAULT_LOG_FORMAT
        assert config["formatters"]["standard"]["datefmt"] == DEFAULT_DATE_FORMAT
        assert config["handlers"]["console"]["level"] == DEFAULT_LOG_LEVEL
        assert config["root"]["level"] == DEFAULT_LOG_LEVEL
        assert "file" in config["handlers"]  # Default log_to_file is True

    def test_validates_log_levels(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack, clean_env_vars):
        """Test that invalid log levels are rejected and default is used."""
        # Configure mock stack to avoid filename issues
        mock_frame = MagicMock()
        mock_frame.filename = "/test/path.py"
        mock_inspect_stack.return_value = [mock_frame]
        
        # Configure mock Streamlit secrets with invalid log level
        mock_streamlit.secrets = {
            "logging": {
                "level": "INVALID_LEVEL",
            }
        }
        
        # Run the function being tested
        setup_logging()
        
        # Verify that dictConfig was called with expected configuration
        mock_logging_dictconfig.assert_called_once()
        config = mock_logging_dictconfig.call_args[0][0]
        
        # Assert that the default log level was used instead of the invalid one
        assert config["handlers"]["console"]["level"] == DEFAULT_LOG_LEVEL
        assert config["root"]["level"] == DEFAULT_LOG_LEVEL

    def test_falls_back_to_basicconfig_if_dictconfig_fails(self, mock_streamlit, mock_logging_dictconfig, 
                                                       mock_basicconfig, mock_inspect_stack, clean_env_vars):
        """Test fallback to basicConfig if dictConfig fails."""
        # Configure mock stack to avoid filename issues
        mock_frame = MagicMock()
        mock_frame.filename = "/test/path.py"
        mock_inspect_stack.return_value = [mock_frame]
        
        # Configure mock to simulate dictConfig failing
        mock_logging_dictconfig.side_effect = ValueError("Invalid configuration")
        
        # Configure streamlit secrets with real values
        mock_streamlit.secrets = {
            "logging": {
                "level": "INFO", 
                "format": "TEST_FORMAT",
                "date_format": "TEST_DATE_FORMAT"
            }
        }
        
        # Run the function being tested
        setup_logging()
        
        # Verify that basicConfig was called with expected parameters
        mock_basicconfig.assert_called_once()
        assert mock_basicconfig.call_args[1]["level"] == "INFO"  # Should use the configured level
        assert mock_basicconfig.call_args[1]["format"] == "TEST_FORMAT"
        assert mock_basicconfig.call_args[1]["datefmt"] == "TEST_DATE_FORMAT"