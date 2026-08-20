import os
import sys
import sqlite3
from tqdm import tqdm

sys.path.append('../')

# VARIABLES
DB_FILE = "/Users/jaeahkim/Library/CloudStorage/GoogleDrive-jaeah@umich.edu/My Drive/Personal Projects/FitnessRecommender/data/raw/mHealth.db"
LIST_OF_COLUMN_NAMES = [
    "subject_id",
    "x_accel_chest",
    "y_accel_chest",
    "z_accel_chest",
    "ecg_l1",
    "ecg_l2",
    "x_accel_l_ankle",
    "y_accel_l_ankle",
    "z_accel_l_ankle",
    "x_gyro_l_ankle",
    "y_gyro_l_ankle",
    "z_gyro_l_ankle",
    "x_magnet_l_ankle",
    "y_magnet_l_ankle",
    "z_magnet_l_ankle",
    "x_accel_r_arm",
    "y_accel_r_arm",
    "z_accel_r_arm",
    "x_gyro_r_arm",
    "y_gyro_r_arm",
    "z_gyro_r_arm",
    "x_magnet_r_arm",
    "y_magnet_r_arm",
    "z_magnet_r_arm",
    "activity_label"
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

def initialize_database_table(table_name, list_of_column_names):
    """Create necessary tables in database dynamically if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Automatically map non-id columns to REAL NOT NULL
    column_definitions = [f"{col} REAL NOT NULL" for col in list_of_column_names]

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

def draft_initialize_database(table_name):
    """Create necessary tables in database if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create data table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER,
                    x_accel_chest REAL NOT NULL,
                    y_accel_chest REAL NOT NULL,
                    z_accel_chest REAL NOT NULL,
                    ecg_l1 REAL NOT NULL,
                    ecg_l2 REAL NOT NULL,
                    x_accel_l_ankle REAL NOT NULL,
                    y_accel_l_ankle REAL NOT NULL,
                    z_accel_l_ankle REAL NOT NULL,
                    x_gyro_l_ankle REAL NOT NULL,
                    y_gyro_l_ankle REAL NOT NULL,
                    z_gyro_l_ankle REAL NOT NULL,
                    x_magnet_l_ankle REAL NOT NULL,
                    y_magnet_l_ankle REAL NOT NULL,
                    z_magnet_l_ankle REAL NOT NULL,
                    x_accel_r_arm REAL NOT NULL,
                    y_accel_r_arm REAL NOT NULL,
                    z_accel_r_arm REAL NOT NULL,
                    x_gyro_r_arm REAL NOT NULL,
                    y_gyro_r_arm REAL NOT NULL,
                    z_gyro_r_arm REAL NOT NULL,
                    x_magnet_r_arm REAL NOT NULL,
                    y_magnet_r_arm REAL NOT NULL,
                    z_magnet_r_arm REAL NOT NULL,
                    activity_label INTEGER NOT NULL
                   )
    """)

    conn.commit()

def populate_database_from_logs():
    """Populate the database with data from log files."""
    conn = get_connection()
    cursor = conn.cursor()

    batch = []

    for sbj_id, log_file in tqdm(enumerate(log_files)):
        with open(log_file) as file:
            for line in file:
                clean_line = line.split()
                row = (sbj_id, *clean_line)
                batch.append(row)

                if len(batch) >= 1000:
                    cursor.executemany("""
                    INSERT INTO sensor_data (
                        subject_id,
                        x_accel_chest,
                        y_accel_chest,
                        z_accel_chest,
                        ecg_l1,
                        ecg_l2,
                        x_accel_l_ankle,
                        y_accel_l_ankle,
                        z_accel_l_ankle,
                        x_gyro_l_ankle,
                        y_gyro_l_ankle,
                        z_gyro_l_ankle,
                        x_magnet_l_ankle,
                        y_magnet_l_ankle,
                        z_magnet_l_ankle,
                        x_accel_r_arm,
                        y_accel_r_arm,
                        z_accel_r_arm,
                        x_gyro_r_arm,
                        y_gyro_r_arm,
                        z_gyro_r_arm,
                        x_magnet_r_arm,
                        y_magnet_r_arm,
                        z_magnet_r_arm,
                        activity_label
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch)
                    
                    conn.commit()
                    batch.clear()

    if batch:
        cursor.executemany(f"""
                    INSERT INTO sensor_data (
                        subject_id,
                        x_accel_chest,
                        y_accel_chest,
                        z_accel_chest,
                        ecg_l1,
                        ecg_l2,
                        x_accel_l_ankle,
                        y_accel_l_ankle,
                        z_accel_l_ankle,
                        x_gyro_l_ankle,
                        y_gyro_l_ankle,
                        z_gyro_l_ankle,
                        x_magnet_l_ankle,
                        y_magnet_l_ankle,
                        z_magnet_l_ankle,
                        x_accel_r_arm,
                        y_accel_r_arm,
                        z_accel_r_arm,
                        x_gyro_r_arm,
                        y_gyro_r_arm,
                        z_gyro_r_arm,
                        x_magnet_r_arm,
                        y_magnet_r_arm,
                        z_magnet_r_arm,
                        activity_label
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", batch)
        conn.commit()



if __name__ == "__main__":
    conn = get_connection()
    cursor = conn.cursor()
    

