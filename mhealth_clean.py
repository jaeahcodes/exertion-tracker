import csv
import sqlite3
from tqdm import tqdm
from mh_database import get_connection, initialize_database, add_data

DB_FILE = "mHealth.db"

log_files = []

for i in range(1,11):
    log_str = f"MHEALTHDATASET/mHealth_subject{i}.log"
    log_files.append(log_str)

conn = get_connection()
cursor = conn.cursor()
initialize_database()

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
