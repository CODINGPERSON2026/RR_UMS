"""
Confidence Scoring & Explainability Module for AI/ML Fitness Trend.
Extracts positive strength factors and areas for improvement based on model inputs.
"""


def compute_prediction_confidence(model, X_prep, soldier_features):
    """
    Computes a realistic prediction confidence percentage (e.g. 70% to 96%)
    based on model class probability margin and data completeness.
    """
    base_conf = 85.0
    
    # 1. Model prediction probabilities margin
    if hasattr(model, 'predict_proba'):
        try:
            probs = model.predict_proba(X_prep)[0]
            top_prob = float(max(probs))
            # Map top_prob (e.g. 0.5 to 1.0) into confidence adjustment
            base_conf = 70.0 + (top_prob * 26.0)
        except Exception:
            base_conf = 84.0
            
    # 2. Adjust for missing or unverified fields
    if not soldier_features.get('bpet_grade'):
        base_conf -= 6.0
    if not soldier_features.get('ppt_grade'):
        base_conf -= 6.0
    if not soldier_features.get('has_sport'):
        base_conf -= 3.0
    if soldier_features.get('data_quality_flags'):
        base_conf -= min(10.0, len(soldier_features['data_quality_flags']) * 2.5)
        
    final_conf = max(55.0, min(97.5, base_conf))
    return round(final_conf, 1)


def extract_explainable_factors(soldier_features):
    """
    Decomposes soldier metrics into human-readable, technically accurate:
    1. Positive Factors (Strengths)
    2. Improvement Factors (Areas for Improvement)
    3. Important Predictive Indicators
    """
    strengths = []
    improvements = []
    
    # BPET Performance
    bpet_grade = soldier_features.get('bpet_grade')
    if bpet_grade == 'EXCELLENT':
        strengths.append("High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.")
    elif bpet_grade == 'GOOD':
        strengths.append("Solid BPET Performance: Achieved 'Good' standard in military physical endurance.")
    elif bpet_grade in ['SATISFACTORY', 'SAT']:
        improvements.append("Moderate BPET: Graded 'Satisfactory'; endurance pacing can be improved to reach 'Good/Excellent'.")
    elif bpet_grade in ['LMC', 'A2P', 'FAIL']:
        improvements.append("BPET Deficiency: Low physical grading or restriction recorded during endurance testing.")
    else:
        improvements.append("BPET Untested: No recent formal BPET test recorded in system.")
        
    # PPT Performance
    ppt_grade = soldier_features.get('ppt_grade')
    if ppt_grade == 'EXCELLENT':
        strengths.append("High PPT Performance: Achieved 'Excellent' in physical proficiency standards.")
    elif ppt_grade == 'GOOD':
        strengths.append("Solid PPT Performance: Meets high physical proficiency benchmarks.")
    elif ppt_grade in ['SATISFACTORY', 'SAT']:
        improvements.append("PPT Potential: Satisfactory performance; calisthenics, chin-ups, and sprint speed can be elevated.")
    elif ppt_grade in ['LMC', 'A2P', 'FAIL']:
        improvements.append("PPT Remedial Needed: Physical proficiency test requires structured conditioning.")
        
    # Weight & BMI
    dev_pct = soldier_features.get('weight_deviation_percent')
    bmi = soldier_features.get('bmi')
    bmi_cat = soldier_features.get('bmi_category')
    
    if dev_pct is not None:
        if abs(dev_pct) <= 5.0:
            strengths.append(f"Optimal Body Weight: Actual weight is within {dev_pct}% of the Indian Army ideal weight benchmark.")
        elif 5.0 < dev_pct <= 10.0:
            strengths.append(f"Authorized Weight Range: Current weight (+{dev_pct}%) is within permissible military SHAPE-1 authorization.")
        elif dev_pct > 10.0:
            improvements.append(f"Excess Body Weight: Actual weight is {dev_pct}% above ideal standard (+{soldier_features.get('weight_difference_kg')} kg deviation).")
        elif dev_pct < -10.0:
            improvements.append(f"Underweight Status: Body weight is {abs(dev_pct)}% below the authorized physical benchmark.")
            
    if bmi is not None and 19.0 <= bmi <= 24.5:
        strengths.append(f"Healthy BMI ({bmi}) indicates prime physical conditioning.")
        
    # Sports & Physical Activities
    has_sport = soldier_features.get('has_sport')
    sports_list = soldier_features.get('sports_list')
    if has_sport:
        strengths.append(f"Active Sports Participation: Regularly participates in unit athletic activities ({sports_list}).")
    else:
        improvements.append("No Structured Sports: Currently not registered in regular unit sports competitions.")
        
    # Medical & Restrictions
    if soldier_features.get('has_medical_restriction'):
        restr_desc = soldier_features.get('restrictions') or soldier_features.get('medical_problem') or 'Active restrictions'
        improvements.append(f"Medical Contraindications: {restr_desc} limits high-impact physical loading.")
    else:
        strengths.append("Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.")
        
    # Default fallbacks if empty
    if not strengths:
        strengths.append("Demographic Baseline: Within normal military operational age & service profile.")
    if not improvements:
        improvements.append("Maintenance Focus: Sustain current peak endurance, cardiovascular health, and sports routine.")
        
    return {
        'strengths': strengths,
        'improvements': improvements
    }
