"""
Data Preprocessing, Feature Engineering, and Extraction Pipeline
for AI New Joinee Recommendation (Unit 15 CESR)
"""

import os
import sys
import re
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any, Tuple, Optional

# Ensure workspace root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from db_config import get_db_connection
from aiml.ai_new_joinee_recommendation.position_mapping import (
    VALID_COMPANIES,
    VALID_DB_COMPANIES,
    VALID_SPECIALTIES,
    SPECIALTY_KEYWORDS,
    SPECIALTY_COMPANY_AFFINITY,
    normalize_company_name,
    to_db_company_name,
    to_display_company_name,
    extract_specialties_from_trade_and_text
)

# Rank hierarchy map (Higher number = higher seniority/responsibility)
RANK_ORDER = {
    "Agniveer": 1,
    "Signal Man": 2,
    "CFN": 2,
    "L NK": 3,
    "LOC NK": 3,
    "NK": 4,
    "L HAV": 5,
    "LOC HAV": 5,
    "HAV": 6,
    "CQMH": 7,
    "CHM": 7,
    "RHM": 7,
    "Naib Subedar": 8,
    "Subedar": 9,
    "Subedar Major": 10,
    "Officer": 11,
    "Other": 3
}

# Major military trade families
TRADE_FAMILIES = {
    "trade_fam_ttc": ["ttc", "ttc -ll", "telecom", "telephone"],
    "trade_fam_efs": ["efs", "equipment", "fault"],
    "trade_fam_lmn": ["lmn", "line man", "line", "wire"],
    "trade_fam_dvr": ["dvr", "dvr mt", "dmv", "driver", "transport", "opr dvr"],
    "trade_fam_occ": ["occ", "op ciph", "cipher", "operator"],
    "trade_fam_clk": ["clk", "clk sd", "clk (sd)", "clerk", "pa", "typist"],
    "trade_fam_tech": ["tech", "tech sa", "je sys", "jene", "je ne", "er", "dtmn", "artsan", "artish", "welder"],
    "trade_fam_logistics": ["skt", "skt (eme)", "atbv", "aebv", "at(bv)", "wm", "w/m", "stwd", "qm", "store"],
    "trade_fam_services": ["chef", "chef com", "chef mess", "hk", "hkeeper", "h/k", "h /k", "mess keeper"],
    "trade_fam_radio": ["rr", "radio", "wireless", "dsr", "mw", "vhf", "mccs"]
}

DUTY_DOMAIN_KEYWORDS = {
    "domain_tech": ["tech", "efs", "ttc", "repair", "hardware", "switch", "system", "je", "maintenance", "workshop"],
    "domain_comn": ["radio", "rr", "wireless", "exchange", "mccs", "sig", "sigcen", "line", "mw", "vhf", "communication"],
    "domain_it": ["it", "computer", "server", "lan", "wan", "software", "network", "cyber", "system"],
    "domain_clerk": ["clerk", "sd", "clk", "admin", "office", "drafting", "dispatch", "record", "branch"],
    "domain_qm": ["qm", "skt", "store", "ration", "clothing", "mes", "equipment", "provision"],
    "domain_dvr": ["dvr", "driver", "transport", "mt", "vehicle", "convoy"],
    "domain_gd": ["gd", "guard", "security", "chq", "patrol", "sentry", "escort", "orderly"]
}


def get_rank_level(rank_str: Optional[str]) -> int:
    """Map rank to numeric seniority level."""
    if not rank_str:
        return 2
    r_clean = str(rank_str).strip()
    for k, v in RANK_ORDER.items():
        if k.lower() == r_clean.lower():
            return v
    # Partial matching
    for k, v in RANK_ORDER.items():
        if k.lower() in r_clean.lower() or r_clean.lower() in k.lower():
            return v
    return 3


