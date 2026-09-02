"""
Unified Feature Engineering Pipeline for AI/ML Fitness Trend.
Builds complete ML feature vectors, explainable attributes, and baseline readiness indices.
"""

from .bmi import calculate_bmi, get_bmi_category
from .ideal_weight import calculate_ideal_weight_and_deviation
from .sports_features import extract_sports_features
from .medical_features import extract_medical_features
from ..data.data_validator import validate_and_clean_soldier_data
from ..data.data_aggregator import aggregate_sports_for_personnel
from ..config import FITNESS_CATEGORIES


# List of numerical/encoded feature names used for ML Model input
ML_FEATURE_COLUMNS = [
    'age',
    'height_cm',
    'actual_weight_kg',
    'ideal_weight_kg',
    'weight_difference_kg',
    'weight_deviation_percent',
    'bmi',
    'service_years',
    'bpet_score',
    'ppt_score',
    'sport_count',
    'has_sport',
    'team_sport_indicator',
    'individual_sport_indicator',
    'endurance_sport_indicator',
    'strength_sport_indicator',
    'combat_sport_indicator',
    'water_sport_indicator',
    'has_medical_restriction',
    'is_low_medical_category',
    'medical_risk_penalty'
]


def compute_ground_truth_fitness_score(features):
    """
    Computes a standardized Military Physical Readiness Ground Truth Score (0 - 100)
    derived rigorously from verified historical test standards:
    - BPET Score (35% weight)
    - PPT Score (35% weight)
    - Weight / BMI Deviation Authorization (20% weight)
    - Sports & Activity Participation (10% bonus / weight)
    - Deductions for active Low Medical Category / Medical Restrictions.
    
    Returns:
        float score (0.0 to 100.0)
    """
    # Base components
    bpet = features.get('bpet_score')
    ppt = features.get('ppt_score')
    dev_pct = features.get('weight_deviation_percent')
    sports_bonus = features.get('sports_readiness_score', 0.0)
    med_penalty = features.get('medical_risk_penalty', 0.0)
    
    # Defaults if tests not yet conducted (impute to median standard 70)
    bpet_eff = bpet if bpet is not None else 70.0
    ppt_eff = ppt if ppt is not None else 70.0
    
    # Physical tests subtotal (max 70 pts)
    phys_subtotal = (bpet_eff * 0.35) + (ppt_eff * 0.35)
    
    # Weight deviation score (max 20 pts)
    # 0% dev -> 20 pts; +/- 5% -> 18 pts; +/- 10% -> 14 pts; +/- 20% -> 5 pts; >25% -> 0 pts
    if dev_pct is None:
        wt_score = 14.0
    else:
        abs_dev = abs(dev_pct)
        if abs_dev <= 3.0:
            wt_score = 20.0
        elif abs_dev <= 7.0:
            wt_score = 17.0
        elif abs_dev <= 12.0:
            wt_score = 13.0
        elif abs_dev <= 18.0:
            wt_score = 8.0
        else:
            wt_score = max(0.0, 20.0 - abs_dev)
            
    # Sports bonus (max 10 pts)
    sp_score = min(10.0, sports_bonus * 0.5)
    
    total_score = phys_subtotal + wt_score + sp_score - med_penalty
    total_score = max(10.0, min(100.0, total_score))
    return round(total_score, 1)


def score_to_fitness_category(score):
    """
    Maps 0-100 fitness score to canonical category label.
    """
    if score is None:
        return "UNKNOWN"
    if score >= FITNESS_CATEGORIES["EXCELLENT"]["min_score"]:
        return "EXCELLENT"
    elif score >= FITNESS_CATEGORIES["GOOD"]["min_score"]:
        return "GOOD"
    elif score >= FITNESS_CATEGORIES["AVERAGE"]["min_score"]:
        return "AVERAGE"
    else:
        return "NEEDS_IMPROVEMENT"


