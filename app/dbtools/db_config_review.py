import logging
from log_config import setup_logging
from db_utils import get_engine, get_db_session  # Import the get_engine function
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
import json
import os
from contextlib import contextmanager

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def review_database_configuration():
    """
    Reviews the database configuration, tables, columns, and indexes.
    """
    logger.info("Starting database configuration review process")

    # Ensure the logs directory exists
    log_dir = os.path.join("app", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Define the output file path
    output_file_path = os.path.join(log_dir, "db_config_review.json")

    try:
        engine = get_engine()  # Get the engine from db_utils
        if engine is None:
            logger.error("Failed to get database engine.")
            print("Failed to get database engine. Check logs.")
            return

        inspector = inspect(engine)

        db_metadata = {
            "database_name": engine.url.database,
            "tables": {}
        }

        # Get table information
        for table_name in inspector.get_table_names():
            table_info = {
                "columns": [],
                "indexes": []
            }

            # Get column information
            for column in inspector.get_columns(table_name):
                column_info = {
                    "name": column['name'],
                    "type": str(column['type']),
                    "nullable": column['nullable'],
                    "primary_key": column.get('primary_key', False),  # Use get() with a default value
                    "default": str(column['default']) if column['default'] else None
                }
                table_info["columns"].append(column_info)

            # Get index information
            for index in inspector.get_indexes(table_name):
                index_info = {
                    "name": index['name'],
                    "columns": index['column_names'],
                    "unique": index['unique']
                }
                table_info["indexes"].append(index_info)

            db_metadata["tables"][table_name] = table_info

        # Write the database metadata to a JSON file
        with open(output_file_path, "w") as outfile:
            json.dump(db_metadata, outfile, indent=4)

        print(f"Database configuration review completed successfully. Output written to {output_file_path}")
        logger.info(f"Database configuration review completed successfully. Output written to {output_file_path}")

    except SQLAlchemyError as e:
        error_msg = f"SQLAlchemy error during database review: {str(e)}"
        print(f"\nERROR: {error_msg}")
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Error during database review: {str(e)}"
        print(f"\nERROR: {error_msg}")
        logger.error(error_msg)

if __name__ == '__main__':
    review_database_configuration()