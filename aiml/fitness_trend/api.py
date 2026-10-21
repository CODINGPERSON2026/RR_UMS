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
from datetime import datetime
from .data.reports_db import (
    ensure_ai_fitness_reports_table,
    get_saved_report_by_army_number,
    get_saved_report_by_id,
    insert_or_update_ai_fitness_report,
    bulk_insert_or_update_ai_fitness_reports,
    touch_fitness_report_timestamp,
    fetch_reports_paginated,
    fetch_dynamic_report_stats
)
from .features.feature_engineering import generate_features_for_soldier
from .prediction.predictor import predict_soldier_fitness, get_model_info, load_cached_models
from .recommendations.recommendation_engine import generate_full_recommendations
from .progression.progression import generate_fitness_progression_trajectory
from .training.train import train_and_persist_models

logger = logging.getLogger("fitness_trend.api")


def analyze_personnel_fitness(army_number, goal="Overall Fitness", regenerate=False, language="en", report_date=None):
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
            touch_fitness_report_timestamp(clean_army_no)
            now_12hr = datetime.now().strftime('%d/%m/%Y, %I:%M %p')
            saved['generated_at_str'] = now_12hr
            saved['date_time_12hr'] = now_12hr
            soldier_features = _reconstruct_soldier_features(saved)
            prediction = _ensure_complete_prediction(saved['prediction_result'], soldier_features)
            progression = _ensure_complete_progression(saved['progression_prediction'], soldier_features, prediction)
            recommendations = _ensure_complete_recommendations(saved.get('recommendations'), soldier_features)
            return {
                'success': True,
                'soldier': soldier_features,
                'prediction': prediction,
                'recommendations': recommendations,
                'progression': progression,
                'report_id': saved.get('id'),
                'cached': True,
                'generated_at': now_12hr,
                'date_time_12hr': now_12hr
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
    prediction = _ensure_complete_prediction(prediction, features)
    
    # 5. Recommendations
    recommendations = generate_full_recommendations(features, goal=goal, report_date=report_date)
    
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
        'fitness_status': 'Unfit' if (features.get('weight_deviation_percent') is not None and float(features.get('weight_deviation_percent')) >= 11.0) else 'Healthy',
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
    now_12hr = datetime.now().strftime('%d/%m/%Y, %I:%M %p')

    return {
        'success': True,
        'soldier': features,
        'prediction': prediction,
        'recommendations': recommendations,
        'progression': progression,
        'report_id': report_id,
        'cached': False,
        'generated_at': now_12hr,
        'date_time_12hr': now_12hr
    }


def regenerate_personnel_fitness_report(army_number, goal="Overall Fitness", language="en", report_date=None):
    """
    Explicitly forces recalculation and updates the ai_fitness_reports table.
    """
    return analyze_personnel_fitness(army_number, goal=goal, regenerate=True, language=language, report_date=report_date)


def get_saved_fitness_report_by_id(report_id):
    """
    Fetches a saved AI fitness report directly by primary key.
    """
    return get_saved_report_by_id(report_id)


def calculate_all_individuals_fitness(goal="Overall Fitness", language="English", task_id=None, is_aborted=None):
    """
    Evaluates fitness for all individuals in the unit (all personnel in weight_info),
    persists/updates their evaluation in `ums.ai_fitness_reports`, and computes
    a breakdown of fit vs unfit personnel for CO, 2IC, and Adjutant oversight.
    Supports atomic transactional rollback if aborted by user.
    """
    logger.info(f"Initiating batch fitness calculation for all individuals (task_id={task_id})...")
    ensure_ai_fitness_reports_table()

    # 1. Preload models & cached menus
    load_cached_models()

    # 2. Fetch all personnel joined data
    p_rows, w_rows, s_rows, ideal_weights = fetch_all_personnel_fitness_data()
    if not w_rows:
        return {
            'success': False,
            'error': 'No personnel found in weight_info table.',
            'total_processed': 0,
            'unfit_count': 0,
            'fit_count': 0,
            'unfit_personnel': []
        }

    # Index personnel and sports by normalized army_number
    p_map = {str(p.get('army_number', '')).strip(): p for p in p_rows}
    s_map = {}
    for s in s_rows:
        ano = str(s.get('army_number', '')).strip()
        s_map.setdefault(ano, []).append(s)

    # Deduplicate weight_info rows by army_number so each soldier is only evaluated once
    unique_w_map = {}
    for w in w_rows:
        ano = str(w.get('army_number', '')).strip()
        if ano:
            unique_w_map[ano] = w
    w_rows = list(unique_w_map.values())

    reports_payload_list = []
    unfit_personnel = []
    unfit_count = 0
    fit_count = 0

    for idx, w_row in enumerate(w_rows):
        # Abort check during evaluation loop
        if is_aborted and is_aborted():
            logger.warning(f"Calculation aborted by user at record {idx+1}/{len(w_rows)} (task_id={task_id}). Rolling back transaction.")
            return {
                'success': False,
                'aborted': True,
                'error': 'Calculation was aborted by user. Transaction rolled back: zero database changes were made.',
                'total_processed': 0,
                'unfit_count': 0,
                'fit_count': 0,
                'unfit_personnel': []
            }

        ano = str(w_row.get('army_number', '')).strip()
        if not ano:
            continue

        p_row = p_map.get(ano)
        sports = s_map.get(ano, [])

        # Feature Engineering
        features = generate_features_for_soldier(p_row, w_row, sports, ideal_weights)

        # AI Prediction
        prediction = predict_soldier_fitness(features)
        prediction = _ensure_complete_prediction(prediction, features)

        # Recommendations & Progression
        recommendations = generate_full_recommendations(features, goal=goal)
        progression = generate_fitness_progression_trajectory(
            features,
            predicted_score=prediction.get('fitness_score'),
            goal=goal
        )

        score = prediction.get('fitness_score')

        # Determine Unfit vs Fit: ONLY if weight status & difference overweight is starting from 11% (including 11%)
        dev_pct = features.get('weight_deviation_percent')
        if dev_pct is None and features.get('ideal_weight_kg') and features.get('actual_weight_kg'):
            try:
                ideal_w = float(features.get('ideal_weight_kg'))
                actual_w = float(features.get('actual_weight_kg'))
                if ideal_w > 0:
                    dev_pct = round(((actual_w - ideal_w) / ideal_w) * 100.0, 2)
            except Exception:
                dev_pct = None

        is_unfit = (dev_pct is not None and float(dev_pct) >= 11.0)
        status_label = 'Unfit' if is_unfit else 'Healthy'

        if is_unfit:
            unfit_count += 1
            unfit_personnel.append({
                'army_number': ano,
                'name': features.get('name', 'Soldier'),
                'rank': features.get('rank', 'Soldier'),
                'company': features.get('company', 'Unit HQ'),
                'score': score,
                'fitness_status': status_label,
                'bmi': features.get('bmi'),
                'actual_weight_kg': features.get('actual_weight_kg'),
                'ideal_weight_kg': features.get('ideal_weight_kg'),
                'weight_deviation_percent': dev_pct
            })
        else:
            fit_count += 1

        report_payload = {
            'personnel_id': features.get('personnel_id'),
            'army_number': ano,
            'name': features.get('name'),
            'rank': features.get('rank'),
            'company': features.get('company'),
            'age': features.get('age'),
            'height_cm': features.get('height_cm'),
            'actual_weight_kg': features.get('actual_weight_kg'),
            'ideal_weight_kg': features.get('ideal_weight_kg'),
            'bmi': features.get('bmi'),
            'fitness_score': score,
            'fitness_status': status_label,
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
        reports_payload_list.append(report_payload)

    # Final abort check right before persistence
    if is_aborted and is_aborted():
        logger.warning(f"Calculation aborted by user before database persistence (task_id={task_id}). Rolling back transaction.")
        return {
            'success': False,
            'aborted': True,
            'error': 'Calculation was aborted by user. Transaction rolled back: zero database changes were made.',
            'total_processed': 0,
            'unfit_count': 0,
            'fit_count': 0,
            'unfit_personnel': []
        }

    # 3. Bulk persist to ums.ai_fitness_reports in a single ACID transaction
    save_result = bulk_insert_or_update_ai_fitness_reports(reports_payload_list)

    msg = f"Successfully calculated fitness for {len(reports_payload_list)} individuals. Added/updated in ums.ai_fitness_reports. Unfit individuals: {unfit_count}, Fit individuals: {fit_count}."
    logger.info(msg)

    return {
        'success': True,
        'total_processed': len(reports_payload_list),
        'unfit_count': unfit_count,
        'fit_count': fit_count,
        'unfit_personnel': unfit_personnel,
        'saved': save_result,
        'message': msg
    }


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
    if not isinstance(diet, dict) or not diet.get('macros') or not diet.get('sample_menu') or not diet.get('mess_category'):
        recs['diet'] = fresh_recs['diet']
    elif not diet.get('strategy'):
        diet['strategy'] = fresh_recs['diet'].get('strategy', '')

    if not recs.get('medical_notice'):
        recs['medical_notice'] = fresh_recs['medical_notice']
    ex = recs.get('exercise')
    if not ex or not ex.get('exercises') or not any('rest' in x for x in ex.get('exercises', [])):
        recs['exercise'] = fresh_recs['exercise']

    return recs


def _generate_soldier_strengths(soldier, pred=None):
    """
    Synthesizes technically accurate, context-aware positive predictive factors (strengths)
    based on the soldier's actual demographic, physical, medical, and athletic attributes.
    """
    strengths = []
    age = soldier.get('age') or 26
    svc = soldier.get('service_years') or 4
    bmi = float(soldier.get('bmi') or 22.0)
    dev_pct = float(soldier.get('weight_deviation_percent') or 0.0)
    bpet = str(soldier.get('bpet_grade') or '').upper()
    ppt = str(soldier.get('ppt_grade') or '').upper()
    has_sport = soldier.get('has_sport') or (soldier.get('sport_count', 0) > 0)
    is_med_restricted = soldier.get('has_medical_restriction') or soldier.get('is_low_medical_category')

    if not is_med_restricted:
        strengths.append("Medical SHAPE-1 Clearance: Fully cleared for unrestricted high-tempo physical conditioning with zero active contraindications.")
    
    if 18.5 <= bmi <= 24.9:
        strengths.append(f"Healthy Body Composition: BMI ({bmi}) supports optimal tactical agility, endurance, and field mobility.")
    elif abs(dev_pct) <= 10.0:
        strengths.append("Authorized Weight Range: Current body weight is within permissible military SHAPE-1 authorization benchmark.")
    
    if bpet in ['EXCELLENT', 'GOOD']:
        strengths.append(f"High BPET Endurance: Graded '{bpet}' in military physical endurance standards and 5km road run.")
    if ppt in ['EXCELLENT', 'GOOD']:
        strengths.append(f"Solid Physical Proficiency: Graded '{ppt}' in military calisthenics, chin-ups, and sprint agility.")
    
    if has_sport:
        sport_name = soldier.get('primary_sport') or soldier.get('sports_list') or 'Athletics'
        strengths.append(f"Athletic Engagement: Regularly participates in active unit sports competitions ({sport_name}).")
    
    if len(strengths) < 2:
        strengths.append(f"Demographic Baseline Resilience: Optimal operational age ({age} yrs, {svc} yrs service) provides strong conditioning capacity.")
    if len(strengths) < 3:
        strengths.append("Metabolic Responsiveness: High physiological receptivity to structured military nutrition and targeted conditioning protocols.")
    if len(strengths) < 4:
        strengths.append("Cardiovascular Foundation: Baseline aerobic capacity capable of sustaining progressive 5km road-run tempos.")

    return strengths[:4]


def _generate_soldier_improvements(soldier, pred=None):
    """
    Synthesizes priority conditioning and improvement areas based on the soldier's
    body metrics, medical profile, or assigns maintenance conditioning targets.
    """
    improvements = []
    bmi = float(soldier.get('bmi') or 22.0)
    cur_wt = float(soldier.get('actual_weight_kg') or 70.0)
    ideal_wt = float(soldier.get('ideal_weight_kg') or cur_wt)
    diff_wt = round(cur_wt - ideal_wt, 1)
    bpet = str(soldier.get('bpet_grade') or '').upper()
    ppt = str(soldier.get('ppt_grade') or '').upper()
    is_med_restricted = soldier.get('has_medical_restriction') or soldier.get('is_low_medical_category')
    has_sport = soldier.get('has_sport') or (soldier.get('sport_count', 0) > 0)

    if diff_wt > 2.0:
        improvements.append(f"Body Weight Optimization: Target progressive reduction of +{diff_wt} kg excess body weight toward authorized military standard.")
    elif diff_wt < -2.0:
        improvements.append(f"Lean Mass Accretion: Target progressive gain of +{abs(diff_wt)} kg lean muscle mass to meet standard.")

    if bmi >= 25.0:
        improvements.append(f"Elevated BMI ({bmi}): Implement moderate caloric deficit and structured aerobic fat-oxidation drills.")
    elif bmi < 18.5:
        improvements.append(f"Low BMI ({bmi}): Increase daily caloric density and high-protein intake for muscle stabilization.")

    if is_med_restricted:
        restr = soldier.get('restrictions') or soldier.get('medical_problem') or 'Low medical category limitations'
        improvements.append(f"Medical Adherence: Strictly observe prescribed restrictions ({restr}); avoid high-impact joint loading.")

    if bpet not in ['EXCELLENT', 'GOOD']:
        improvements.append("BPET Road-Run Conditioning: Improve 5km pacing and aerobic threshold to achieve Good/Excellent standard.")

    if ppt not in ['EXCELLENT', 'GOOD']:
        improvements.append("Calisthenics & Agility: Elevate chin-ups, push-up repetitions, and horizontal rope traverse endurance.")

    if not has_sport:
        improvements.append("Battalion Sports Participation: Actively participate in scheduled unit athletic and intramural sports.")

    if not improvements:
        improvements = [
            "Threshold Aerobic Stamina: Sustain high-intensity interval training (HIIT) to maintain peak cardiovascular VO2 max.",
            "Tactical Load Carriage: Progressively incorporate weighted endurance marches (BPET battle-load conditioning).",
            "Core & Lumbar Spine Stability: Integrate functional abdominal, glute bridge, and spinal stability drills.",
            "Hydration Discipline: Maintain strict 3.5+ L daily hydration and electrolyte replenishment during field exercises."
        ]

    return improvements[:4]


def _ensure_complete_prediction(prediction, soldier_features):
    """
    Guarantees that prediction payload always contains non-empty, technically
    accurate Positive Predictive Factors (strengths) and Priority Areas Requiring Improvement
    (improvements), derived from the soldier's physical profile.
    """
    if not isinstance(prediction, dict):
        prediction = {}

    strengths = prediction.get('strengths') or prediction.get('key_strengths')
    if not isinstance(strengths, list) or len(strengths) == 0:
        strengths = _generate_soldier_strengths(soldier_features, prediction)

    improvements = prediction.get('improvements') or prediction.get('risk_factors')
    if not isinstance(improvements, list) or len(improvements) == 0:
        improvements = _generate_soldier_improvements(soldier_features, prediction)

    prediction['strengths'] = strengths
    prediction['key_strengths'] = strengths
    prediction['improvements'] = improvements
    prediction['risk_factors'] = improvements
    return prediction


