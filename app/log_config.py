import logging
import os
import time
from pathlib import Path
import streamlit as st  # Import streamlit
import gzip
import logging.handlers

class GzipRotator:
    def __call__(self, source, dest):
        with open(source, "rb") as sf:
            with gzip.open(dest, "wb") as df:
                df.writelines(sf)
        os.remove(source)

def setup_logging():
    """Sets up logging configuration with rotation and gzip compression."""
    # Get logging configuration from secrets
    log_config = st.secrets.get("logging", {})
    level = getattr(logging, log_config.get("level", "WARNING"))

    # Dynamically generate log file name based on the script name
    script_name = Path(os.environ.get("PYFILE", "app")).stem  # Get script name from environment variable
    log_file_path = Path("logs") / f"{script_name}.log"
    log_file_path = str(log_file_path)  # Convert Path object to string

    try:
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(exist_ok=True)

        # Configure root logger for file output
        max_bytes = 10 * 1024 * 1024  # 10MB
        backup_count = 5  # Keep 5 rotated logs

        rotating_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        rotating_handler.rotator = GzipRotator()
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[rotating_handler],
            force=True
        )

        # Set higher levels for noisy libraries
        logging.getLogger("streamlit").setLevel(logging.WARNING)
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

        # Log initial messages
        logging.info(f"--- Logging Initialized (Level: {logging.getLevelName(level)}, Rotation Enabled ---")
        logging.info(f"Log file: {log_file_path}")
        logging.info(f"Max log size: {max_bytes} bytes")
        logging.info(f"Backup count: {backup_count}")
        logging.info("----------------------------------------------------------------------")

    except Exception as e:
        # Fallback to basic console logging
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
        logging.error(f"Failed to setup file logging: {e}")