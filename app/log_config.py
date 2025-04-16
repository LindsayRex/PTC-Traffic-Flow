import logging
import os
import time
from pathlib import Path
import streamlit as st  # Import streamlit

def setup_logging(script_name="app"):
    """
    Set up logging configuration with a dynamic log file name.

    Args:
        script_name (str, optional): Name of the script using the logger.
                                     Defaults to "app".
    """
    # Get logging configuration from secrets
    log_config = st.secrets.get("logging", {})
    level = getattr(logging, log_config.get("level", "WARNING").upper(), logging.INFO)

    # Create a dynamic log file name based on the script name and timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file_name = f"{script_name}_{timestamp}.log"
    file_path = os.path.join("logs", log_file_name)

    try:
        # Create logs directory if it doesn't exist
        log_dir = Path(file_path).parent
        log_dir.mkdir(exist_ok=True)

        # Configure root logger for file output
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(str(file_path), mode='w', encoding='utf-8'),
            ],
            force=True
        )

        # Set higher levels for noisy libraries
        logging.getLogger("streamlit").setLevel(logging.WARNING)
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

        # Log initial messages
        logging.info(f"--- Logging Initialized (Level: {logging.getLevelName(level)}, Encoding: UTF-8) ---")
        logging.info(f"Log file: {file_path}")
        logging.info("----------------------------------------------------------------------")

    except Exception as e:
        # Fallback to basic console logging
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
        logging.error(f"Failed to setup file logging: {e}")