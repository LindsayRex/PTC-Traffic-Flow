import os
import logging
from log_config import setup_logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from models import Base

# Set up logging
setup_logging(script_name="init_db")  # Pass the script name
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with station reference data"""
    logger.info("Starting database initialization process")
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/traffic_db')
    logger.info(f"Using database URL: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL)
    logger.info("Database engine created")

    try:
        with engine.connect() as connection:
            try:
                print("\nInitializing PostGIS extension...")
                logger.info("Initializing PostGIS extension")
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                connection.commit()
                print("PostGIS extension initialized successfully")
            except SQLAlchemyError as e:
                error_msg = f"SQLAlchemy error during PostGIS initialization: {str(e)}"
                print(f"\nERROR: {error_msg}")
                logger.error(error_msg)
                raise

            print("\nCreating new tables...")
            logger.info("Creating new database tables")
            Base.metadata.create_all(engine)
            print("New tables created successfully")

            print("\nDatabase initialization completed successfully!")
            logger.info("Database initialization completed successfully")

    except SQLAlchemyError as e:
        error_msg = f"SQLAlchemy error during database operations: {str(e)}"
        print(f"\nCRITICAL ERROR: {error_msg}")
        logger.critical(error_msg)
    except Exception as e:
        error_msg = f"Fatal error during database initialization: {str(e)}"
        print(f"\nCRITICAL ERROR: {error_msg}")
        logger.critical(error_msg)
    finally:
        engine.dispose()
        logger.info("Database engine disposed")

if __name__ == '__main__':
    init_db()