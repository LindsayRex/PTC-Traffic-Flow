
import logging
from log_config import setup_logging
from sqlalchemy.exc import SQLAlchemyError
from models import Base
from db_utils import get_db_session, get_engine

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def drop_db():
    """Drop all database tables"""
    logger.info("Starting database dropping process")
    
    engine = get_engine()
    if not engine:
        logger.error("Failed to create database engine")
        return
        
    print("\nWARNING: This will drop all existing tables in the database.")
    confirmation = input("Are you sure you want to proceed? (yes/no): ")
    
    if confirmation.lower() != 'yes':
        print("Operation cancelled.")
        logger.info("Database drop cancelled by user")
        return

    try:
        logger.warning("Dropping all existing tables")
        Base.metadata.drop_all(bind=engine)
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
        engine.dispose()
        logger.info("Database engine disposed")

if __name__ == '__main__':
    drop_db()
