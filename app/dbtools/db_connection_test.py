import toml
from sqlalchemy import create_engine, inspect
import os

def test_db_connection():
    """
    Tests the database connection and lists tables in a PostgreSQL database.
    """
    # Initialize connection to None outside the try block
    connection = None
    try:
        # Construct the path to the secrets.toml file
        # Assuming the script is run from the 'app/dbtools' directory
        # Adjust the path if the script is run from a different location
        # If run from project root ('ptc_traffic_flow'), it should be:
        # secrets_path = os.path.join(".streamlit", "secrets.toml")
        # If run from 'app/dbtools', we need to go up two levels:
        # current_dir = os.path.dirname(__file__)
        # project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        # secrets_path = os.path.join(project_root, ".streamlit", "secrets.toml")

        # Let's stick to the original assumption that it's run from a place
        # where '.streamlit/secrets.toml' is a valid relative path.
        # If you run `python app/dbtools/db_connection_test.py` from the project root,
        # the path needs adjustment as shown above.
        # For simplicity, assuming execution context makes the original path valid:
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        print(f"Attempting to load secrets from: {os.path.abspath(secrets_path)}") # Added for debugging path

        # Check if file exists before trying to load
        if not os.path.exists(secrets_path):
            raise FileNotFoundError(f"secrets.toml file not found at expected path: {secrets_path}")

        # Load the secrets from the TOML file
        secrets = toml.load(secrets_path)
        print("secrets.toml loaded successfully.")

        # Retrieve the database URL from the secrets
        # Check if 'environment' key exists first
        if "environment" not in secrets:
             raise KeyError("Key 'environment' not found in secrets.toml.")
        if "DATABASE_URL" not in secrets["environment"]:
             raise KeyError("Key 'DATABASE_URL' not found under 'environment' in secrets.toml.")

        database_url = secrets["environment"]["DATABASE_URL"]
        # Optional: Mask password if printing URL for debug
        # print(f"Using Database URL: {database_url[:database_url.find('://')+3]}...{database_url[database_url.rfind('@'):]}")

        # Create a SQLAlchemy engine
        print("Creating SQLAlchemy engine...")
        engine = create_engine(database_url)

        # Establish a connection
        print("Attempting to connect to the database...")
        connection = engine.connect()
        print("Connection established successfully.")

        # Inspect the database
        inspector = inspect(engine)

        # Get the table names
        print("Fetching table names...")
        table_names = inspector.get_table_names()

        print("\nConnection to the database was successful!")
        print("\nList of tables:")
        if table_names:
            for table_name in table_names:
                print(f"- {table_name}")
        else:
            print("(No tables found in the public schema or accessible tables)")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure the '.streamlit/secrets.toml' file exists relative to the script's execution directory.")
    except KeyError as e:
        print(f"Error: Configuration key missing - {e}. Check the structure of your secrets.toml file.")
        print("Expected structure: [environment] -> DATABASE_URL = '...'")
    except ImportError as e:
        print(f"Error: A required library might be missing. {e}")
        print("Ensure 'toml' and 'SQLAlchemy' (and potentially 'psycopg2-binary' or another DB driver) are installed.")
    except Exception as e:
        # Catch other potential errors (e.g., sqlalchemy connection errors)
        print(f"An error occurred during database connection or inspection: {e}")
        print(f"Error Type: {type(e).__name__}")
    finally:
        # This block will always execute
        if connection:
            print("Closing database connection.")
            connection.close()
        else:
            print("No active database connection to close.")

if __name__ == "__main__":
    test_db_connection()