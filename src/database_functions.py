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

print(DB_FILE)