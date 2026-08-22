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

def get_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    return conn

def initialize_database_table(table_name, column_specs):
    """Create necessary tables in database dynamically if they don't exist."""
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

def populate_database_from_logs(
        table_name = "sensor_data", 
        column_specs = COLUMN_SPECS,
        logs = log_files):
    """Populate the database with data from log files."""
    conn = get_connection()
    cursor = conn.cursor()

    batch = []

    # Process column names from list
    column_definitions = [f"{col} {dtype}" for col, dtype in column_specs]

    # Join into comma-separated column string
    columns_sql = ",       ".join(column_definitions)

    for sbj_id, log_file in tqdm(enumerate(logs)):
        with open(log_file) as file:
            for line in file:
                clean_line = line.split()
                row = (sbj_id, *clean_line)
                batch.append(row)

                if len(batch) >= 1000: 
                    cursor.executemany(f"""
                    INSERT INTO {table_name} (
                    {columns_sql}
                    )
                    VALUES ({','.join(['?'] * len(column_specs))})""", batch)

                    conn.commit()
                    batch.clear()

    if batch:
        cursor.executemany(f"""
                    INSERT INTO {table_name} (
                    {columns_sql}
                    )
                    VALUES ({','.join(['?'] * len(column_specs))})""", batch)
        conn.commit()
        batch.clear()




if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    

