import os
import logging
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

@st.cache_resource
def get_engine():
    """Creates a SQLAlchemy engine using Streamlit secrets."""
    try:
        # Use DATABASE_URL from Replit Secrets
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            st.error("DATABASE_URL not found in environment")
            return None

        debug_value = st.secrets.environment.get("debug", False)
        # Convert string "true" or "false" to boolean if necessary
        if isinstance(debug_value, str):
            debug = debug_value.lower() == "true"
        else:
            debug = bool(debug_value)  # Ensure it's a boolean

        return create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            echo=False
        )
    except Exception as e:
        st.error(f"Failed to create database engine: {e}")
        logger.error(f"Database connection error: {e}")
        return None

def test_db_connection(engine):
    """Tests the database connection and returns the result."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            return f"Connection successful. Result: {result}"
    except SQLAlchemyError as e:
        return f"Connection failed: {e}"

if __name__ == "__main__":
    # Example usage (only when running this file directly)
    engine = get_engine()
    if engine:
        result = test_db_connection(engine)
        print(result)
    else:
        print("Engine could not be created.")