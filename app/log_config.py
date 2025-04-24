import logging
import logging.config
import os
import sys
from pathlib import Path
import datetime
import streamlit as st
import inspect # <-- Import inspect module

# --- FIX: Add default configuration ---
DEFAULT_LOG_LEVEL = "ERROR"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
# --- END FIX ---

def setup_logging():
    """
    Configures logging for the application.
    Attempts to use Streamlit secrets, falls back to environment variables or defaults.
    """
    log_level = DEFAULT_LOG_LEVEL
    log_format = DEFAULT_LOG_FORMAT
    date_format = DEFAULT_DATE_FORMAT
    log_to_file = True # Default to logging to file

    # --- FIX: Safely attempt to access Streamlit secrets ---
    try:
        # Check if running within Streamlit context AND secrets are available
        if hasattr(st, 'secrets'):
            log_config = st.secrets.get("logging", {})
            log_level = log_config.get("level", DEFAULT_LOG_LEVEL).upper()
            log_format = log_config.get("format", DEFAULT_LOG_FORMAT)
            date_format = log_config.get("date_format", DEFAULT_DATE_FORMAT)
            log_to_file = log_config.get("log_to_file", True)
            print("Logging configured via Streamlit secrets.") # Add print statement for clarity
        else:
             # Fallback if st.secrets doesn't exist (e.g., script run outside Streamlit)
             print("Streamlit secrets not available, checking environment variables.")
             log_level = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
             # Add similar fallbacks for format, date_format, log_to_file if needed via env vars
             log_to_file = os.environ.get("LOG_TO_FILE", "True").lower() == "true"

    except (AttributeError, st.errors.StreamlitAPIException, st.errors.StreamlitSecretNotFoundError) as e:
        # Catch errors if st.secrets access fails
        print(f"Could not access Streamlit secrets ({type(e).__name__}), checking environment variables.")
        log_level = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
        # Add similar fallbacks for format, date_format, log_to_file if needed via env vars
        log_to_file = os.environ.get("LOG_TO_FILE", "True").lower() == "true"
    # --- END FIX ---

    # --- FIX: Determine caller script name ---
    caller_script_name = "app" # Default name
    try:
        stack = inspect.stack()
        # The last frame in the stack usually represents the initial script.
        # Filter out frames that might be from interactive sessions or frozen modules.
        relevant_frames = [frame for frame in stack if frame.filename and not frame.filename.startswith('<')]
        if relevant_frames:
            # Get the filename of the outermost relevant frame
            top_level_script_path = relevant_frames[-1].filename
            # Extract the name without extension
            caller_script_name = Path(top_level_script_path).stem
            print(f"Determined caller script name for logging: {caller_script_name}") # Debug print
        else:
            print("Could not determine caller script from stack, using default 'app' for log name.")

    except Exception as inspect_err:
        print(f"Error inspecting stack to determine caller script name: {inspect_err}. Using default 'app' for log name.")
    # --- END FIX ---

    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        print(f"Warning: Invalid LOG_LEVEL '{log_level}' found. Using default '{DEFAULT_LOG_LEVEL}'.")
        log_level = DEFAULT_LOG_LEVEL

    # Basic logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format,
                'datefmt': date_format,
            },
        },
        'handlers': {
            'console': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stdout, # Explicitly use stdout
            },
        },
        'root': { # Configure the root logger
            'handlers': ['console'],
            'level': log_level,
        },
        # Example: Configure specific loggers if needed
        # 'loggers': {
        #     'app.db_utils': {
        #         'handlers': ['console'],
        #         'level': 'DEBUG', # Example: More verbose logging for db_utils
        #         'propagate': False, # Prevent messages going to root logger too
        #     },
        # }
    }

    # --- FIX: Conditional file logging ---
    if log_to_file:
        # Get the directory containing log_config.py (app/)
        script_dir = Path(__file__).parent
        # Get the parent directory (project root: ptc_traffic_flow/)
        project_root = script_dir.parent
        # Define the logs directory path within the project root
        log_dir_path = project_root / "logs"
        # Construct the full file path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # --- FIX: Use determined script name ---
        log_file_name = f"{caller_script_name}_{timestamp}.log" # Use determined name
        # --- END FIX ---
        file_path = log_dir_path / log_file_name

        try:
            # Create logs directory if it doesn't exist
            log_dir_path.mkdir(exist_ok=True)

            # Add file handler configuration
            logging_config['handlers']['file'] = {
                'level': log_level, # Log at the same level as console or specify differently
                'class': 'logging.FileHandler',
                'formatter': 'standard',
                'filename': file_path,
                'encoding': 'utf-8',
            }
            # Add file handler to the root logger
            logging_config['root']['handlers'].append('file')
            print(f"Logging to file: {file_path}")

        except OSError as e:
            print(f"Warning: Could not create log directory or file {file_path}: {e}. File logging disabled.")
            # Ensure 'file' handler is not added if creation fails
            if 'file' in logging_config['handlers']:
                del logging_config['handlers']['file']
            if 'file' in logging_config['root']['handlers']:
                logging_config['root']['handlers'].remove('file')
    else:
        print("File logging is disabled via configuration.")
    # --- END FIX ---

    # Apply the configuration
    try:
        logging.config.dictConfig(logging_config)
        # Initial log message after configuration
        root_logger = logging.getLogger()
        root_logger.info(f"--- Logging Initialized (Level: {log_level}, Encoding: UTF-8) ---")
        if log_to_file and 'file' in logging_config['handlers']:
             root_logger.info(f"Log file: {logging_config['handlers']['file']['filename']}")
        root_logger.info("-" * 70)

    except Exception as e:
        # Fallback to basicConfig if dictConfig fails
        print(f"Error applying dictConfig ({e}), falling back to basicConfig.")
        logging.basicConfig(level=log_level, format=log_format, datefmt=date_format, stream=sys.stdout)
        logging.warning("Used basicConfig due to dictConfig failure.")

# Example usage (optional, for testing)
if __name__ == '__main__':
    print("Running log_config.py directly for testing...")
    # Example: Set environment variable for testing fallback
    # os.environ["LOG_LEVEL"] = "DEBUG"
    setup_logging()
    logging.debug("This is a debug message.")
    logging.info("This is an info message.")
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")
    logging.critical("This is a critical message.")
    # Test a module logger
    # test_logger = logging.getLogger("app.test_module")
    # test_logger.info("Message from test_module")