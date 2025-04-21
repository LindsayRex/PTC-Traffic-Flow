import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from db_utils import get_engine

# Set up logging
logger = logging.getLogger(__name__) # Get logger for this module

def get_existing_indexes(engine, table_name):
    """Retrieves existing indexes for a given table."""
    try:
        with engine.connect() as connection:
            # SQL to fetch indexes, excluding primary keys
            query = text(f"""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = '{table_name}'
                AND indexname NOT LIKE '{table_name}_pkey';
            """)
            result = connection.execute(query)
            indexes = [row[0] for row in result]
            return indexes
    except SQLAlchemyError as e:
        logger.error(f"Error fetching indexes for table {table_name}: {e}")
        print(f"Error fetching indexes for table {table_name}: {e}")
        return []

def drop_index(engine, table_name, index_name):
    """Drops a specified index from a table."""
    try:
        with engine.connect() as connection:
            query = text(f"""
                DROP INDEX IF EXISTS {index_name};
            """)
            connection.execute(query)
            connection.commit()
            print(f"Index {index_name} dropped successfully from table {table_name}")
            logger.info(f"Index {index_name} dropped from table {table_name}")
    except SQLAlchemyError as e:
        logger.error(f"Error dropping index {index_name} from table {table_name}: {e}")
        print(f"Error dropping index {index_name} from table {table_name}: {e}")

def get_existing_tables(engine):
    """Retrieves a list of existing tables in the database."""
    try:
        with engine.connect() as connection :
            query = text("""
                SELECT tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
            """)
            result = connection.execute(query)
            tables = [row[0] for row in result]
            return tables
    except SQLAlchemyError as e:
        logger.error(f"Error fetching tables: {e}")
        print(f"Error fetching tables: {e}")
        return []

def analyze_table(engine, table_name):
    """Analyzes a specified table."""
    try:
        with engine.connect() as connection:
            query = text(f"""
                ANALYZE {table_name};
            """)
            connection.execute(query)
            connection.commit()
            print(f"Table {table_name} analyzed successfully.")
            logger.info(f"Table {table_name} analyzed.")
    except SQLAlchemyError as e:
        logger.error(f"Error analyzing table {table_name}: {e}")
        print(f"Error analyzing table {table_name}: {e}")

def build_index(engine, table_name, column_name):
    """Builds an index on a specified column of a table."""
    index_name = f"{table_name}_{column_name}_idx"
    try:
        with engine.connect() as connection:
            query = text(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} ({column_name});
            """)
            connection.execute(query)
            connection.commit()
            print(f"Index {index_name} built successfully on table {table_name}({column_name})")
            logger.info(f"Index {index_name} built on table {table_name}({column_name})")
    except SQLAlchemyError as e:
        logger.error(f"Error building index on table {table_name}({column_name}): {e}")
        print(f"Error building index on table {table_name}({column_name}): {e}")

def main():
    """Main function to drive the index building and dropping process."""
    engine = get_engine()
    if not engine:
        logger.error("Failed to create database engine")
        print("Failed to create database engine. Check logs.")
        return

    while True:
        print("\nChoose an action:")
        print("1. Drop Indexes")
        print("2. Build Indexes")
        print("3. Analyze Tables")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            # Drop Indexes
            tables = get_existing_tables(engine)
            if not tables:
                print("No tables found in the database.")
                continue

            print("\nAvailable tables:")
            for i, table in enumerate(tables):
                print(f"{i+1}. {table}")

            table_choice = input("Enter the number of the table to drop indexes from (or 'all' for all tables): ")

            if table_choice.lower() == 'all':
                tables_to_process = tables
            elif table_choice.isdigit() and 1 <= int(table_choice) <= len(tables):
                tables_to_process = [tables[int(table_choice) - 1]]
            else:
                print("Invalid table choice.")
                continue

            for table_name in tables_to_process:
                indexes = get_existing_indexes(engine, table_name)
                if not indexes:
                    print(f"No indexes found for table {table_name}")
                    continue

                print(f"\nIndexes for table {table_name}:")
                for i, index in enumerate(indexes):
                    print(f"{i+1}. {index}")

                index_choice = input("Enter the number of the index to drop (or 'all' for all indexes): ")

                if index_choice.lower() == 'all':
                    indexes_to_drop = indexes
                elif index_choice.isdigit() and 1 <= int(index_choice) <= len(indexes):
                    indexes_to_drop = [indexes[int(index_choice) - 1]]
                else:
                    print("Invalid index choice.")
                    continue

                for index_name in indexes_to_drop:
                    drop_index(engine, table_name, index_name)

        elif choice == '2':
            # Build Indexes
            tables = get_existing_tables(engine)
            if not tables:
                print("No tables found in the database.")
                continue

            print("\nAvailable tables:")
            for i, table in enumerate(tables):
                print(f"{i+1}. {table}")

            table_choice = input("Enter the number of the table to build indexes on: ")

            if not table_choice.isdigit() or not 1 <= int(table_choice) <= len(tables):
                print("Invalid table choice.")
                continue

            table_name = tables[int(table_choice) - 1]

            column_name = input(f"Enter the column name to build an index on for table {table_name}: ")
            build_index(engine, table_name, column_name)

        elif choice == '3':
            # Analyze Tables
            tables = get_existing_tables(engine)
            if not tables:
                print("No tables found in the database.")
                continue

            print("\nAvailable tables:")
            for i, table in enumerate(tables):
                print(f"{i+1}. {table}")

            table_choice = input("Enter the number of the table to analyze (or 'all' for all tables): ")

            if table_choice.lower() == 'all':
                tables_to_analyze = tables
            elif table_choice.isdigit() and 1 <= int(table_choice) <= len(tables):
                tables_to_analyze = [tables[int(table_choice) - 1]]
            else:
                print("Invalid table choice.")
                continue

            for table_name in tables_to_analyze:
                analyze_table(engine, table_name)

        elif choice == '4':
            print("Exiting.")
            break

        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()