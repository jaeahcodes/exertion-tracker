import json
import os
from pathlib import Path
import sys
import sqlite3
from tqdm import tqdm

sys.path.append('../')

# VARIABLES
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_FILE_PATH = PROJECT_ROOT / "db_file_path.txt"
with open(DB_FILE_PATH, "r") as f:
    DB_FILE = f.read().strip()

COLUMN_SPEC_FILE = PROJECT_ROOT / "column_specs.json"
with open(COLUMN_SPEC_FILE, "r") as f:
    COLUMN_SPECS = json.load(f)
RAW_COLUMN_SPECS = COLUMN_SPECS["raw"]
PROCESSED_COLUMN_SPECS = COLUMN_SPECS["processed"]


# List of mHealth log files to process
LOG_FILES = []
for i in range(1,11):
    log_str = f"data/raw/MHEALTHDATASET/mHealth_subject{i}.log"
    LOG_FILES.append(log_str)


# FUNCTIONS
def get_connection(db_file = DB_FILE):
    """Establish a connection to the SQLite database."""
    print(f"Connecting to database...")
    conn = sqlite3.connect(db_file)
    return conn

def make_column_schema(column_spec_dict):
    """Create column schema for input into database functions.
    Input:
        column_spec_dict: Dictionary of format column: dtype.
    Output:
        columns_sql: Comma-separated column dtype string."""
    column_definitions = [f"{col} {dtype}" for col, dtype in column_spec_dict.items()]
    schema = ["id INTEGER PRIMARY KEY AUTOINCREMENT"] + column_definitions
    columns_sql = ",       ".join(schema)
    return columns_sql


def initialize_database_table(table_name, column_specs):
    """Create necessary tables in database dynamically if they don't exist.
    Input: 
        table_name: Name of the table to create.
        column_specs: List of tuples specifying column names and types.
    Output: 
        None; creates the table in the database if it doesn't exist. 
    """
    conn = get_connection()
    cursor = conn.cursor()

    columns_sql = make_column_schema(column_specs)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
        )
    """)

    conn.commit()
    conn.close()

def execute_from_dataframe(
        df,
        table_name,
        columns_sql,
        length_of_columns,
        batch_size = 1000
):
    """Insert data from a DataFrame into the database dynamically.
    Input: 
        df: DataFrame containing the data to be inserted.
        table_name: Name of the table to insert data into.
        columns_sql: String of column definitions.
        batch_size: Number of rows to insert in each batch.
    Output: 
        None; inserts data into the specified database table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    batch = []

    for _, row in df.iterrows():
                batch.append(tuple(row))
    
                if len(batch) >= batch_size: 
                    cursor.executemany(f"""
                    INSERT INTO {table_name} (
                    {columns_sql}
                    )
                    VALUES ({','.join(['?'] * length_of_columns)})""", batch)
    
                    conn.commit()
                    batch.clear()

    if batch:
        cursor.executemany(f"""
                    INSERT INTO {table_name} (
                    {columns_sql}
                    )
                    VALUES ({','.join(['?'] * length_of_columns)})""", batch)
        conn.commit()
        batch.clear()

def execute_from_logs(
    table_name,
    columns_sql,
    logs,
    length_of_columns,
    batch_size = 1000
):
    """Insert data from log files into the database dynamically.
    Input: 
        table_name: Name of the table to insert data into.
        columns_sql: String of column definitions.
        logs: List of log files to read data from.
        batch_size: Number of rows to insert in each batch.
    Output: 
        None; inserts data into the specified database table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    batch = []

    for sbj_id, log_file in tqdm(enumerate(logs)):
        with open(log_file) as file:
            for line in file:
                clean_line = line.split()
                row = (sbj_id, *clean_line)
                batch.append(row)

                if len(batch) >= batch_size: 
                    cursor.executemany(f"""
                    INSERT INTO {table_name} (
                    {columns_sql}
                    )
                    VALUES ({','.join(['?'] * length_of_columns)})""", batch)

                    conn.commit()
                    batch.clear()

    if batch:
        cursor.executemany(f"""
                    INSERT INTO {table_name} (
                    {columns_sql}
                    )
                    VALUES ({','.join(['?'] * length_of_columns)})""", batch)
        conn.commit()
        batch.clear()

def populate_database(
        table_name,
        column_specs,
        logs = None,
        df = None,
        batch_size = 1000
):
    """Populate the database dynamically from a DataFrame or from log files.
    Input: 
        df: DataFrame containing the data to be inserted.
        table_name: Name of the table to insert data into.
        column_specs: List of tuples specifying column names and types.
        logs: Optional list of log files to read data from.
        batch_size: Number of rows to insert in each batch.
    Output: 
        None; inserts data into the specified database table.
    """

    columns_sql = make_column_schema(column_specs)

    length_of_columns = len(column_specs)

    if logs:
        try:
            execute_from_logs(
            table_name,
            columns_sql,
            logs,
            length_of_columns,
            batch_size = batch_size
        )
        except Exception as e:
            print(f"Error occurred while populating database from logs: {e}")
            raise
    elif df:
        try:
            execute_from_dataframe(
                df,
                table_name,
                columns_sql,
                length_of_columns,
                batch_size = batch_size
            )
        except Exception as e:
            print(f"Error occurred while populating database from DataFrame: {e}")
            raise
    else:
        raise ValueError("Invalid source specified. Use 'logs' or 'dataframe' for from_source.")