def generate_features_for_soldier(personnel_row, weight_row, sports_rows, ideal_weights_rows):
    """
    Complete end-to-end feature extraction for a single soldier.
    Returns:
        dict containing both ML feature dict, UI profile dict, and ground truth targets.
    """
    # 1. Clean & validate base soldier data
    soldier_base = validate_and_clean_soldier_data(personnel_row, weight_row)
    
    # 2. Compute BMI
    bmi = calculate_bmi(soldier_base['actual_weight_kg'], soldier_base['height_cm'])
    bmi_category, bmi_color, bmi_badge = get_bmi_category(bmi)
    
    # 3. Compute Ideal Weight & Deviation
    ideal_info = calculate_ideal_weight_and_deviation(
        soldier_base['height_cm'],
        soldier_base['actual_weight_kg'],
        soldier_base['age'],
        ideal_weights_rows
    )
    
    # 4. Extract Sports Features
    sports_info = extract_sports_features(sports_rows)
    
    # 5. Extract Medical Features
    med_info = extract_medical_features(soldier_base)
    
    # 6. Assemble Combined Feature Dict
    combined = {
        # Identifiers & Metadata (excluded from ML features)
        'army_number': soldier_base['army_number'],
        'name': soldier_base['name'],
        'rank': soldier_base['rank'],
        'company': soldier_base['company'],
        'trade': soldier_base['trade'],
        'section': soldier_base['section'],
        'data_quality_flags': soldier_base['data_quality_flags'],
        'is_sufficient_for_prediction': soldier_base['is_sufficient_for_prediction'],
        
        # Physical & Demographic features
        'age': soldier_base['age'],
        'height_cm': soldier_base['height_cm'],
        'actual_weight_kg': soldier_base['actual_weight_kg'],
        'ideal_weight_kg': ideal_info['ideal_weight_kg'],
        'weight_difference_kg': ideal_info['weight_difference_kg'],
        'weight_deviation_percent': ideal_info['weight_deviation_percent'],
        'weight_status': ideal_info['weight_status'],
        'weight_status_badge': ideal_info['weight_status_badge'],
        'is_within_shape_limits': ideal_info['is_within_shape_limits'],
        'bmi': bmi,
        'bmi_category': bmi_category,
        'bmi_color': bmi_color,
        'bmi_badge': bmi_badge,
        'service_years': soldier_base['service_years'],
        
        # Physical Testing features
        'bpet_grade': soldier_base['bpet_grade'],
        'bpet_score': soldier_base['bpet_score'],
        'ppt_grade': soldier_base['ppt_grade'],
        'ppt_score': soldier_base['ppt_score'],
        'bpet_date': soldier_base['bpet_date'],
        
        # Sports features
        'sport_count': sports_info['sport_count'],
        'has_sport': sports_info['has_sport'],
        'sports_list': sports_info['sports_list'],
        'primary_sport': sports_info['primary_sport'],
        'team_sport_indicator': sports_info['team_sport_indicator'],
        'individual_sport_indicator': sports_info['individual_sport_indicator'],
        'endurance_sport_indicator': sports_info['endurance_sport_indicator'],
        'strength_sport_indicator': sports_info['strength_sport_indicator'],
        'combat_sport_indicator': sports_info['combat_sport_indicator'],
        'water_sport_indicator': sports_info['water_sport_indicator'],
        'physical_activity_level': sports_info['physical_activity_level'],
        'sports_readiness_score': sports_info['sports_readiness_score'],
        
        # Medical & Restriction features
        'has_medical_restriction': med_info['has_medical_restriction'],
        'is_low_medical_category': med_info['is_low_medical_category'],
        'medical_risk_penalty': med_info['medical_risk_penalty'],
        'contraindicated_categories': med_info['contraindicated_categories'],
        'contraindicated_exercises': med_info['contraindicated_exercises'],
        'medical_safety_warning': med_info['medical_safety_warning'],
        'clearance_status': med_info['clearance_status'],
        'medical_problem': soldier_base['medical_problem'],
        'restrictions': soldier_base['restrictions'],
        'status_type': soldier_base['status_type'],
        'category_type': soldier_base['category_type']
    }
    
    # Ground truth calculations
    ground_truth_score = compute_ground_truth_fitness_score(combined)
    ground_truth_cat = score_to_fitness_category(ground_truth_score)
    
    combined['ground_truth_score'] = ground_truth_score
    combined['ground_truth_category'] = ground_truth_cat
    
    return combined


def generate_dataset_features(personnel_list, weight_list, sports_list, ideal_weights_list):
    """
    Extracts features for the entire database population.
    Returns:
        list of feature dicts for all soldiers.
    """
    from ..data.data_aggregator import aggregate_all_sports
    
    # Index weights by army_number
    weights_map = {}
    for w in weight_list:
        an = (w.get('army_number') or '').strip()
        if an:
            weights_map[an] = w
            
    # Index sports by army_number
    sports_map = {}
    for s in sports_list:
        an = (s.get('army_number') or '').strip()
        if an:
            if an not in sports_map:
                sports_map[an] = []
            sports_map[an].append(s)
            
    all_features = []
    for p in personnel_list:
        an = (p.get('army_number') or '').strip()
        if not an:
            continue
        w = weights_map.get(an)
        s_rows = sports_map.get(an, [])
        feat = generate_features_for_soldier(p, w, s_rows, ideal_weights_list)
        all_features.append(feat)
        
    return all_features
