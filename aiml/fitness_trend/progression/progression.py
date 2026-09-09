"""
Goal-based Progress Estimation Engine.
Calculates realistic 30, 60, and 90-day physiological and performance progression trajectories.
Clearly labeled as goal-based estimates to uphold medical and scientific integrity.
"""

from ..features.bmi import calculate_bmi


def generate_fitness_progression_trajectory(soldier_features, predicted_score=None, goal="Overall Fitness"):
    """
    Computes expected 30, 60, and 90-day progression milestones based on baseline conditioning and adherence.
    
    Returns:
        dict: {
            'is_projection_estimate': True,
            'disclaimer': str,
            'goal_selected': str,
            'milestones': list of milestone dicts (Current, 30-Day, 60-Day, 90-Day),
            'chart_data': {
                'labels': list,
                'weight_series': list,
                'bmi_series': list,
                'score_series': list
            }
        }
    """
    cur_wt = soldier_features.get('actual_weight_kg') or 70.0
    ideal_wt = soldier_features.get('ideal_weight_kg') or cur_wt
    ht = soldier_features.get('height_cm') or 172.0
    cur_bmi = soldier_features.get('bmi') or 23.5
    cur_score = float(predicted_score) if predicted_score is not None else float(soldier_features.get('ground_truth_score', 70.0))
    dev_pct = soldier_features.get('weight_deviation_percent') or 0.0
    
    # Estimate monthly rate of safe weight adjustment (max 1.5 - 2.0 kg/month)
    if dev_pct > 5.0:
        # Overweight: target gradual fat loss towards ideal weight
        excess_kg = cur_wt - ideal_wt
        w_delta_30 = -min(1.8, excess_kg * 0.35)
        w_delta_60 = -min(3.5, excess_kg * 0.70)
        w_delta_90 = -min(5.0, excess_kg * 0.95)
    elif dev_pct < -5.0:
        # Underweight: target gradual lean mass gain
        deficit_kg = ideal_wt - cur_wt
        w_delta_30 = min(1.2, deficit_kg * 0.35)
        w_delta_60 = min(2.4, deficit_kg * 0.70)
        w_delta_90 = min(3.5, deficit_kg * 0.90)
    else:
        # Maintenance: minimal weight change
        w_delta_30 = 0.0
        w_delta_60 = 0.0
        w_delta_90 = 0.0
        
    wt_30 = round(cur_wt + w_delta_30, 1)
    wt_60 = round(cur_wt + w_delta_60, 1)
    wt_90 = round(cur_wt + w_delta_90, 1)
    
    bmi_30 = calculate_bmi(wt_30, ht) or cur_bmi
    bmi_60 = calculate_bmi(wt_60, ht) or cur_bmi
    bmi_90 = calculate_bmi(wt_90, ht) or cur_bmi
    
    # Readiness Score progression (estimated improvement with regular PT and diet)
    headroom = 100.0 - cur_score
    score_30 = round(min(100.0, cur_score + (headroom * 0.25)), 1)
    score_60 = round(min(100.0, cur_score + (headroom * 0.55)), 1)
    score_90 = round(min(100.0, cur_score + (headroom * 0.85)), 1)
    
    # BPET & PPT Performance Milestones
    bpet_val = soldier_features.get('bpet_score') if soldier_features.get('bpet_score') is not None else 80
    ppt_val = soldier_features.get('ppt_score') if soldier_features.get('ppt_score') is not None else 80

    if goal == 'BPET Improvement' or bpet_val < 80:
        bpet_desc_cur = "Current baseline 5km pace (approx. 24:30 mins)"
        bpet_desc_30 = "Improved aerobic base (5km pacing target: 23:30 mins)"
        bpet_desc_60 = "Enhanced tempo & rope agility (5km target: 22:45 mins)"
        bpet_desc_90 = "Peak Tactical BPET Readiness (5km target: < 22:00 mins - Excellent standard)"
    else:
        bpet_desc_cur = "Standard military aerobic endurance baseline"
        bpet_desc_30 = "+10% cardiovascular stamina and rapid post-PT recovery"
        bpet_desc_60 = "+20% aerobic capacity with consistent high pacing"
        bpet_desc_90 = "Sustained peak aerobic readiness and obstacle mastery"
        
    if goal == 'PPT Improvement' or ppt_val < 80:
        ppt_desc_cur = "Baseline calisthenics & 2.4km timing"
        ppt_desc_30 = "+2 strict chin-ups, 35+ push-ups, sub 10:30 min 2.4km"
        ppt_desc_60 = "+4 strict chin-ups, 45+ push-ups, sub 10:00 min 2.4km"
        ppt_desc_90 = "10+ continuous chin-ups, 50+ push-ups, sub 9:30 min 2.4km (Excellent)"
    else:
        ppt_desc_cur = "Standard physical proficiency test baseline"
        ppt_desc_30 = "Improved muscular endurance in core & upper push-pull"
        ppt_desc_60 = "High calisthenics power and fast 2.4km interval speed"
        ppt_desc_90 = "Top-tier physical proficiency index across all tests"
        
    milestones = [
        {
            'period': 'Current Baseline',
            'days': 0,
            'weight_kg': cur_wt,
            'bmi': cur_bmi,
            'fitness_score': cur_score,
            'bpet_target': bpet_desc_cur,
            'ppt_target': ppt_desc_cur,
            'badge': 'secondary'
        },
        {
            'period': '30 Days Projected',
            'days': 30,
            'weight_kg': wt_30,
            'bmi': bmi_30,
            'fitness_score': score_30,
            'bpet_target': bpet_desc_30,
            'ppt_target': ppt_desc_30,
            'badge': 'info'
        },
        {
            'period': '60 Days Projected',
            'days': 60,
            'weight_kg': wt_60,
            'bmi': bmi_60,
            'fitness_score': score_60,
            'bpet_target': bpet_desc_60,
            'ppt_target': ppt_desc_60,
            'badge': 'primary'
        },
        {
            'period': '90 Days Projected',
            'days': 90,
            'weight_kg': wt_90,
            'bmi': bmi_90,
            'fitness_score': score_90,
            'bpet_target': bpet_desc_90,
            'ppt_target': ppt_desc_90,
            'badge': 'success'
        }
    ]
    
    return {
        'is_projection_estimate': True,
        'disclaimer': 'Goal-based physiological progress estimate assuming consistent adherence to the recommended tactical training and nutrition schedule. Not a medically guaranteed forecast.',
        'goal_selected': goal,
        'milestones': milestones,
        'chart_data': {
            'labels': ['Current', '30 Days', '60 Days', '90 Days'],
            'weight_series': [cur_wt, wt_30, wt_60, wt_90],
            'bmi_series': [cur_bmi, bmi_30, bmi_60, bmi_90],
            'score_series': [cur_score, score_30, score_60, score_90]
        },
        'trajectory_30d': {
            'projected_fitness_score': score_30,
            'projected_weight_kg': wt_30,
            'projected_bmi': bmi_30,
            'bmi': bmi_30
        },
        'trajectory_60d': {
            'projected_fitness_score': score_60,
            'projected_weight_kg': wt_60,
            'projected_bmi': bmi_60,
            'bmi': bmi_60
        },
        'trajectory_90d': {
            'projected_fitness_score': score_90,
            'projected_weight_kg': wt_90,
            'projected_bmi': bmi_90,
            'bmi': bmi_90
        }
    }
