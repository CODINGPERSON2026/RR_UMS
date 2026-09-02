"""
Ideal Weight Calculation & Deviation Analysis.
Accurately maps personnel height & age to standard Indian Military ideal_weights table.
"""

from ..config import VALID_BOUNDS


def parse_age_range(age_range_str):
    """
    Parses an age range string like '18-22', '23-27', '48-70'.
    Returns:
        tuple (min_age, max_age) or (None, None)
    """
    if not age_range_str:
        return None, None
    try:
        parts = str(age_range_str).strip().split('-')
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        elif len(parts) == 1 and parts[0].isdigit():
            val = int(parts[0])
            return val, val
    except Exception:
        return None, None
    return None, None


def get_ideal_weight_from_table(height_cm, age_years, ideal_weights_rows):
    """
    Finds matching ideal weight from table.
    1. Filters rows matching age in age_range (or closest age range if slightly out of bounds).
    2. Matches exact height_cm or finds closest height_cm available.
    
    Returns:
        float ideal_weight_kg or None if insufficient/invalid data.
    """
    if height_cm is None or age_years is None or not ideal_weights_rows:
        return None
        
    try:
        ht = float(height_cm)
        ag = int(age_years)
    except (ValueError, TypeError):
        return None
        
    if not (VALID_BOUNDS['min_height_cm'] <= ht <= VALID_BOUNDS['max_height_cm']):
        return None
    if not (VALID_BOUNDS['min_age_years'] <= ag <= VALID_BOUNDS['max_age_years']):
        return None
        
    # 1. Filter rows matching age range
    age_matched_rows = []
    all_ranges = []
    
    for row in ideal_weights_rows:
        ar_str = row.get('age_range')
        min_a, max_a = parse_age_range(ar_str)
        if min_a is not None and max_a is not None:
            all_ranges.append((min_a, max_a, row))
            if min_a <= ag <= max_a:
                age_matched_rows.append(row)
                
    # Fallback to closest age range if age is e.g. 17 or 72
    if not age_matched_rows and all_ranges:
        # Sort by distance to age
        def range_dist(item):
            min_a, max_a, _ = item
            if ag < min_a:
                return min_a - ag
            elif ag > max_a:
                return ag - max_a
            return 0
            
        all_ranges.sort(key=range_dist)
        closest_min, closest_max, _ = all_ranges[0]
        for min_a, max_a, r in all_ranges:
            if min_a == closest_min and max_a == closest_max:
                age_matched_rows.append(r)
                
    if not age_matched_rows:
        return None
        
    # 2. Find exact or closest height match
    exact_matches = [r for r in age_matched_rows if float(r.get('height_cm', 0)) == ht]
    if exact_matches:
        val = exact_matches[0].get('ideal_weight_kg')
        return round(float(val), 2) if val is not None else None
        
    # Find nearest height
    sorted_by_height = sorted(
        age_matched_rows,
        key=lambda r: abs(float(r.get('height_cm', 0)) - ht)
    )
    
    best_match = sorted_by_height[0]
    val = best_match.get('ideal_weight_kg')
    return round(float(val), 2) if val is not None else None


def calculate_ideal_weight_and_deviation(height_cm, actual_weight_kg, age_years, ideal_weights_rows):
    """
    Computes ideal weight, weight difference, deviation percentage, and military weight status.
    
    Returns:
        dict: {
            'ideal_weight_kg': float or None,
            'weight_difference_kg': float or None,
            'weight_deviation_percent': float or None,
            'weight_status': str,
            'weight_status_badge': str,
            'is_within_shape_limits': bool
        }
    """
    ideal_wt = get_ideal_weight_from_table(height_cm, age_years, ideal_weights_rows)
    
    if ideal_wt is None or actual_weight_kg is None:
        return {
            'ideal_weight_kg': None,
            'weight_difference_kg': None,
            'weight_deviation_percent': None,
            'weight_status': 'Undetermined',
            'weight_status_badge': 'secondary',
            'is_within_shape_limits': False
        }
        
    act_wt = float(actual_weight_kg)
    diff_kg = round(act_wt - ideal_wt, 2)
    dev_pct = round((diff_kg / ideal_wt) * 100.0, 2)
    
    # Military Weight Status Classifications (+/- 10% authorization limit)
    # Standard military SHAPE-1 authorization allows up to +10% over ideal weight
    is_within_shape = abs(dev_pct) <= 10.0
    
    if abs(dev_pct) <= 5.0:
        status = "Ideal Weight"
        badge = "success"
    elif 5.0 < dev_pct <= 10.0:
        status = f"Authorized Limit (+{dev_pct}%)"
        badge = "info"
    elif 10.0 < dev_pct <= 20.0:
        status = f"Overweight (+{dev_pct}%)"
        badge = "warning"
    elif dev_pct > 20.0:
        status = f"Significantly Overweight (+{dev_pct}%)"
        badge = "danger"
    elif -10.0 <= dev_pct < -5.0:
        status = f"Slightly Underweight ({dev_pct}%)"
        badge = "info"
    else:
        status = f"Underweight ({dev_pct}%)"
        badge = "warning"
        
    return {
        'ideal_weight_kg': ideal_wt,
        'weight_difference_kg': diff_kg,
        'weight_deviation_percent': dev_pct,
        'weight_status': status,
        'weight_status_badge': badge,
        'is_within_shape_limits': is_within_shape
    }
