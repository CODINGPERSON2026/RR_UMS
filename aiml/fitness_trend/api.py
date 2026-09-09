"""
Core API logic handler for AI/ML Fitness Trend.
Orchestrates data fetching, feature engineering, prediction, recommendations,
progression, database persistence in ai_fitness_reports, and duplicate prevention.
"""

import logging
from .data.db_loader import (
    fetch_single_personnel_data,
    fetch_personnel_list_for_search,
    fetch_all_personnel_fitness_data,
    fetch_total_weight_info_count
)
from .data.reports_db import (
    ensure_ai_fitness_reports_table,
    get_saved_report_by_army_number,
    get_saved_report_by_id,
    insert_or_update_ai_fitness_report,
    fetch_reports_paginated,
    fetch_dynamic_report_stats
)
from .features.feature_engineering import generate_features_for_soldier
from .prediction.predictor import predict_soldier_fitness, get_model_info
from .recommendations.recommendation_engine import generate_full_recommendations
from .progression.progression import generate_fitness_progression_trajectory
from .training.train import train_and_persist_models

logger = logging.getLogger("fitness_trend.api")


def analyze_personnel_fitness(army_number, goal="Overall Fitness", regenerate=False, language="en"):
    """
    Executes or loads complete end-to-end fitness evaluation for a soldier.
    
    Workflow:
    1. If `regenerate=False`, checks `ai_fitness_reports` for existing record.
       If found, loads and returns without re-running ML computation (duplicate prevention).
    2. If not found or `regenerate=True`:
       - Fetches DB data across personnel and weight_info.
       - Generates feature vector (BMI, Ideal Weight, Sports, Medical).
       - Runs AI Prediction (Score, Category, Confidence, Factors).
       - Generates Personalized Recommendations (Diet, Workout, Safety).
       - Generates 30-60-90 Day Progression Trajectory.
       - Persists/updates record in `ai_fitness_reports`.
    
    Returns:
        dict: Complete structured payload for frontend consumption.
    """
    if not army_number or not isinstance(army_number, str):
        return {
            'success': False,
            'error': 'Invalid Army Number provided.'
        }
        
    clean_army_no = army_number.strip()

    # 1. Check existing report in ai_fitness_reports (Avoid Duplicate Reports)
    if not regenerate:
        saved = get_saved_report_by_army_number(clean_army_no)
        if saved and saved.get('prediction_result') and saved.get('recommendations') and saved.get('progression_prediction'):
            logger.info(f"Loaded existing AI fitness report ID {saved.get('id')} from database for {clean_army_no}.")
            soldier_features = _reconstruct_soldier_features(saved)
            progression = _ensure_complete_progression(saved['progression_prediction'], soldier_features, saved['prediction_result'])
            recommendations = _ensure_complete_recommendations(saved.get('recommendations'), soldier_features)
            return {
                'success': True,
                'soldier': soldier_features,
                'prediction': saved['prediction_result'],
                'recommendations': recommendations,
                'progression': progression,
                'report_id': saved.get('id'),
                'cached': True,
                'generated_at': saved.get('generated_at_str')
            }

    # 2. Fetch fresh DB records for soldier
    data_dict = fetch_single_personnel_data(clean_army_no)
    if not data_dict or not data_dict.get('personnel'):
        return {
            'success': False,
            'error': f'Personnel record with Army Number "{clean_army_no}" was not found in weight_info table.'
        }
        
    p_row = data_dict['personnel']
    w_row = data_dict['weight_info']
    s_rows = data_dict['sports']
    iw_rows = data_dict['ideal_weights']
    
    # 3. Feature Engineering
    features = generate_features_for_soldier(p_row, w_row, s_rows, iw_rows)
    
    # 4. AI Prediction
    prediction = predict_soldier_fitness(features)
    
    # 5. Recommendations
    recommendations = generate_full_recommendations(features, goal=goal)
    
    # 6. Progression Trajectory
    progression = generate_fitness_progression_trajectory(
        features,
        predicted_score=prediction.get('fitness_score'),
        goal=goal
    )
    
    # 7. Persist to ai_fitness_reports table
    report_payload = {
        'personnel_id': features.get('personnel_id'),
        'army_number': features.get('army_number'),
        'name': features.get('name'),
        'rank': features.get('rank'),
        'company': features.get('company'),
        'age': features.get('age'),
        'height_cm': features.get('height_cm'),
        'actual_weight_kg': features.get('actual_weight_kg'),
        'ideal_weight_kg': features.get('ideal_weight_kg'),
        'bmi': features.get('bmi'),
        'fitness_score': prediction.get('fitness_score'),
        'fitness_status': prediction.get('category_label'),
        'prediction_result': prediction,
        'recommendations': recommendations,
        'diet_recommendations': recommendations.get('diet'),
        'exercise_recommendations': recommendations.get('exercise'),
        'progression_prediction': progression,
        'report_language': language or 'English',
        'report_generated': True,
        'model_name': prediction.get('algorithm', 'GradientBoostingClassifier'),
        'model_version': prediction.get('model_version', 'v1')
    }
    report_id = insert_or_update_ai_fitness_report(report_payload)

    return {
        'success': True,
        'soldier': features,
        'prediction': prediction,
        'recommendations': recommendations,
        'progression': progression,
        'report_id': report_id,
        'cached': False
    }


