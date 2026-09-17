import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import time
from aiml.fitness_trend.data.db_loader import fetch_all_personnel_fitness_data
from aiml.fitness_trend.features.feature_engineering import generate_features_for_soldier
from aiml.fitness_trend.prediction.predictor import predict_soldier_fitness, load_cached_models
from aiml.fitness_trend.recommendations.recommendation_engine import generate_full_recommendations
from aiml.fitness_trend.progression.progression import generate_fitness_progression_trajectory

p_rows, w_rows, s_rows, ideal_weights = fetch_all_personnel_fitness_data()
p_map = {str(p.get('army_number', '')).strip(): p for p in p_rows}
s_map = {}
for s in s_rows:
    ano = str(s.get('army_number', '')).strip()
    s_map.setdefault(ano, []).append(s)

load_cached_models()

w_row = w_rows[0]
ano = str(w_row.get('army_number', '')).strip()
p_row = p_map.get(ano)
sports = s_map.get(ano, [])

t0 = time.time()
features = generate_features_for_soldier(p_row, w_row, sports, ideal_weights)
t_feat = time.time() - t0

t0 = time.time()
pred = predict_soldier_fitness(features)
t_pred = time.time() - t0

t0 = time.time()
recs = generate_full_recommendations(features, goal="Overall Fitness")
t_recs = time.time() - t0

t0 = time.time()
prog = generate_fitness_progression_trajectory(features, predicted_score=pred.get('fitness_score'), goal="Overall Fitness")
t_prog = time.time() - t0

print(f"Features: {t_feat*1000:.2f}ms | Pred: {t_pred*1000:.2f}ms | Recs: {t_recs*1000:.2f}ms | Prog: {t_prog*1000:.2f}ms")
