"""
Medical & Restriction Features Module for AI/ML Fitness Trend.
Identifies medical contraindications and safety risk flags.
"""

from ..config import RESTRICTION_KEYWORDS


def extract_medical_features(soldier_data):
    """
    Analyzes medical categories, medical problems, and written restrictions.
    
    Returns:
        dict: {
            'has_medical_restriction': int (0 or 1),
            'is_low_medical_category': int (0 or 1),
            'medical_risk_penalty': float,
            'contraindicated_categories': list of str,
            'contraindicated_exercises': list of str,
            'medical_safety_warning': str or None,
            'clearance_status': str ('Fully Cleared', 'Conditional / Restricted', 'Medical Evaluation Required')
        }
    """
    is_lmc = 1 if soldier_data.get('is_lmc') else 0
    med_problem = (soldier_data.get('medical_problem') or '').lower()
    restrictions = (soldier_data.get('restrictions') or '').lower()
    
    combined_text = f"{med_problem} {restrictions}".strip()
    
    contraindicated_cats = []
    contraindicated_exercises = []
    
    # Check each anatomical / systemic condition
    for cat_name, keywords in RESTRICTION_KEYWORDS.items():
        for kw in keywords:
            if kw in combined_text:
                if cat_name not in contraindicated_cats:
                    contraindicated_cats.append(cat_name)
                break
                
    if 'spine_back' in contraindicated_cats:
        contraindicated_exercises.extend([
            'Heavy Deadlifts', 'Barbell Back Squats', 'Forward Bending Exercises (PPG)',
            'Weighted Overhead Press', 'Rope Climbing with Load', 'Heavy Weight Lifting'
        ])
        
    if 'knee_lower_limb' in contraindicated_cats:
        contraindicated_exercises.extend([
            'Deep Barbell Squats', 'Box Jumps', 'Sprint Intervals',
            'Cross Country Running with Load', 'High-Impact Jumping', 'Prolonged Standing PPG'
        ])
        
    if 'shoulder_upper_limb' in contraindicated_cats:
        contraindicated_exercises.extend([
            'Heavy Bench Press', 'Overhead Military Press', 'Rope Climbing',
            'Heavy Push-ups with Deficit', 'Heavy Arms Handling'
        ])
        
    if 'cardiovascular' in contraindicated_cats:
        contraindicated_exercises.extend([
            'Maximal 1-Rep Heavy Lifting', 'Valsalva Maneuver Straining',
            'Exhaustive 5km Sprinting without Gradual Warm-up'
        ])
        
    has_restr = 1 if (contraindicated_cats or restrictions or med_problem or is_lmc) else 0
    
    # Calculate penalty score (0 to 30 pts deduction)
    penalty = 0.0
    if is_lmc:
        penalty += 15.0
    if contraindicated_cats:
        penalty += len(contraindicated_cats) * 5.0
    if restrictions:
        penalty += 5.0
    penalty = min(30.0, penalty)
    
    if is_lmc or 'spine_back' in contraindicated_cats or 'knee_lower_limb' in contraindicated_cats:
        clearance = "Conditional / Restricted"
        warning = "Soldier has recorded medical conditions/restrictions. High-impact routines are blocked. Doctor clearance required."
    elif has_restr:
        clearance = "Conditional / Restricted"
        warning = "Soldier has active restrictions. Routine customized to avoid contraindicated strain."
    else:
        clearance = "Fully Cleared"
        warning = None
        
    return {
        'has_medical_restriction': has_restr,
        'is_low_medical_category': is_lmc,
        'medical_risk_penalty': penalty,
        'contraindicated_categories': contraindicated_cats,
        'contraindicated_exercises': list(set(contraindicated_exercises)),
        'medical_safety_warning': warning,
        'clearance_status': clearance
    }
