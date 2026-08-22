import sys
sys.path.append('../')
import src.database_functions as dbf
import src.helper_functions as hf

from pathlib import Path
import pandas as pd

# Variables
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 1. Initialize database connection
conn = dbf.get_connection()
dbf.initialize_database_table("sensor_data", dbf.RAW_COLUMN_SPECS)

# 2. Populate database from raw log files
dbf.populate_database("sensor_data", dbf.RAW_COLUMN_SPECS, logs = dbf.LOG_FILES, batch_size = 1000)

# 3. Process data (from DataFrame)
df = pd.read_sql("SELECT * FROM sensor_data ORDER BY subject_id ASC", conn)
df_filtered = hf.preprocess_full_df(df)

# 4. Populate database from processed DataFrame
dbf.populate_database("processed_data", dbf.PROCESSED_COLUMN_SPECS, df = df_filtered, batch_size = 1000)

# TODO: 5. Create (and save) visualizations


# TODO: 6. Train cascade
