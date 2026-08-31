"""
Data Preprocessing, Feature Engineering, and Extraction Pipeline
for AI New Joinee Recommendation (Unit 15 CESR) - STRICTLY TRADE-FREE
"""

import os
import sys
import re
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
    UNIT_15_CESR_STRUCTURE,
    normalize_company_name,
    to_db_company_name,
    to_display_company_name,
    get_section_for_position,
    is_valid_hierarchy
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
    "Nb Sub": 8,
    "Subedar": 9,
    "Sub": 9,
    "Subedar Major": 10,
    "SM": 10,
    "Officer": 11,
    "Capt": 11,
    "Major": 11,
    "Lt Col": 11,
    "Col": 11,
    "Other": 3
}

# Domain keyword dictionary for historical duties (NO TRADE USED)
DUTY_DOMAIN_KEYWORDS = {
    "domain_tech": ["tech", "efs", "ttc", "repair", "hardware", "switch", "system", "je", "maintenance", "workshop", "dtmn"],
    "domain_comn": ["radio", "rr", "wireless", "exchange", "mccs", "sig", "sigcen", "line", "mw", "vhf", "communication", "node"],
    "domain_it": ["it", "computer", "server", "lan", "wan", "software", "network", "cyber", "system", "coding", "projects"],
    "domain_clerk": ["clerk", "sd", "clk", "admin", "office", "drafting", "dispatch", "record", "branch", "trg clk", "head clk", "co clk", "coy clk"],
    "domain_qm": ["qm", "skt", "store", "ration", "clothing", "mes", "equipment", "provision", "storeman"],
    "domain_dvr": ["dvr", "driver", "transport", "mt", "vehicle", "convoy", "duty dvr", "mtnco"],
    "domain_gd": ["gd", "guard", "security", "chq", "patrol", "sentry", "escort", "orderly", "runner", "buddy", "orh", "mess", "chm", "rhm", "cqmh"]
}


def get_rank_level(rank_str: Optional[str]) -> int:
    """Map rank to numeric seniority level."""
    if not rank_str:
        return 2
    r_clean = str(rank_str).strip()
    for k, v in RANK_ORDER.items():
        if k.lower() == r_clean.lower():
            return v
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
                    dt = datetime.strptime(date_of_enrollment.strip(), fmt).date()
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
                    d1 = datetime.strptime(from_date.strip(), fmt).date()
                except ValueError:
                    pass
            if isinstance(to_date, str) and not d2:
                try:
                    d2 = datetime.strptime(to_date.strip(), fmt).date()
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
    rank: str,
    date_of_enrollment: Any = None,
    prior_station: str = "",
    units_history: List[Dict[str, Any]] = None,
    is_fresh: bool = False,
    extra_personnel_attrs: Dict[str, Any] = None
) -> Dict[str, float]:
    """
    Extract standardized numerical feature dictionary for model inference/training.
    CRITICAL: Strictly excludes 'trade' and any trade-based rules/features.
    """
    features: Dict[str, float] = {}

    # 1. Rank Seniority Level
    features["rank_level"] = float(get_rank_level(rank))

    # 2. Service Duration
    features["service_years"] = float(calculate_service_years(date_of_enrollment))

    # 3. Units Served History Features
    units = units_history or []
    if is_fresh or not units:
        features["num_units"] = 0.0
        features["total_tenure_days"] = 0.0
        features["avg_tenure_days"] = 0.0
        features["has_prev_units"] = 0.0
        duty_text = ""
        unit_names_text = ""
    else:
        num_units = float(len(units))
        tenures = [calculate_tenure_days(u.get("from_date"), u.get("to_date")) for u in units]
        total_tenure_days = float(sum(tenures))
        avg_tenure_days = float(total_tenure_days / max(1.0, num_units))

        features["num_units"] = num_units
        features["total_tenure_days"] = total_tenure_days
        features["avg_tenure_days"] = avg_tenure_days
        features["has_prev_units"] = 1.0

        duty_text = " ".join([str(u.get("duty_performed") or u.get("duty") or "") for u in units]).lower()
        unit_names_text = " ".join([str(u.get("unit") or u.get("unit_name") or "") for u in units]).lower()

    # 4. Duty Domain Signals from Past Units Served
    for domain, kws in DUTY_DOMAIN_KEYWORDS.items():
        score = 0.0
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', duty_text):
                score += 1.0
        features[domain] = float(min(score, 3.0))

    # 5. Unit Operational Exposure Types (Field RR, Corps HQ, Signal Regiment)
    features["exp_rr"] = 1.0 if ("rr" in unit_names_text or "rashtriya" in unit_names_text) else 0.0
    features["exp_corps"] = 1.0 if ("corps" in unit_names_text or "cgsr" in unit_names_text or "mdsr" in unit_names_text) else 0.0
    features["exp_sig_reg"] = 1.0 if ("sig" in unit_names_text or "csr" in unit_names_text or "regm" in unit_names_text) else 0.0

    # 6. Prior Station & Additional Personnel Metadata (Non-trade)
    features["has_prior_station"] = 1.0 if (prior_station and str(prior_station).strip().upper() not in ["", "NO", "NONE", "N/A"]) else 0.0
    if extra_personnel_attrs:
        worked_it_val = 1.0 if str(extra_personnel_attrs.get("worked_it", "")).strip().upper() in ["YES", "1", "TRUE"] else 0.0
        features["worked_it"] = worked_it_val
    else:
        features["worked_it"] = 0.0

    return features


FEATURE_NAMES = list(extract_features_from_dict(rank="HAV").keys())
FEATURE_COLUMNS = FEATURE_NAMES


def load_historical_dataset() -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Fetch historical personnel and units_served data from UMS database,
    clean and engineer non-trade features for hierarchical training.
    Returns: (df_features, s_company_target, df_metadata_and_targets)
    """
    conn = get_db_connection()
    if conn is None:
        raise ConnectionError("Failed to connect to UMS database.")

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch eligible personnel records (EXCLUDING TRADE FROM TARGETS/FEATURES)
        query_personnel = """
            SELECT id, army_number, name, `rank`, company, date_of_enrollment,
                   prior_station, section, worked_it
            FROM personnel
            WHERE company IN ('HQ company', 'COMN Company', '3 Company', 'HQ Coy', 'Comn Coy', '3 Coy', 'HQ COY', 'COMN COY', '3 COY')
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
    target_companies = []
    metadata_rows = []

    for p in personnel_rows:
        pid = p.get("id")
        rank = p.get("rank") or "Signal Man"
        enroll_date = p.get("date_of_enrollment")
        target_coy = normalize_company_name(p.get("company"))
        prior_st = p.get("prior_station") or ""
        raw_sec = p.get("section") or "GENERAL DUTY"

        units = units_by_pid.get(pid, [])

        feats = extract_features_from_dict(
            rank=rank,
            date_of_enrollment=enroll_date,
            prior_station=prior_st,
            units_history=units,
            is_fresh=(len(units) == 0),
            extra_personnel_attrs={"worked_it": p.get("worked_it")}
        )

        feats["personnel_id"] = pid
        feats["army_number"] = p.get("army_number") or ""
        feature_rows.append(feats)
        target_companies.append(target_coy)

        metadata_rows.append({
            "personnel_id": pid,
            "army_number": p.get("army_number") or "",
            "target_company": target_coy,
            "target_section": raw_sec
        })

    df_features = pd.DataFrame(feature_rows)
    s_companies = pd.Series(target_companies, name="target_company")
    df_meta = pd.DataFrame(metadata_rows)

    return df_features, s_companies, df_meta
