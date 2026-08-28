import sys
from pathlib import Path
import pandas as pd

# Variables
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

import src.training_functions as tf

df_final = pd.read_csv("data/processed/final_data.csv")
df_final = df_final.drop(columns = ["Unnamed: 0"])

X, y, groups = tf.split_feature_df(df_final)

# tf.find_best_model(X, y, groups)
"""
Model Pipeline Comparison Report
           Model  Accuracy  F1 Macro  F1 Weighted
GradientBoosting  0.844304  0.691682     0.841931
      ExtraTrees  0.755906  0.684490     0.749460
         XGBoost  0.841050  0.670819     0.833456
             KNN  0.639160  0.636341     0.642384
    RandomForest  0.803885  0.634898     0.793611
"""

tf.use_best_model(X, y, groups, model = 'GradientBoosting')

