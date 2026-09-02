"""
Medical Safety Filter and Contraindication Gate.
Prevents recommending unsafe physical movements for soldiers with medical categories or injuries.
"""


def get_medical_clearance_notice(soldier_features):
    """
    Returns standard military medical clearance advisories.
    """
    has_restr = soldier_features.get('has_medical_restriction')
    warning = soldier_features.get('medical_safety_warning')
    
    if has_restr:
        return {
            'status': 'RESTRICTED',
            'alert_class': 'danger',
            'title': 'Active Medical Restrictions Applied',
            'message': warning or 'Physical activities are modified to comply with registered medical restrictions and low medical category parameters. Medical officer clearance required prior to high-intensity training.',
            'is_restricted': True
        }
    else:
        return {
            'status': 'CLEARED',
            'alert_class': 'success',
            'title': 'Medically Cleared (SHAPE-1)',
            'message': 'Soldier is medically cleared for standard military physical training and advanced tactical conditioning.',
            'is_restricted': False
        }


def filter_unsafe_exercises(candidate_exercises, soldier_features):
    """
    Filters out any exercise that conflicts with the soldier's recorded medical restrictions.
    Provides safer, low-impact alternatives where appropriate.
    
    Returns:
        tuple: (safe_exercises_list, blocked_exercises_list)
    """
    contraindicated = set(soldier_features.get('contraindicated_exercises', []))
    contra_cats = set(soldier_features.get('contraindicated_categories', []))
    is_lmc = bool(soldier_features.get('is_low_medical_category'))
    
    safe_list = []
    blocked_list = []
    
    for item in candidate_exercises:
        ex_name = item.get('exercise', '')
        ex_type = item.get('type', '')
        
        # Check direct name collision
        if ex_name in contraindicated:
            blocked_list.append({
                'exercise': ex_name,
                'reason': 'Directly contraindicated by recorded medical condition/restriction.'
            })
            continue
            
        # Check anatomical category constraints
        if 'spine_back' in contra_cats and ex_type in ['heavy_lifting', 'spinal_loading', 'high_impact_jump', 'deep_bend']:
            blocked_list.append({
                'exercise': ex_name,
                'reason': 'Contraindicated due to spine/back restriction (avoids axial spinal loading).'
            })
            continue
            
        if 'knee_lower_limb' in contra_cats and ex_type in ['deep_squat', 'high_impact_plyo', 'sprint_incline']:
            blocked_list.append({
                'exercise': ex_name,
                'reason': 'Contraindicated due to knee/lower limb condition (avoids high knee shear stress).'
            })
            continue
            
        if is_lmc and item.get('intensity') == 'High':
            # Downgrade intensity rather than completely blocking if exercise is otherwise safe
            item_copy = dict(item)
            item_copy['intensity'] = 'Low - Moderate'
            item_copy['sets'] = max(2, item.get('sets', 3) - 1)
            item_copy['notes'] = "Intensity downgraded due to Medical Category."
            safe_list.append(item_copy)
            continue
            
        safe_list.append(item)
        
    # If key routines were blocked, inject medically safe rehabilitation / conditioning exercises
    if 'spine_back' in contra_cats:
        safe_list.append({
            'exercise': 'Bird-Dog & McGill Curl-Up (Core Stabilization)',
            'type': 'core_rehab',
            'sets': 3,
            'reps': '8-10 holds (6 sec each)',
            'duration': '10 mins',
            'frequency': '4 days/week',
            'rest': '60 sec',
            'intensity': 'Low',
            'notes': 'Spine-safe core stabilization recommended for low back resilience.'
        })
        safe_list.append({
            'exercise': 'Brisk Walking / Swimming',
            'type': 'low_impact_cardio',
            'sets': 1,
            'reps': 'Continuous',
            'duration': '30 mins',
            'frequency': '5 days/week',
            'rest': 'N/A',
            'intensity': 'Low - Moderate',
            'notes': 'Non-impact cardiovascular conditioning.'
        })
        
    if 'knee_lower_limb' in contra_cats:
        safe_list.append({
            'exercise': 'Straight Leg Raises & Glute Bridges',
            'type': 'lower_rehab',
            'sets': 3,
            'reps': '12-15 reps',
            'duration': '12 mins',
            'frequency': '4 days/week',
            'rest': '45 sec',
            'intensity': 'Low',
            'notes': 'Low-impact knee stability & quadriceps strengthening.'
        })
        
    return safe_list, blocked_list
