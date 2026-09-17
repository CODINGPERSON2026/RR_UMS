import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import time
import pandas as pd
import numpy as np
from aiml.fitness_trend.data.db_loader import fetch_all_personnel_fitness_data
from aiml.fitness_trend.features.feature_engineering import generate_features_for_soldier, ML_FEATURE_COLUMNS
from aiml.fitness_trend.prediction.predictor import load_cached_models, score_to_fitness_category, FITNESS_CATEGORIES, extract_explainable_factors, compute_prediction_confidence

t0 = time.time()
p_rows, w_rows, s_rows, ideal_weights = fetch_all_personnel_fitness_data()
p_map = {str(p.get('army_number', '')).strip(): p for p in p_rows}
s_map = {}
for s in s_rows:
    ano = str(s.get('army_number', '')).strip()
    s_map.setdefault(ano, []).append(s)

models = load_cached_models()

feature_list = []
rows_dict_list = []
for w_row in w_rows:
    ano = str(w_row.get('army_number', '')).strip()
    p_row = p_map.get(ano)
    sports = s_map.get(ano, [])
    feat = generate_features_for_soldier(p_row, w_row, sports, ideal_weights)
    feature_list.append(feat)
    
    r_dict = {}
    for col in ML_FEATURE_COLUMNS:
        val = feat.get(col)
        r_dict[col] = float(val) if val is not None else np.nan
    rows_dict_list.append(r_dict)

t_feat = time.time() - t0

t0 = time.time()
df_all = pd.DataFrame(rows_dict_list, columns=ML_FEATURE_COLUMNS)
X_prep_all = models['preprocessor'].transform(df_all)
scores_all = models['regressor'].predict(X_prep_all)
preds_idx_all = models['classifier'].predict(X_prep_all)
t_pred = time.time() - t0

print(f"Features for ALL {len(w_rows)} soldiers: {t_feat:.2f}s | Bulk Vector ML Prediction: {t_pred:.3f}s!")
