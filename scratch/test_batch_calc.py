import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import time
from aiml.fitness_trend.data.db_loader import fetch_all_personnel_fitness_data, fetch_ideal_weights_table
from aiml.fitness_trend.features.feature_engineering import generate_features_for_soldier
from aiml.fitness_trend.prediction.predictor import predict_soldier_fitness, load_cached_models
from aiml.fitness_trend.recommendations.recommendation_engine import generate_full_recommendations
from aiml.fitness_trend.progression.progression import generate_fitness_progression_trajectory
from aiml.fitness_trend.data.reports_db import ensure_ai_fitness_reports_table, insert_or_update_ai_fitness_report

t0 = time.time()
p_rows, w_rows, s_rows, ideal_weights = fetch_all_personnel_fitness_data()
print(f"Loaded {len(w_rows)} weight rows, {len(p_rows)} personnel rows in {time.time() - t0:.2f}s")

# Index personnel and sports by army_number
p_map = {str(p.get('army_number', '')).strip(): p for p in p_rows}
s_map = {}
for s in s_rows:
    ano = str(s.get('army_number', '')).strip()
    s_map.setdefault(ano, []).append(s)

load_cached_models()

t1 = time.time()
# Test first 10
for i, w_row in enumerate(w_rows[:10]):
    ano = str(w_row.get('army_number', '')).strip()
    p_row = p_map.get(ano)
    sports = s_map.get(ano, [])
    features = generate_features_for_soldier(p_row, w_row, sports, ideal_weights)
    pred = predict_soldier_fitness(features)
    recs = generate_full_recommendations(features, goal="Overall Fitness")
    prog = generate_fitness_progression_trajectory(features, predicted_score=pred.get('fitness_score'), goal="Overall Fitness")
print(f"Processed 10 soldiers in {time.time() - t1:.3f}s ({((time.time() - t1)/10)*1000:.1f}ms per soldier)")