def regenerate_personnel_fitness_report(army_number, goal="Overall Fitness", language="en"):
    """
    Explicitly forces recalculation and updates the ai_fitness_reports table.
    """
    return analyze_personnel_fitness(army_number, goal=goal, regenerate=True, language=language)


def get_saved_fitness_report_by_id(report_id):
    """
    Fetches a saved AI fitness report directly by primary key.
    """
    return get_saved_report_by_id(report_id)


def get_all_reports_paginated(search_query="", company="", status="", from_date=None, to_date=None,
                              sort_by="generated_at", sort_order="desc", page=1, per_page=10):
    """
    Returns paginated reports list with filtering and search for the dashboard table.
    """
    return fetch_reports_paginated(
        search_query=search_query,
        company=company,
        status=status,
        from_date=from_date,
        to_date=to_date,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page
    )


def get_reports_statistics():
    """
    Returns real-time dynamic statistics for CO/2IC/Adjutant dashboards.
    """
    return fetch_dynamic_report_stats()


def search_personnel_records(query_str="", limit=50):
    """
    Returns search results for personnel selection.
    """
    rows = fetch_personnel_list_for_search(query_str, limit)
    total_count = fetch_total_weight_info_count()
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
    return {
        'success': True,
        'count': len(results),
        'total_count': total_count,
        'data': results
    }


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


def _reconstruct_soldier_features(saved):
    """Reconstructs soldier feature dict from saved database record."""
    clean_army_no = saved.get('army_number', '')
    data_dict = fetch_single_personnel_data(clean_army_no)
    if data_dict and data_dict.get('personnel'):
        p_row = data_dict['personnel']
        w_row = data_dict['weight_info']
        s_rows = data_dict['sports']
        iw_rows = data_dict['ideal_weights']
        return generate_features_for_soldier(p_row, w_row, s_rows, iw_rows)

    # Fallback to saved fields if live record is missing
    return {
        'army_number': saved.get('army_number'),
        'personnel_id': saved.get('personnel_id'),
        'name': saved.get('name') or 'Soldier',
        'rank': saved.get('rank') or 'Agniveer',
        'trade': 'Clk SD',
        'company': saved.get('company') or 'Unit HQ',
        'section': 'CHQ',
        'age': saved.get('age') or 25,
        'service_years': 2.0,
        'height_cm': saved.get('height_cm') or 170.0,
        'actual_weight_kg': saved.get('actual_weight_kg') or 65.0,
        'ideal_weight_kg': saved.get('ideal_weight_kg') or 65.0,
        'bmi': saved.get('bmi') or 22.5,
        'bmi_category': 'Normal (Ideal)',
        'weight_deviation_percent': 0.0,
        'weight_difference_kg': 0.0,
        'weight_status': 'Ideal Weight',
        'bpet_grade': 'EXCELLENT',
        'ppt_grade': 'EXCELLENT',
        'physical_activity_level': 'Moderate',
        'has_medical_restriction': False,
        'medical_status': 'SHAPE-1',
        'sports_list': 'None',
        'sport_count': 0
    }


