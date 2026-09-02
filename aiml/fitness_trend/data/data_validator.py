"""
Data Validator and Sanitizer for AI/ML Fitness Trend.
Implements source priority rules, sanity checks, and edge-case detection for dirty military data.
"""

from datetime import datetime, date
import re
from ..config import VALID_BOUNDS, BPET_SCORE_MAP, PPT_SCORE_MAP


def clean_bpet_ppt_grading(grading_val):
    """
    Standardize raw BPET or PPT grading strings into canonical military categories.
    Handles variations like 'EX', 'EXCELLENT', 'EXELENT', 'GOOD', 'GOO', 'SAT', 'LMC', 'A2P', 'NA', 'TEST'.
    
    Returns:
        tuple: (canonical_grade, standard_score) or (None, None)
    """
    if grading_val is None:
        return None, None
    
    val_str = str(grading_val).strip().upper()
    if not val_str or val_str in ['NONE', 'NULL', 'NAN', 'NA', 'TEST', '-']:
        return None, None
    
    # Check exact maps
    if val_str in ['EX', 'EXCELLENT', 'EXELENT', 'EX ']:
        return 'EXCELLENT', 100
    if val_str in ['GOOD', 'GOO', 'G0OOD', 'GD']:
        return 'GOOD', 80
    if val_str in ['SAT', 'SATISFACTORY', 'SATISFIED']:
        return 'SATISFACTORY', 60
    if val_str in ['LMC', 'LOW MEDICAL CATEGORY']:
        return 'LMC', 40
    if val_str in ['A2P', 'P2', 'P3']:
        return 'A2P', 40
    if val_str in ['FAIL', 'FAILED', 'REMEDIAL']:
        return 'FAIL', 30
    
    # Generic contains checks
    if 'EX' in val_str:
        return 'EXCELLENT', 100
    if 'GOO' in val_str:
        return 'GOOD', 80
    if 'SAT' in val_str:
        return 'SATISFACTORY', 60
    
    return None, None


def calculate_age_from_dob(dob_val):
    """
    Safely calculate age in full years from date of birth.
    Returns:
        int age or None if invalid/future date.
    """
    if not dob_val:
        return None
    
    try:
        if isinstance(dob_val, str):
            # Try parsing various date formats
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
                try:
                    dob_val = datetime.strptime(dob_val.strip(), fmt).date()
                    break
                except ValueError:
                    continue
        
        if isinstance(dob_val, datetime):
            dob_val = dob_val.date()
            
        if isinstance(dob_val, date):
            today = date.today()
            if dob_val > today:
                return None  # Future DOB is invalid
            
            age = today.year - dob_val.year - ((today.month, today.day) < (dob_val.month, dob_val.day))
            if VALID_BOUNDS['min_age_years'] <= age <= VALID_BOUNDS['max_age_years']:
                return int(age)
            return None
    except Exception:
        return None
    return None


def calculate_service_years(enrollment_date):
    """
    Calculate total years of service from enrollment date.
    """
    if not enrollment_date:
        return 0.0
    
    try:
        if isinstance(enrollment_date, str):
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
                try:
                    enrollment_date = datetime.strptime(enrollment_date.strip(), fmt).date()
                    break
                except ValueError:
                    continue
                    
        if isinstance(enrollment_date, datetime):
            enrollment_date = enrollment_date.date()
            
        if isinstance(enrollment_date, date):
            today = date.today()
            if enrollment_date > today:
                return 0.0
            days = (today - enrollment_date).days
            return round(max(0.0, days / 365.25), 1)
    except Exception:
        return 0.0
    return 0.0


