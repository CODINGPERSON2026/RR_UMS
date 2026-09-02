"""
BMI Calculation and Categorization Module.
Guarantees division-by-zero prevention, realistic boundary checks, and military BMI categorization.
"""

from ..config import BMI_CATEGORIES, VALID_BOUNDS


def calculate_bmi(weight_kg, height_cm):
    """
    Calculate Body Mass Index: weight_kg / (height_m ^ 2).
    
    Guards:
    - Checks for None, 0, or negative values.
    - Validates height in [130cm, 225cm] and weight in [35kg, 160kg].
    
    Returns:
        float rounded to 2 decimal places, or None if input data is invalid.
    """
    if weight_kg is None or height_cm is None:
        return None
    
    try:
        wt = float(weight_kg)
        ht = float(height_cm)
    except (ValueError, TypeError):
        return None
        
    if wt <= 0 or ht <= 0:
        return None
        
    if not (VALID_BOUNDS['min_height_cm'] <= ht <= VALID_BOUNDS['max_height_cm']):
        return None
        
    if not (VALID_BOUNDS['min_weight_kg'] <= wt <= VALID_BOUNDS['max_weight_kg']):
        return None
        
    height_m = ht / 100.0
    if height_m <= 0:
        return None
        
    bmi = wt / (height_m * height_m)
    
    # Boundary sanity check for BMI (must be between 10.0 and 60.0)
    if bmi < 10.0 or bmi > 60.0:
        return None
        
    return round(bmi, 2)


def get_bmi_category(bmi_value):
    """
    Maps BMI value to category label and badge color.
    
    Returns:
        tuple: (category_name, hex_color, badge_class)
    """
    if bmi_value is None:
        return "Unknown / Invalid Data", "#94a3b8", "secondary"
        
    try:
        bmi = float(bmi_value)
    except (ValueError, TypeError):
        return "Unknown / Invalid Data", "#94a3b8", "secondary"
        
    if bmi < 18.5:
        return "Underweight", "#3b82f6", "info"
    elif bmi <= 24.9:
        return "Normal (Ideal)", "#10b981", "success"
    elif bmi <= 29.9:
        return "Overweight", "#f59e0b", "warning"
    elif bmi <= 34.9:
        return "Obese Class I", "#f97316", "danger"
    else:
        return "Obese Class II (Severe)", "#ef4444", "danger"