def _ensure_complete_progression(progression, soldier_features, prediction_result):
    """
    Guarantees trajectory_30d, trajectory_60d, and trajectory_90d always have
    projected_fitness_score and projected_weight_kg populated even for older records or mocks.
    """
    if not isinstance(progression, dict):
        progression = {}

    cur_wt = float(soldier_features.get('actual_weight_kg') or 70.0)
    ideal_wt = float(soldier_features.get('ideal_weight_kg') or cur_wt)
    cur_ht = float(soldier_features.get('height_cm') or 170.0)
    cur_score = float(prediction_result.get('fitness_score') if prediction_result else 70.0)

    excess = cur_wt - ideal_wt
    if excess > 0:
        w30 = round(cur_wt - min(1.8, excess * 0.35), 1)
        w60 = round(cur_wt - min(3.5, excess * 0.70), 1)
        w90 = round(cur_wt - min(5.0, excess * 0.95), 1)
    elif excess < 0:
        deficit = abs(excess)
        w30 = round(cur_wt + min(1.2, deficit * 0.35), 1)
        w60 = round(cur_wt + min(2.4, deficit * 0.70), 1)
        w90 = round(cur_wt + min(3.5, deficit * 0.90), 1)
    else:
        w30 = cur_wt
        w60 = cur_wt
        w90 = cur_wt

    headroom = 100.0 - cur_score
    s30 = round(min(100.0, cur_score + (headroom * 0.25)), 1)
    s60 = round(min(100.0, cur_score + (headroom * 0.55)), 1)
    s90 = round(min(100.0, cur_score + (headroom * 0.85)), 1)

    t30 = progression.setdefault('trajectory_30d', {})
    t60 = progression.setdefault('trajectory_60d', {})
    t90 = progression.setdefault('trajectory_90d', {})

    if not t30.get('projected_fitness_score'):
        t30['projected_fitness_score'] = s30
    if not t30.get('projected_weight_kg'):
        t30['projected_weight_kg'] = w30
    if not t30.get('projected_bmi'):
        t30['projected_bmi'] = round(w30 / ((cur_ht / 100.0) ** 2), 1) if cur_ht > 0 else 23.5

    if not t60.get('projected_fitness_score'):
        t60['projected_fitness_score'] = s60
    if not t60.get('projected_weight_kg'):
        t60['projected_weight_kg'] = w60
    if not t60.get('projected_bmi'):
        t60['projected_bmi'] = round(w60 / ((cur_ht / 100.0) ** 2), 1) if cur_ht > 0 else 23.5

    if not t90.get('projected_fitness_score'):
        t90['projected_fitness_score'] = s90
    if not t90.get('projected_weight_kg'):
        t90['projected_weight_kg'] = w90
    if not t90.get('projected_bmi'):
        t90['projected_bmi'] = round(w90 / ((cur_ht / 100.0) ** 2), 1) if cur_ht > 0 else 23.5

    return progression


def _ensure_complete_recommendations(recs, soldier_features):
    """
    Guarantees recommendations always contain the full targeted nutrition plan
    (caloric strategy, macros, hydration, unit mess meal schedule) and structured
    tactical exercise regimen matching the exact output of /fitness/.
    """
    from .recommendations.recommendation_engine import generate_full_recommendations
    fresh_recs = generate_full_recommendations(soldier_features)

    if not isinstance(recs, dict) or not recs:
        return fresh_recs

    diet = recs.get('diet')
    if not isinstance(diet, dict) or not diet.get('macros') or not diet.get('sample_menu'):
        recs['diet'] = fresh_recs['diet']
    elif not diet.get('strategy'):
        diet['strategy'] = fresh_recs['diet'].get('strategy', '')

    if not recs.get('medical_notice'):
        recs['medical_notice'] = fresh_recs['medical_notice']
    if not recs.get('exercise') or not recs['exercise'].get('exercises'):
        recs['exercise'] = fresh_recs['exercise']

    return recs

