import os
import logging
from log_config import setup_logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from models import Base

# For TOML parsing
import tomli

# Set up logging
setup_logging(script_name="init_db")
logger = logging.getLogger(__name__)

def get_database_url():
    # 1. Try environment variable
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        logger.info("Loaded DATABASE_URL from environment variable.")
        return db_url

    # 2. Try .streamlit/secrets.toml
    secrets_path = os.path.join(os.path.dirname(__file__), '..', '.streamlit', 'secrets.toml')
    try:
        with open(secrets_path, "rb") as f:
            secrets = tomli.load(f)
            db_url = secrets.get("DATABASE_URL")
            if db_url:
                logger.info("Loaded DATABASE_URL from .streamlit/secrets.toml.")
                return db_url
    except FileNotFoundError:
        logger.error(f"secrets.toml not found at {secrets_path}")
    except Exception as e:
        logger.error(f"Error reading secrets.toml: {e}")

    raise RuntimeError("DATABASE_URL not found in environment or .streamlit/secrets.toml")

def init_db():
    """Initialize the database with station reference data"""
    logger.info("Starting database initialization process")
    DATABASE_URL = get_database_url()
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