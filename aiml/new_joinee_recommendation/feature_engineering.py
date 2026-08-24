from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, date
import pandas as pd
import numpy as np

from .config import CANONICAL_COMPANIES
from .data_loader import normalize_company
from .utils import parse_date_safe, pd_is_na, get_logger

logger = get_logger("feature_engineering")

def build_features_for_personnel(
    personnel_row: Dict[str, Any],
    units_df: Optional[pd.DataFrame] = None,
    ref_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Extracts and computes the exact 19 feature columns expected by the preprocessor
    from a personnel profile dictionary and its associated units_served history.
    """
    if ref_date is None:
        ref_date = date.today()

    # 1. Soldier Categorical Features
    trade = str(personnel_row.get("trade") or "").strip().upper()
    trade = trade if trade and trade not in ["", "NONE", "NAN", "NULL"] else "UNKNOWN"

    rank = str(personnel_row.get("rank") or "").strip().upper()
    rank = rank if rank and rank not in ["", "NONE", "NAN", "NULL"] else "UNKNOWN"

    prior_station = str(personnel_row.get("prior_station") or "").strip().upper()
    prior_station = prior_station if prior_station and prior_station not in ["", "NONE", "NAN", "NULL"] else "NO"

    # 2. Soldier Temporal & Numerical Features
    enrollment_date = parse_date_safe(personnel_row.get("date_of_enrollment"))
    if enrollment_date:
        service_years = max(0.0, (ref_date - enrollment_date).days / 365.25)
    else:
        service_years = 0.0

    dob = parse_date_safe(personnel_row.get("date_of_birth"))
    if dob:
        age_years = max(0.0, (ref_date - dob).days / 365.25)
    else:
        age_years = 0.0

    detailed_course = str(personnel_row.get("detailed_course") or "").strip()
    has_course = 1 if (detailed_course and detailed_course.lower() not in ["", "none", "no", "nan", "null"]) else 0

    # 3. Units Served Sequence & Aggregate Features
    has_unit_history = 0
    previous_unit_count = 0
    unique_previous_unit_count = 0
    duty_count = 0
    total_service_duration_days = 0.0
    avg_posting_duration_days = 0.0
    days_since_last_posting = 0.0

    prev_u1 = "NO_UNIT"
    prev_u2 = "NO_UNIT"
    prev_u3 = "NO_UNIT"
    most_freq_unit = "NO_UNIT"
    most_recent_duty = "NO_DUTY"
    most_freq_duty = "NO_DUTY"

    if units_df is not None and len(units_df) > 0:
        valid_units = units_df.copy()
        if "from_date" in valid_units.columns:
            valid_units["from_date_parsed"] = valid_units["from_date"].apply(parse_date_safe)
            valid_units = valid_units.sort_values(by="from_date_parsed", ascending=True)

        unit_list = [str(u).strip().upper() for u in valid_units["unit"].dropna() if str(u).strip()]
        duties_list = [str(d).strip().upper() for d in valid_units.get("duty_performed", pd.Series()).dropna() if str(d).strip()]

        if unit_list:
            has_unit_history = 1
            previous_unit_count = len(unit_list)
            unique_previous_unit_count = len(set(unit_list))

            if len(unit_list) >= 1:
                prev_u1 = unit_list[0]
            if len(unit_list) >= 2:
                prev_u2 = unit_list[1]
            if len(unit_list) >= 3:
                prev_u3 = unit_list[2]

            # Most frequent unit
            from collections import Counter
            u_counts = Counter(unit_list)
            most_freq_unit = u_counts.most_common(1)[0][0]

        if duties_list:
            duty_count = len(duties_list)
            most_recent_duty = duties_list[-1]
            d_counts = Counter(duties_list)
            most_freq_duty = d_counts.most_common(1)[0][0]

        # Calculate durations
        durations = []
        last_to_date = None
        for _, row in valid_units.iterrows():
            f_d = parse_date_safe(row.get("from_date"))
            t_d = parse_date_safe(row.get("to_date"))
            if f_d and t_d and t_d >= f_d:
                durations.append((t_d - f_d).days)
                if last_to_date is None or t_d > last_to_date:
                    last_to_date = t_d

        if durations:
            total_service_duration_days = float(sum(durations))
            avg_posting_duration_days = float(np.mean(durations))

        if last_to_date:
            days_since_last_posting = max(0.0, float((ref_date - last_to_date).days))

    features = {
        "trade": trade,
        "rank": rank,
        "prior_station": prior_station,
        "previous_unit_1": prev_u1,
        "previous_unit_2": prev_u2,
        "previous_unit_3": prev_u3,
        "most_frequent_unit": most_freq_unit,
        "most_recent_duty": most_recent_duty,
        "most_frequent_duty": most_freq_duty,
        "service_years": round(float(service_years), 2),
        "age_years": round(float(age_years), 2),
        "has_course": int(has_course),
        "has_unit_history": int(has_unit_history),
        "previous_unit_count": int(previous_unit_count),
        "unique_previous_unit_count": int(unique_previous_unit_count),
        "duty_count": int(duty_count),
        "total_service_duration_days": round(float(total_service_duration_days), 1),
        "avg_posting_duration_days": round(float(avg_posting_duration_days), 1),
        "days_since_last_posting": round(float(days_since_last_posting), 1)
    }

    return features

def build_dataset(
    personnel_df: pd.DataFrame,
    units_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Constructs full training dataset X (features) and y (target company).
    Filters only records belonging to canonical companies.
    """
    df = personnel_df.copy()
    df["target_company"] = df["company"].apply(normalize_company)
    
    # Filter to eligible records
    eligible = df[df["target_company"].isin(CANONICAL_COMPANIES)].copy()
    
    # Group units by personnel_id / army_number
    units_by_id = {}
    units_by_armyno = {}
    
    if len(units_df) > 0:
        for pid, group in units_df.groupby("personnel_id"):
            if pd.notna(pid):
                units_by_id[int(pid)] = group
        if "army_number" in units_df:
            for ano, group in units_df.groupby("army_number"):
                if pd.notna(ano):
                    units_by_armyno[str(ano).strip()] = group

    rows = []
    targets = []

    for _, p_row in eligible.iterrows():
        p_dict = p_row.to_dict()
        pid = p_dict.get("id")
        ano = str(p_dict.get("army_number") or "").strip()

        u_df = None
        if pid in units_by_id:
            u_df = units_by_id[pid]
        elif ano in units_by_armyno:
            u_df = units_by_armyno[ano]

        feat = build_features_for_personnel(p_dict, u_df)
        rows.append(feat)
        targets.append(p_dict["target_company"])

    X = pd.DataFrame(rows)
    y = pd.Series(targets, name="target_company")

    return X, y
