from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, date
import pandas as pd
import numpy as np

from .config import CANONICAL_COMPANIES
from .data_loader import normalize_company
from .utils import parse_date_safe, sanitize_text, get_logger

logger = get_logger("feature_engineering")

def build_features_for_personnel(
    personnel_row: Dict[str, Any],
    units_df: Optional[pd.DataFrame] = None,
    ref_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Extracts and computes the exact 19 feature columns expected by the preprocessor
    from a personnel profile dictionary and its associated units_served history.
    Guards against negative values, future dates, and invalid types.
    """
    if ref_date is None:
        ref_date = date.today()

    # 1. Soldier Categorical Features
    trade = sanitize_text(personnel_row.get("trade"), default="UNKNOWN").upper()
    rank = sanitize_text(personnel_row.get("rank"), default="UNKNOWN").upper()
    prior_station = sanitize_text(personnel_row.get("prior_station"), default="NO").upper()

    # 2. Soldier Temporal & Numerical Features
    enrollment_date = parse_date_safe(personnel_row.get("date_of_enrollment"), allow_future=False, max_future_cutoff=ref_date)
    if enrollment_date and enrollment_date <= ref_date:
        service_years = max(0.0, (ref_date - enrollment_date).days / 365.25)
    else:
        service_years = 0.0

    dob = parse_date_safe(personnel_row.get("date_of_birth"), allow_future=False, max_future_cutoff=ref_date)
    if dob and dob <= ref_date:
        age_years = max(0.0, (ref_date - dob).days / 365.25)
    else:
        age_years = 0.0

    detailed_course = sanitize_text(personnel_row.get("detailed_course"), default="")
    has_course = 1 if (detailed_course and detailed_course.lower() not in ["", "none", "no", "nan", "null", "unknown"]) else 0

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
            valid_units["from_date_parsed"] = valid_units["from_date"].apply(
                lambda v: parse_date_safe(v, allow_future=False, max_future_cutoff=ref_date)
            )
            # Sort safely
            valid_units = valid_units.sort_values(
                by="from_date_parsed",
                ascending=True,
                na_position="first"
            )

        unit_list = [
            sanitize_text(u, default="").upper()
            for u in valid_units.get("unit", pd.Series()).dropna()
            if sanitize_text(u, default="")
        ]
        duties_list = [
            sanitize_text(d, default="").upper()
            for d in valid_units.get("duty_performed", pd.Series()).dropna()
            if sanitize_text(d, default="")
        ]

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

            from collections import Counter
            u_counts = Counter(unit_list)
            most_freq_unit = u_counts.most_common(1)[0][0]

        if duties_list:
            duty_count = len(duties_list)
            most_recent_duty = duties_list[-1]
            from collections import Counter
            d_counts = Counter(duties_list)
            most_freq_duty = d_counts.most_common(1)[0][0]

        # Calculate durations safely
        durations = []
        last_to_date = None
        for _, row in valid_units.iterrows():
            f_d = parse_date_safe(row.get("from_date"), allow_future=False, max_future_cutoff=ref_date)
            t_d = parse_date_safe(row.get("to_date"), allow_future=False, max_future_cutoff=ref_date)
            if f_d and t_d:
                if f_d > t_d:
                    f_d, t_d = t_d, f_d # Swap if reversed
                dur = max(0, (t_d - f_d).days)
                durations.append(dur)
                if last_to_date is None or t_d > last_to_date:
                    last_to_date = t_d

        if durations:
            total_service_duration_days = float(sum(durations))
            avg_posting_duration_days = float(np.mean(durations))

        if last_to_date and last_to_date <= ref_date:
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
    if "target_company" not in df.columns:
        df["target_company"] = df["company"].apply(normalize_company)
    
    # Filter to eligible records
    eligible = df[df["target_company"].isin(CANONICAL_COMPANIES)].copy()
    
    # Group units by personnel_id / army_number
    units_by_id = {}
    units_by_armyno = {}
    
    if len(units_df) > 0:
        for pid, group in units_df.groupby("personnel_id"):
            if pd.notna(pid):
                try:
                    units_by_id[int(pid)] = group
                except Exception:
                    pass
        if "army_number" in units_df:
            for ano, group in units_df.groupby("army_number"):
                if pd.notna(ano):
                    ano_str = str(ano).strip().upper()
                    if ano_str and ano_str not in ["NAN", "NONE", "NULL", ""]:
                        units_by_armyno[ano_str] = group

    rows = []
    targets = []

    for _, p_row in eligible.iterrows():
        p_dict = p_row.to_dict()
        pid = p_dict.get("id")
        try:
            pid_int = int(pid) if pd.notna(pid) else None
        except Exception:
            pid_int = None
        ano = str(p_dict.get("army_number") or "").strip().upper()

        u_df = None
        if pid_int is not None and pid_int in units_by_id:
            u_df = units_by_id[pid_int]
        elif ano and ano in units_by_armyno:
            u_df = units_by_armyno[ano]

        feat = build_features_for_personnel(p_dict, u_df)
        rows.append(feat)
        targets.append(p_dict["target_company"])

    X = pd.DataFrame(rows)
    y = pd.Series(targets, name="target_company")

    logger.info(f"Built training dataset: X shape={X.shape}, y distribution={y.value_counts().to_dict()}")
    return X, y

