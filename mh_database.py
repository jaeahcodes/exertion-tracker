import sqlite3

DB_FILE = "mHealth.db"

def get_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    return conn

def initialize_database():
    """Create necessary tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
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
    conn.close()

def add_data(sbj_id, xac, yac, zac, ecgl1, ecgl2, xala, yala, zala, xgla, ygla, zgla, xmla, ymla, zmla, xgra, ygra, zgra, xmra, ymra, zmra, activity_label):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   INSERT INTO sensor_data (
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
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                      sbj_id, 
                      xac, 
                      yac, 
                      zac, 
                      ecgl1, 
                      ecgl2, 
                      xala,
                      yala, 
                      zala, 
                      xgla, 
                      ygla, 
                      zgla, 
                      xmla, 
                      ymla, 
                      zmla, 
                      xgra, 
                      ygra, 
                      zgra, 
                      xmra, 
                      ymra, 
                      zmra, 
                      activity_label
                   ))

    conn.commit()
    conn.close()
