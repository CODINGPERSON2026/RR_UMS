"""
Feature Engineering Pipeline for UMS AI Company Readiness.
Extracts strictly time-aligned operational features from database records.
Enforces Data Leakage Prevention: No future status or future leave dates are included.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd

from .models.readiness_models import CompanyReadiness
from .utils import safe_div

# Explicit feature column names in order
FEATURE_COLUMNS = [
    "company_hq",
    "company_comn",
    "company_3coy",
    "authorized_strength",
    "actual_strength",
    "strength_ratio",
    "leave_rate",
    "detachment_rate",
    "td_rate",
    "course_away_rate",
    "availability_rate",
    "trade_fulfillment_ratio",
    "qualification_fulfillment_ratio",
    "course_fulfillment_ratio",
    "shape1_ratio",
    "lmc_ratio",
    "bpet_pass_ratio",
    "ppt_pass_ratio",
    "upcoming_recat_ratio"
]


def extract_features_from_readiness(
    readiness: CompanyReadiness,
    personnel: List[Dict[str, Any]],
    weight_info: Dict[str, Dict[str, Any]],
    as_of_date: Optional[date] = None
) -> Dict[str, float]:
    """
    Extracts time-aligned operational features from current state.
    
    Guarantees:
    - Zero data leakage: Evaluated strictly at `as_of_date` or current moment.
    - No future qualification status or future leave records are accessed.
    """
    ref_date = as_of_date or date.today()
    coy = readiness.company
    total_strength = len(personnel)
    req_strength = readiness.required_strength or total_strength or 1

    # 1. Company one-hot encoding
    c_hq = 1.0 if coy == "HQ COY" else 0.0
    c_comn = 1.0 if coy == "COMN COY" else 0.0
    c_3coy = 1.0 if coy == "3 COY" else 0.0

    # 2. Strength metrics
    str_ratio = safe_div(total_strength, req_strength, 1.0)

    # 3. Availability metrics
    av_dim = readiness.dimensions.get("availability")
    av_details = av_dim.details if av_dim else {}
    
    onleave_cnt = av_details.get("onleave", 0)
    det_cnt = av_details.get("detachment", 0)
    td_cnt = av_details.get("td", 0)
    oncourse_cnt = av_details.get("oncourse", 0)
    avail_cnt = av_details.get("available", total_strength)

    leave_rate = safe_div(onleave_cnt, total_strength)
    det_rate = safe_div(det_cnt, total_strength)
    td_rate = safe_div(td_cnt, total_strength)
    course_rate = safe_div(oncourse_cnt, total_strength)
    avail_rate = safe_div(avail_cnt, total_strength)

    # 4. Dimension ratios
    trade_ratio = safe_div(readiness.dimensions.get("trade").score if readiness.dimensions.get("trade") else 100.0, 100.0)
    qual_ratio = safe_div(readiness.dimensions.get("qualification").score if readiness.dimensions.get("qualification") else 100.0, 100.0)
    course_ratio = safe_div(readiness.dimensions.get("course").score if readiness.dimensions.get("course") else 100.0, 100.0)

    # 5. Medical & Fitness metrics
    med_dim = readiness.dimensions.get("medical")
    med_details = med_dim.details if med_dim else {}
    shape1_cnt = med_details.get("shape1", total_strength)
    lmc_cnt = med_details.get("lmc", 0)
    shape1_rate = safe_div(shape1_cnt, total_strength)
    lmc_rate = safe_div(lmc_cnt, total_strength)

    fit_dim = readiness.dimensions.get("fitness")
    fit_details = fit_dim.details if fit_dim else {}
    fit_cnt = fit_details.get("fit_count", total_strength)
    bpet_pass_rate = safe_div(fit_cnt, total_strength)
    ppt_pass_rate = bpet_pass_rate  # Tied to physical standard

    # 6. Upcoming medical recategorization due in next 60 days
    cutoff_recat = ref_date + timedelta(days=60)
    upcoming_recat_cnt = 0
    for p in personnel:
        recat_due = p.get("next_recat_due")
        if recat_due:
            if isinstance(recat_due, datetime):
                recat_due = recat_due.date()
            if ref_date <= recat_due <= cutoff_recat:
                upcoming_recat_cnt += 1
    upcoming_recat_rate = safe_div(upcoming_recat_cnt, total_strength)

    return {
        "company_hq": c_hq,
        "company_comn": c_comn,
        "company_3coy": c_3coy,
        "authorized_strength": float(req_strength),
        "actual_strength": float(total_strength),
        "strength_ratio": round(str_ratio, 4),
        "leave_rate": round(leave_rate, 4),
        "detachment_rate": round(det_rate, 4),
        "td_rate": round(td_rate, 4),
        "course_away_rate": round(course_rate, 4),
        "availability_rate": round(avail_rate, 4),
        "trade_fulfillment_ratio": round(trade_ratio, 4),
        "qualification_fulfillment_ratio": round(qual_ratio, 4),
        "course_fulfillment_ratio": round(course_ratio, 4),
        "shape1_ratio": round(shape1_rate, 4),
        "lmc_ratio": round(lmc_rate, 4),
        "bpet_pass_ratio": round(bpet_pass_rate, 4),
        "ppt_pass_ratio": round(ppt_pass_rate, 4),
        "upcoming_recat_ratio": round(upcoming_recat_rate, 4)
    }


def to_feature_vector(feature_dict: Dict[str, float]) -> np.ndarray:
    """Converts feature dictionary to ordered numpy 1D vector."""
    return np.array([feature_dict.get(col, 0.0) for col in FEATURE_COLUMNS], dtype=np.float32)


def to_feature_dataframe(feature_dicts: List[Dict[str, float]]) -> pd.DataFrame:
    """Converts a list of feature dictionaries to a structured DataFrame."""
    df = pd.DataFrame(feature_dicts)
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
    return df[FEATURE_COLUMNS]


def extract_features_from_snapshot(snapshot: Dict[str, Any]) -> Dict[str, float]:
    """
    Extracts ordered 19 operational features from an ai_company_readiness_history snapshot row.
    Guarantees consistent column mapping across historical training and live inference.
    """
    coy = str(snapshot.get("company", ""))
    c_hq = 1.0 if "hq" in coy.lower() or "1" in coy.lower() else 0.0
    c_comn = 1.0 if "comm" in coy.lower() or "comn" in coy.lower() else 0.0
    c_3coy = 1.0 if "3" in coy.lower() else 0.0

    act = float(snapshot.get("actual_strength") or 1)
    req = float(snapshot.get("required_strength") or act or 1)
    str_ratio = safe_div(act, req, 1.0)

    onleave = float(snapshot.get("onleave_count") or 0)
    det = float(snapshot.get("detachment_count") or 0)
    td = float(snapshot.get("td_count") or 0)
    oncourse = float(snapshot.get("oncourse_count") or 0)
    avail = float(snapshot.get("available_strength") or (act - onleave - det - td - oncourse))
    unfit = float(snapshot.get("unfit_count") or 0)

    leave_rate = safe_div(onleave, act)
    det_rate = safe_div(det, act)
    td_rate = safe_div(td, act)
    course_rate = safe_div(oncourse, act)
    avail_rate = safe_div(avail, act)

    trade_score = float(snapshot.get("trade_score") if snapshot.get("trade_score") is not None else 100.0)
    qual_score = float(snapshot.get("qualification_score") if snapshot.get("qualification_score") is not None else 100.0)
    course_score = float(snapshot.get("course_score") if snapshot.get("course_score") is not None else 100.0)
    fit_score = float(snapshot.get("fitness_score") if snapshot.get("fitness_score") is not None else 100.0)

    shape1_rate = safe_div(max(0.0, act - unfit), act)
    lmc_rate = safe_div(unfit, act)
    bpet_rate = safe_div(fit_score, 100.0)
    recat_rate = safe_div(min(unfit * 0.4, act), act)

    return {
        "company_hq": c_hq,
        "company_comn": c_comn,
        "company_3coy": c_3coy,
        "authorized_strength": float(req),
        "actual_strength": float(act),
        "strength_ratio": round(str_ratio, 4),
        "leave_rate": round(leave_rate, 4),
        "detachment_rate": round(det_rate, 4),
        "td_rate": round(td_rate, 4),
        "course_away_rate": round(course_rate, 4),
        "availability_rate": round(avail_rate, 4),
        "trade_fulfillment_ratio": round(safe_div(trade_score, 100.0), 4),
        "qualification_fulfillment_ratio": round(safe_div(qual_score, 100.0), 4),
        "course_fulfillment_ratio": round(safe_div(course_score, 100.0), 4),
        "shape1_ratio": round(shape1_rate, 4),
        "lmc_ratio": round(lmc_rate, 4),
        "bpet_pass_ratio": round(bpet_rate, 4),
        "ppt_pass_ratio": round(bpet_rate, 4),
        "upcoming_recat_ratio": round(recat_rate, 4)
    }

