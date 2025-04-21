import logging
import os
import time
from pathlib import Path
import streamlit as st

_logging_initialized = False # Flag to ensure setup runs only once

def setup_logging():
    """
    Set up logging configuration for the entire application.

    Configures the root logger with a timestamped file handler.
    Ensures that handlers are added only once per application run.
    """
    global _logging_initialized
    if _logging_initialized:
        return # Already initialized

    # Get logging configuration from secrets
    log_config = st.secrets.get("logging", {})
    level_name = log_config.get("level", "DEBUG").upper()
    level = getattr(logging, level_name, logging.INFO)

    # Create a dynamic log file name based on timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file_name = f"app_{timestamp}.log" # Generic name + timestamp
    
    # --- FIX: Construct path relative to this script's parent directory (the project root) ---
    # Get the directory containing log_config.py (app/)
    script_dir = Path(__file__).parent
    # Get the parent directory (project root: ptc_traffic_flow/)
    project_root = script_dir.parent
    # Define the logs directory path within the project root
    log_dir_path = project_root / "logs"
    # Construct the full file path
    file_path = log_dir_path / log_file_name
    # --- END FIX ---

    try:
        # Create logs directory if it doesn't exist
        # --- FIX: Use the correctly calculated log_dir_path ---
        log_dir_path.mkdir(exist_ok=True) # New way
        # --- END FIX ---

        # Get the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level) # Set level for the root logger

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Create file handler
        file_handler = logging.FileHandler(str(file_path), mode='w', encoding='utf-8')
        file_handler.setFormatter(formatter)

        # Add handler ONLY to the root logger
        # Check if a handler of this type already exists to be safe
        # Remove existing handlers first to avoid duplicates if run multiple times in interactive env
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.addHandler(file_handler)

        # Set higher levels for noisy libraries
        logging.getLogger("streamlit").setLevel(logging.WARNING)
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

        # Log initial messages
        root_logger.info(f"--- Logging Initialized (Level: {level_name}, Encoding: UTF-8) ---")
        root_logger.info(f"Log file: {file_path}")
        root_logger.info("----------------------------------------------------------------------")

        _logging_initialized = True # Mark as initialized

    except Exception as e:
        # Fallback basic config if specific setup fails
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
        logging.error(f"Failed to setup file logging: {e}")

# Example usage in other modules remains the same:
# import logging
# logger = logging.getLogger(__name__)
# logger.info("This message goes to the root logger's file")