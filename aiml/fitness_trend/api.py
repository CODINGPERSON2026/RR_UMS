"""
Core API logic handler for AI/ML Fitness Trend.
Orchestrates data fetching, feature engineering, prediction, recommendations, and progression.
"""

import logging
from .data.db_loader import (
    fetch_single_personnel_data,
    fetch_personnel_list_for_search,
    fetch_all_personnel_fitness_data
)
from .features.feature_engineering import generate_features_for_soldier
from .prediction.predictor import predict_soldier_fitness, get_model_info
from .recommendations.recommendation_engine import generate_full_recommendations
from .progression.progression import generate_fitness_progression_trajectory
from .training.train import train_and_persist_models

logger = logging.getLogger("fitness_trend.api")


def analyze_personnel_fitness(army_number, goal="Overall Fitness"):
    """
    Executes complete end-to-end fitness evaluation for a soldier:
    1. Fetches DB data across 4 tables.
    2. Cleans & validates data (source priority rules).
    3. Engineers feature vector (BMI, Ideal Weight, Sports, Medical).
    4. Runs AI Prediction (Score, Category, Confidence, Factors).
    5. Generates Personalized Recommendations (Diet, Workout, Safety).
    6. Generates 30-60-90 Day Progression Trajectory.
    
    Returns:
        dict: Complete structured payload for frontend consumption.
    """
    if not army_number or not isinstance(army_number, str):
        return {
            'success': False,
            'error': 'Invalid Army Number provided.'
        }
        
    data_dict = fetch_single_personnel_data(army_number.strip())
    if not data_dict or not data_dict.get('personnel'):
        return {
            'success': False,
            'error': f'Personnel record with Army Number "{army_number}" was not found in the database.'
        }
        
    p_row = data_dict['personnel']
    w_row = data_dict['weight_info']
    s_rows = data_dict['sports']
    iw_rows = data_dict['ideal_weights']
    
    # 1. Feature Engineering
    features = generate_features_for_soldier(p_row, w_row, s_rows, iw_rows)
    
    # 2. AI Prediction
    prediction = predict_soldier_fitness(features)
    
    # 3. Recommendations
    recommendations = generate_full_recommendations(features, goal=goal)
    
    # 4. Progression Trajectory
    progression = generate_fitness_progression_trajectory(
        features,
        predicted_score=prediction.get('fitness_score'),
        goal=goal
    )
    
    return {
        'success': True,
        'soldier': features,
        'prediction': prediction,
        'recommendations': recommendations,
        'progression': progression
    }


def search_personnel_records(query_str="", limit=50):
    """
    Returns search results for personnel selection.
    """
    rows = fetch_personnel_list_for_search(query_str, limit)
    results = []
    for r in rows:
        results.append({
            'army_number': r.get('army_number', ''),
            'name': r.get('name', ''),
            'rank': r.get('rank', ''),
            'company': r.get('company', ''),
            'trade': r.get('trade', ''),
            'status_type': r.get('status_type', 'shape'),
            'weight': r.get('actual_weight'),
            'height': r.get('height'),
            'age': r.get('age')
        })
    return {'success': True, 'count': len(results), 'data': results}


def trigger_retraining(version=None):
    """
    Triggers model retraining and persists new model artifacts.
    """
    try:
        res = train_and_persist_models(version=version or "v1")
        return res
    except Exception as e:
        logger.error(f"Retraining failed: {e}")
        return {'success': False, 'error': str(e)}
