import os
import logging
from log_config import setup_logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from models import Base  # Import Base from models.py

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def drop_db():
    logger.info("Starting database dropping process")
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/traffic_db')

    # Add sslmode=require to the database URL
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

    logger.info(f"Using database URL: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL)
    logger.info("Database engine created")

    try:
        # Use a connection context to ensure the connection is closed
        with engine.connect() as connection:
            print("\nWARNING: This will drop all existing tables in the database.")
            logger.warning("Dropping all existing tables")
            Base.metadata.drop_all(bind=connection)  # Drop all tables using the connection
            print("All tables dropped successfully")
            logger.info("All tables dropped successfully")

    except SQLAlchemyError as e:
        error_msg = f"SQLAlchemy error dropping tables: {str(e)}"
        print(f"\nERROR: {error_msg}")
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Error dropping tables: {str(e)}"
        print(f"\nERROR: {error_msg}")
        logger.error(error_msg)
    finally:
        # Dispose of the engine to release resources
        engine.dispose()
        logger.info("Database engine disposed")

if __name__ == '__main__':
    drop_db()