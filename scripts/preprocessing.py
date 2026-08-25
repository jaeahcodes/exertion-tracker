import sys
from pathlib import Path
import pandas as pd

# Variables
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

import src.database_functions as dbf
import src.helper_functions as hf

# 1. Initialize database connection
conn = dbf.get_connection()
dbf.initialize_database_table("sensor_data", dbf.RAW_COLUMN_SPECS)
dbf.initialize_database_table("processed_data", dbf.PROCESSED_COLUMN_SPECS)
dbf.initialize_database_table("final_data", dbf.FINAL_FEATURES)

# 2. Populate database from raw log files
dbf.populate_database("sensor_data", dbf.RAW_COLUMN_SPECS, logs = dbf.LOG_FILES, batch_size = 1000)

# 3. Process data (from DataFrame)
df = pd.read_sql("SELECT * FROM sensor_data ORDER BY subject_id ASC", conn)

# Step 3.1: Preprocess by subject
df_filtered = df.groupby("subject_id").apply(hf.preprocess_full_df).reset_index()

# Step 3.2: Extract HR by subject and activity to prevent bleeding between activity-subject pairs
df_filtered_hr = df_filtered.groupby(["subject_id", "activity_label"]).apply(
    hf.extract_hr_features
).reset_index()

df_filtered_hr.to_csv("data/processed_data.csv")

# 4. Populate database from processed DataFrame
dbf.populate_database("processed_data", dbf.PROCESSED_COLUMN_SPECS, df = df_filtered_hr, batch_size = 1000)

# 5. Feature extraction and export
final_df = hf.create_feature_df(df_filtered_hr)
final_df.to_csv("data/final_data.csv")