def validate_and_clean_soldier_data(personnel_row, weight_row):
    """
    Applies strict source-priority rules and edge-case cleaning to produce a consolidated soldier data dict.
    
    Source Priority Rule:
    1. Height: weight_info.height if within [130cm, 225cm], else personnel.height if valid, else None.
    2. Weight: weight_info.actual_weight if within [35kg, 160kg], else personnel.weight if valid, else None.
    3. Age: Computed from personnel.date_of_birth if valid [17, 65], else weight_info.age if valid, else None.
    
    Returns:
        dict containing cleaned soldier fields and data_quality_flags list.
    """
    flags = []
    
    p = personnel_row or {}
    w = weight_row or {}
    
    army_number = (p.get('army_number') or w.get('army_number') or '').strip()
    name = (p.get('name') or w.get('name') or 'Unknown Personnel').strip()
    rank = (p.get('rank') or w.get('rank') or 'Soldier').strip()
    company = (p.get('company') or w.get('company') or 'Unit HQ').strip()
    trade = (p.get('trade') or 'GD').strip()
    section = (p.get('section') or '').strip()
    
    # 1. Height Resolution
    raw_w_h = w.get('height')
    raw_p_h = p.get('height')
    
    try:
        val_w_h = float(raw_w_h) if raw_w_h is not None else None
    except (ValueError, TypeError):
        val_w_h = None
        
    try:
        val_p_h = float(raw_p_h) if raw_p_h is not None else None
    except (ValueError, TypeError):
        val_p_h = None
        
    height_cm = None
    if val_w_h is not None and VALID_BOUNDS['min_height_cm'] <= val_w_h <= VALID_BOUNDS['max_height_cm']:
        height_cm = round(val_w_h, 1)
    elif val_p_h is not None and VALID_BOUNDS['min_height_cm'] <= val_p_h <= VALID_BOUNDS['max_height_cm']:
        height_cm = round(val_p_h, 1)
        flags.append("Height sourced from personnel table (weight_info height invalid or missing)")
    else:
        flags.append("Missing or unrealistic height")
        
    # 2. Weight Resolution
    raw_w_wt = w.get('actual_weight')
    raw_p_wt = p.get('weight')
    
    try:
        val_w_wt = float(raw_w_wt) if raw_w_wt is not None else None
    except (ValueError, TypeError):
        val_w_wt = None
        
    try:
        val_p_wt = float(raw_p_wt) if raw_p_wt is not None else None
    except (ValueError, TypeError):
        val_p_wt = None
        
    actual_weight_kg = None
    if val_w_wt is not None and VALID_BOUNDS['min_weight_kg'] <= val_w_wt <= VALID_BOUNDS['max_weight_kg']:
        actual_weight_kg = round(val_w_wt, 1)
    elif val_p_wt is not None and VALID_BOUNDS['min_weight_kg'] <= val_p_wt <= VALID_BOUNDS['max_weight_kg']:
        actual_weight_kg = round(val_p_wt, 1)
        flags.append("Weight sourced from personnel table (weight_info weight invalid or missing)")
    else:
        flags.append("Missing or unrealistic weight")
        
    # Check weight divergence between sources
    if val_w_wt is not None and val_p_wt is not None and abs(val_w_wt - val_p_wt) > 5.0:
        flags.append(f"Weight discrepancy detected (weight_info: {val_w_wt}kg vs personnel: {val_p_wt}kg)")
        
    # 3. Age Resolution
    dob_age = calculate_age_from_dob(p.get('date_of_birth'))
    raw_w_age = w.get('age')
    try:
        val_w_age = int(raw_w_age) if raw_w_age is not None else None
    except (ValueError, TypeError):
        val_w_age = None
        
    age = None
    if dob_age is not None:
        age = dob_age
    elif val_w_age is not None and VALID_BOUNDS['min_age_years'] <= val_w_age <= VALID_BOUNDS['max_age_years']:
        age = val_w_age
        flags.append("Age sourced from weight_info (DOB missing)")
    else:
        flags.append("Missing or invalid age")
        
    # 4. Service Years
    service_years = calculate_service_years(p.get('date_of_enrollment'))
    
    # 5. BPET / PPT Gradings
    bpet_grade, bpet_score = clean_bpet_ppt_grading(p.get('bpet_grading'))
    ppt_grade, ppt_score = clean_bpet_ppt_grading(p.get('ppt_grading'))
    
    if bpet_grade is None:
        flags.append("Missing BPET grading")
    if ppt_grade is None:
        flags.append("Missing PPT grading")
        
    # 6. Status & Category
    status_type = (w.get('status_type') or 'shape').strip().lower()
    category_type = (w.get('category_type') or '').strip().lower() if w.get('category_type') else None
    
    # 7. Medical restrictions and details
    med_cat_raw = p.get('med_cat')
    is_lmc = False
    if str(med_cat_raw).strip().lower() in ['yes', 'lmc', 'p2', 'p3', 'a2p', '1']:
        is_lmc = True
    elif status_type == 'category' or category_type in ['temporary', 'permanent']:
        is_lmc = True
        
    medical_problem = (p.get('medical_problem') or '').strip()
    p_restrictions = (p.get('restrictions') or '').strip()
    w_restrictions = (w.get('restrictions') or '').strip()
    
    combined_restrictions = []
    if p_restrictions and p_restrictions.upper() not in ['NO', 'NONE', 'NIL']:
        combined_restrictions.append(p_restrictions)
    if w_restrictions and w_restrictions.upper() not in ['NO', 'NONE', 'NIL']:
        if w_restrictions not in combined_restrictions:
            combined_restrictions.append(w_restrictions)
            
    restrictions_text = "; ".join(combined_restrictions) if combined_restrictions else None
    
    has_medical_restrictions = bool(restrictions_text or medical_problem or is_lmc)
    
    return {
        'army_number': army_number,
        'name': name,
        'rank': rank,
        'company': company,
        'trade': trade,
        'section': section,
        'height_cm': height_cm,
        'actual_weight_kg': actual_weight_kg,
        'age': age,
        'service_years': service_years,
        'bpet_grade': bpet_grade,
        'bpet_score': bpet_score,
        'ppt_grade': ppt_grade,
        'ppt_score': ppt_score,
        'bpet_date': p.get('bpet_date'),
        'status_type': status_type,
        'category_type': category_type,
        'is_lmc': is_lmc,
        'med_cat_raw': med_cat_raw,
        'medical_problem': medical_problem if medical_problem else None,
        'restrictions': restrictions_text,
        'has_medical_restrictions': has_medical_restrictions,
        'participation_activities': p.get('participation_activities'),
        'data_quality_flags': flags,
        'is_sufficient_for_prediction': bool(height_cm and actual_weight_kg and age)
    }
