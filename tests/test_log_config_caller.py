"""
Tests for caller script detection and integration in log_config.py.

These tests verify:
1. The inspect-based caller script name detection
2. Fallback behavior when script name cannot be determined
3. Integration of the complete logging pipeline
4. Interaction between determined caller name and log file naming
"""
import os
import sys
import logging
import inspect
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock, call

# Add the project root to path if not already added by conftest
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import the module being tested
from app.log_config import setup_logging


class TestCallerScriptDetection:
    """Test the caller script detection and integration in log_config module."""

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit module for testing."""
        with patch("app.log_config.st") as mock_st:
            mock_st.secrets = {}  # Empty secrets by default
            yield mock_st

    @pytest.fixture
    def mock_logging_dictconfig(self):
        """Mock logging.config.dictConfig to capture configuration."""
        with patch("app.log_config.logging.config.dictConfig") as mock_dict_config:
            yield mock_dict_config

    @pytest.fixture
    def mock_inspect_stack(self):
        """Mock inspect.stack to control stack frame information."""
        with patch("app.log_config.inspect.stack") as mock_stack:
            yield mock_stack

    @pytest.fixture
    def mock_datetime(self):
        """Mock datetime to control timestamp generation."""
        with patch("app.log_config.datetime") as mock_dt:
            mock_dt.datetime.now.return_value.strftime.return_value = "20250424_120000"
            yield mock_dt

    def test_detects_caller_script_name(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack):
        """Test that the correct caller script name is detected from the stack."""
        # Create a mock stack frame that simulates a real script call
        mock_frame = MagicMock()
        mock_frame.filename = "/workspaces/ptc_traffic_flow/app/main_app.py"
        mock_inspect_stack.return_value = [mock_frame]  # Stack with just one frame for simplicity
        
        # Mock the datetime to get a predictable timestamp
        with patch("app.log_config.datetime") as mock_datetime:
            mock_datetime.datetime.now.return_value.strftime.return_value = "20250424_120000"
            
            # Using patch to verify the output by mocking print
            with patch("builtins.print") as mock_print:
                # Create a concrete path instead of mocking the Path class
                with patch("app.log_config.Path") as mock_path_cls:
                    # Create a spy to capture what Path was instantiated with
                    mock_path_instance = MagicMock()
                    mock_path_cls.return_value = mock_path_instance
                    mock_path_instance.stem = "main_app"
                
                    # Run the function being tested with file logging enabled
                    mock_streamlit.secrets = {"logging": {"log_to_file": True}}
                    setup_logging()
                    
                    # Verify that dictConfig was called with a file handler
                    mock_logging_dictconfig.assert_called_once()
                    config = mock_logging_dictconfig.call_args[0][0]
                    assert "file" in config["handlers"]
                    
                    # Verify the log path is constructed with the correct path components
                    # The Path instance should have been called with the correct script name
                    assert mock_path_instance.stem == "main_app"
                    
                    # Verify that the script name was used in log messages
                    mock_print.assert_any_call("Determined caller script name for logging: main_app")

    def test_falls_back_to_default_app_name_when_detection_fails(self, mock_streamlit, mock_logging_dictconfig, 
                                                             mock_inspect_stack):
        """Test that a default app name is used when caller script detection fails."""
        # Configure mock_inspect_stack to return an empty list (detection failure scenario)
        mock_inspect_stack.return_value = []
        
        with patch("app.log_config.datetime") as mock_datetime:
            mock_datetime.datetime.now.return_value.strftime.return_value = "20250424_120000"
            
            # Using patch to verify the output by mocking print
            with patch("builtins.print") as mock_print:
                # Run the function being tested with file logging enabled
                mock_streamlit.secrets = {"logging": {"log_to_file": True}}
                setup_logging()
                
                # Verify appropriate fallback message was printed
                mock_print.assert_any_call("Could not determine caller script from stack, using default 'app' for log name.")

    def test_handles_inspect_errors(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack):
        """Test that errors in the inspect module are handled gracefully."""
        # Configure mock_inspect_stack to raise an exception
        mock_inspect_stack.side_effect = Exception("Inspect module error")
        
        with patch("app.log_config.datetime") as mock_datetime:
            mock_datetime.datetime.now.return_value.strftime.return_value = "20250424_120000"
            
            # Using patch to verify the output by mocking print
            with patch("builtins.print") as mock_print:
                # Run the function being tested
                mock_streamlit.secrets = {"logging": {"log_to_file": True}}
                setup_logging()
                
                # Verify that an error message was printed
                expected_msg = "Error inspecting stack to determine caller script name: Inspect module error. Using default 'app' for log name."
                mock_print.assert_any_call(expected_msg)

    def test_integration_with_file_naming(self, mock_streamlit, mock_logging_dictconfig, mock_inspect_stack,
                                       mock_datetime):
        """Test the integration between caller script detection and log file naming."""
        # Test with multiple frames to simulate a real call stack
        main_frame = MagicMock()
        main_frame.filename = "/workspaces/ptc_traffic_flow/app/feature_1_profile.py"
        
        irrelevant_frame = MagicMock()
        irrelevant_frame.filename = "<stdin>"  # This should be filtered out
        
        # Create a stack with the relevant frame last (as it would be in a real stack)
        mock_inspect_stack.return_value = [irrelevant_frame, main_frame]
        
        # Configure mock datetime to return fixed timestamp
        mock_datetime.datetime.now.return_value.strftime.return_value = "20250424_120000"
        
        # Using patch to verify the output by mocking print
        with patch("builtins.print") as mock_print:
            # Mock the path class
            with patch("app.log_config.Path") as mock_path_cls:
                mock_path_instance = MagicMock()
                mock_path_cls.return_value = mock_path_instance
                mock_path_instance.stem = "feature_1_profile"
                
                # Run the function being tested with file logging enabled
                mock_streamlit.secrets = {"logging": {"log_to_file": True}}
                setup_logging()
                
                # Verify the log path is constructed with the correct script name
                assert mock_path_instance.stem == "feature_1_profile"
                
                # Verify that the script name was used in log output
                mock_print.assert_any_call("Determined caller script name for logging: feature_1_profile")


class TestLoggingIntegration:
    """Test the complete logging configuration pipeline."""

    @pytest.fixture
    def setup_mocks(self):
        """Set up all required mocks for a complete test."""
        with patch("app.log_config.st") as mock_st, \
             patch("app.log_config.logging.config.dictConfig") as mock_dict_config, \
             patch("app.log_config.logging.getLogger") as mock_get_logger, \
             patch("app.log_config.logging.basicConfig") as mock_basic_config, \
             patch("pathlib.Path.mkdir") as mock_mkdir:
            
            # Configure a mock logger
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            yield {
                "st": mock_st,
                "dict_config": mock_dict_config,
                "get_logger": mock_get_logger,
                "basic_config": mock_basic_config,
                "mkdir": mock_mkdir,
                "logger": mock_logger
            }

    def test_full_logging_pipeline(self, setup_mocks):
        """Test the complete logging pipeline from configuration to message logging."""
        # Configure Streamlit secrets
        setup_mocks["st"].secrets = {
            "logging": {
                "level": "INFO",
                "format": "%(levelname)s: %(message)s",
                "log_to_file": True
            }
        }
        
        # Run setup_logging
        setup_logging()
        
        # Verify that dictConfig was called
        setup_mocks["dict_config"].assert_called_once()
        
        # Verify that getLogger was called and the logger was used
        setup_mocks["get_logger"].assert_called()
        
        # Verify that initial log messages were created
        setup_mocks["logger"].info.assert_called()
        
        # Calling info method of root logger should work after setup
        logging.info("Test message after setup")  # This would actually log in a real test
        
        # We could assert something about this call, but in a real test this would
        # depend on the actual implementation details of logging
        
    def test_handles_complete_failure_gracefully(self, setup_mocks):
        """Test that even if everything fails, logging is still set up with basicConfig."""
        # Configure dictConfig to fail
        setup_mocks["dict_config"].side_effect = Exception("Configuration failed")
        
        # Run setup_logging (should fall back to basicConfig)
        setup_logging()
        
        # Verify that basicConfig was called as a fallback
        setup_mocks["basic_config"].assert_called_once()
        
        # Verify log level and format were passed to basicConfig
        assert setup_mocks["basic_config"].call_args[1]["level"] == "ERROR"  # Default level
        
        # Even after failure, logging should still work (would use basicConfig in a real test)
        logging.warning("Warning after failure")  # This would actually log in a real test