def calculate_service_years(date_of_enrollment: Any) -> float:
    """Calculate service duration in years from enrollment date."""
    if not date_of_enrollment:
        return 2.0
    try:
        if isinstance(date_of_enrollment, str):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    dt = datetime.strptime(date_of_enrollment, fmt).date()
                    break
                except ValueError:
                    dt = None
        elif isinstance(date_of_enrollment, datetime):
            dt = date_of_enrollment.date()
        elif isinstance(date_of_enrollment, date):
            dt = date_of_enrollment
        else:
            return 2.0

        if dt:
            today = date.today()
            years = (today - dt).days / 365.25
            return max(0.1, round(years, 2))
    except Exception:
        pass
    return 2.0


def calculate_tenure_days(from_date: Any, to_date: Any) -> float:
    """Calculate days served between from_date and to_date."""
    if not from_date or not to_date:
        return 365.0
    try:
        d1 = None
        d2 = None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            if isinstance(from_date, str) and not d1:
                try:
                    d1 = datetime.strptime(from_date, fmt).date()
                except ValueError:
                    pass
            if isinstance(to_date, str) and not d2:
                try:
                    d2 = datetime.strptime(to_date, fmt).date()
                except ValueError:
                    pass
        if isinstance(from_date, (datetime, date)) and not d1:
            d1 = from_date.date() if isinstance(from_date, datetime) else from_date
        if isinstance(to_date, (datetime, date)) and not d2:
            d2 = to_date.date() if isinstance(to_date, datetime) else to_date

        if d1 and d2 and d2 >= d1:
            return float((d2 - d1).days)
    except Exception:
        pass
    return 365.0


def extract_features_from_dict(
    trade: str,
    rank: str,
    specialties: List[str] = None,
    date_of_enrollment: Any = None,
    units_history: List[Dict[str, Any]] = None,
    is_fresh: bool = False
) -> Dict[str, float]:
    """
    Extract standardized numerical feature dictionary for model inference/training.
    """
    trade_clean = (trade or "").strip().upper()
    active_specialties = specialties or extract_specialties_from_trade_and_text(trade)
    spec_set = set(active_specialties)

    # 1. Rank Seniority Level
    rank_level = get_rank_level(rank)

    # 2. Service Years
    service_years = calculate_service_years(date_of_enrollment)

    # 3. Specialty Multi-Hot Encoding
    features: Dict[str, float] = {}
    for spec in VALID_SPECIALTIES:
        col_name = f"spec_{spec.replace(' ', '_').replace('/', '_')}"
        features[col_name] = 1.0 if spec in spec_set else 0.0

    # 3b. Trade Family Multi-Hot Indicators
    for fam_name, kws in TRADE_FAMILIES.items():
        matched_fam = 0.0
        for kw in kws:
            if kw in trade_clean.lower() or kw in active_specialties:
                matched_fam = 1.0
                break
        features[fam_name] = matched_fam

    # 4. Units Served History Features
    units = units_history or []
    if is_fresh or not units:
        num_units = 0.0
        total_tenure_days = 0.0
        avg_tenure_days = 0.0
        has_prev_units = 0.0
        duty_text = ""
        unit_names_text = ""
    else:
        num_units = float(len(units))
        tenures = [calculate_tenure_days(u.get("from_date"), u.get("to_date")) for u in units]
        total_tenure_days = float(sum(tenures))
        avg_tenure_days = float(total_tenure_days / max(1.0, num_units))
        has_prev_units = 1.0
        duty_text = " ".join([str(u.get("duty_performed") or u.get("duty") or "") for u in units]).lower()
        unit_names_text = " ".join([str(u.get("unit") or u.get("unit_name") or "") for u in units]).lower()

    features["rank_level"] = float(rank_level)
    features["service_years"] = float(service_years)
    features["num_units"] = float(num_units)
    features["total_tenure_days"] = float(total_tenure_days)
    features["avg_tenure_days"] = float(avg_tenure_days)
    features["has_prev_units"] = float(has_prev_units)

    # 5. Duty Domain Multi-Hot Encoding from historical duties
    for domain, kws in DUTY_DOMAIN_KEYWORDS.items():
        score = 0.0
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', duty_text):
                score += 1.0
            if re.search(r'\b' + re.escape(kw) + r'\b', trade_clean.lower()):
                score += 0.5
        features[domain] = float(min(score, 3.0))

    # 6. Unit Exposure Types (Signal Regiment, RR, Corps HQ, Static)
    features["exp_rr"] = 1.0 if ("rr" in unit_names_text or "rashtriya" in unit_names_text) else 0.0
    features["exp_corps"] = 1.0 if ("corps" in unit_names_text or "cgsr" in unit_names_text or "mdsr" in unit_names_text) else 0.0
    features["exp_sig_reg"] = 1.0 if ("sig" in unit_names_text or "csr" in unit_names_text) else 0.0

    # 7. Specialty-to-Company Prior Affinity Features
    comn_affinity = 0.0
    hq_affinity = 0.0
    coy3_affinity = 0.0

    for spec in active_specialties:
        aff = SPECIALTY_COMPANY_AFFINITY.get(spec, {"HQ Coy": 0.33, "Comn Coy": 0.33, "3 Coy": 0.33})
        comn_affinity += aff.get("Comn Coy", 0.33)
        hq_affinity += aff.get("HQ Coy", 0.33)
        coy3_affinity += aff.get("3 Coy", 0.33)

    tot_aff = max(0.01, comn_affinity + hq_affinity + coy3_affinity)
    features["prior_aff_comn"] = round(comn_affinity / tot_aff, 3)
    features["prior_aff_hq"] = round(hq_affinity / tot_aff, 3)
    features["prior_aff_3coy"] = round(coy3_affinity / tot_aff, 3)

    return features


