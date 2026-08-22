import os
import sys
import sqlite3
from tqdm import tqdm

sys.path.append('../')

# VARIABLES
DB_FILE = "/Users/jaeahkim/Library/CloudStorage/GoogleDrive-jaeah@umich.edu/My Drive/Personal Projects/FitnessRecommender/data/raw/mHealth.db"

COLUMN_SPECS = [
    ("subject_id", "INTEGER NOT NULL"),
    ("x_accel_chest", "REAL NOT NULL"),
    ("y_accel_chest", "REAL NOT NULL"),
    ("z_accel_chest", "REAL NOT NULL"),
    ("ecg_l1", "REAL NOT NULL"),
    ("ecg_l2", "REAL NOT NULL"),
    ("x_accel_l_ankle", "REAL NOT NULL"),
    ("y_accel_l_ankle", "REAL NOT NULL"),
    ("z_accel_l_ankle", "REAL NOT NULL"),
    ("x_gyro_l_ankle", "REAL NOT NULL"),
    ("y_gyro_l_ankle", "REAL NOT NULL"),
    ("z_gyro_l_ankle", "REAL NOT NULL"),
    ("x_magnet_l_ankle", "REAL NOT NULL"),
    ("y_magnet_l_ankle", "REAL NOT NULL"),
    ("z_magnet_l_ankle", "REAL NOT NULL"),
    ("x_accel_r_arm", "REAL NOT NULL"),
    ("y_accel_r_arm", "REAL NOT NULL"),
    ("z_accel_r_arm", "REAL NOT NULL"),
    ("x_gyro_r_arm", "REAL NOT NULL"),
    ("y_gyro_r_arm", "REAL NOT NULL"),
    ("z_gyro_r_arm", "REAL NOT NULL"),
    ("x_magnet_r_arm", "REAL NOT NULL"),
    ("y_magnet_r_arm", "REAL NOT NULL"),
    ("z_magnet_r_arm", "REAL NOT NULL"),
    ("activity_label", "INTEGER NOT NULL")
]

# List of mHealth log files to process
log_files = []
for i in range(1,11):
    log_str = f"data/raw/MHEALTHDATASET/mHealth_subject{i}.log"
    log_files.append(log_str)


# FUNCTIONS
def get_connection(db_file = DB_FILE):
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(db_file)
    return conn

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

    # Automatically map non-id columns to their specified types
    column_definitions = [f"{col} {dtype}" for col, dtype in column_specs]

    # Include primary key at the beginning
    schema = ["id INTEGER PRIMARY KEY AUTOINCREMENT"] + column_definitions

    # Join into comma-separated column string
    columns_sql = ",       ".join(schema)

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
    conn = get_connection()
    cursor = conn.cursor()

    # Process column names from list
    column_definitions = [f"{col} {dtype}" for col, dtype in column_specs]

    # Join into comma-separated column string
    columns_sql = ",       ".join(column_definitions)

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




if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    

