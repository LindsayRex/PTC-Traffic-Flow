
import logging
import os
import time
from pathlib import Path

def setup_logging(log_dir="logs", level=logging.DEBUG):
    """Configures verbose file logging using UTF-8 encoding."""
    try:
        # Create logs directory if it doesn't exist
        log_dir = Path(log_dir)
        log_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_filename = log_dir / f"traffic_data_{timestamp}.log"

        # Configure root logger for file output
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(str(log_filename), mode='w', encoding='utf-8'),
            ],
            force=True
        )

        # Set higher levels for noisy libraries
        logging.getLogger("streamlit").setLevel(logging.WARNING)
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

        # Log initial messages
        logging.info(f"--- Logging Initialized (Level: {logging.getLevelName(level)}, Encoding: UTF-8) ---")
        logging.info(f"Log file: {log_filename}")
        logging.info("----------------------------------------------------------------------")

    except Exception as e:
        # Fallback to basic console logging
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
        logging.error(f"Failed to setup file logging: {e}")