def load_historical_dataset() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Fetch historical personnel and units_served data from UMS database,
    clean and engineer features for training.
    """
    conn = get_db_connection()
    if conn is None:
        raise ConnectionError("Failed to connect to UMS database.")

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch eligible personnel records
        query_personnel = """
            SELECT id, army_number, name, `rank`, trade, company, date_of_enrollment,
                   prior_station, section
            FROM personnel
            WHERE company IN ('HQ company', 'COMN Company', '3 Company', 'HQ Coy', 'Comn Coy', '3 Coy')
              AND `rank` IS NOT NULL
        """
        cursor.execute(query_personnel)
        personnel_rows = cursor.fetchall()

        # 2. Fetch units_served records
        query_units = """
            SELECT personnel_id, army_number, unit, from_date, to_date, duty_performed
            FROM units_served
            ORDER BY personnel_id, sr_no ASC
        """
        cursor.execute(query_units)
        units_rows = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception as e:
        if conn:
            conn.close()
        raise RuntimeError(f"Database query error: {str(e)}")

    if not personnel_rows:
        raise ValueError("No personnel records found in the database for training.")

    # Group units by personnel_id
    units_by_pid: Dict[int, List[Dict[str, Any]]] = {}
    for u in units_rows:
        pid = u.get("personnel_id")
        if pid not in units_by_pid:
            units_by_pid[pid] = []
        units_by_pid[pid].append(u)

    # Build feature dataset
    feature_rows = []
    target_labels = []

    for p in personnel_rows:
        pid = p.get("id")
        trade = p.get("trade") or ""
        rank = p.get("rank") or "Signal Man"
        enroll_date = p.get("date_of_enrollment")
        target_coy = normalize_company_name(p.get("company"))

        units = units_by_pid.get(pid, [])
        specialties = extract_specialties_from_trade_and_text(trade)

        feats = extract_features_from_dict(
            trade=trade,
            rank=rank,
            specialties=specialties,
            date_of_enrollment=enroll_date,
            units_history=units,
            is_fresh=(len(units) == 0)
        )

        feats["personnel_id"] = pid
        feats["army_number"] = p.get("army_number") or ""
        feature_rows.append(feats)
        target_labels.append(target_coy)

    df_features = pd.DataFrame(feature_rows)
    s_targets = pd.Series(target_labels, name="target_company")

    return df_features, s_targets
