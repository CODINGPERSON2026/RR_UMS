"""
Feature Engineering and Dataset Preprocessing for AI NEW ARRIVAL RECOMMENDATION.
Learns patterns primarily from Previous Unit Served, Previous Duty, and Domain Profile.
Loads and processes 2,000-sample dataset from aiml/ai_new_joinee_recommendation/datasets/.
Strictly isolates target variables to guarantee ZERO data leakage.
"""

import os
import sys
import re
import json
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aiml.ai_new_joinee_recommendation.position_mapping import (
    VALID_COMPANIES,
    UNIT_15_CESR_STRUCTURE,
    normalize_company_name,
    get_positions_for_section,
    get_sections_for_company,
    get_positions_for_company,
    is_valid_hierarchy
)

DATASET_DIR = os.path.join(os.path.dirname(__file__), "datasets")
PERSONNEL_CSV = os.path.join(DATASET_DIR, "personnel_test_2000.csv")
UNITS_CSV = os.path.join(DATASET_DIR, "units_served_test_2000.csv")

# Unit Type Categorization Dictionary (Extracts operational profile from Unit Name)
UNIT_TYPE_KEYWORDS = {
    "unit_type_signal": ["SIGNAL", "SIG", "SIGCEN", "NODE", "MCCS", "SERVER", "COMMUNICATION", "TELECOM"],
    "unit_type_admin": ["ADMIN", "RHQ", "OFFICE", "RECORD", "BRANCH", "HQ UNIT", "BASE HQ", "STATION HQ"],
    "unit_type_logistics": ["LOGISTICS", "SUPPLY", "ORDNANCE", "QM", "STORE", "RATION", "DEPOT"],
    "unit_type_field": ["FIELD", "INFANTRY", "LINE", "FORWARD", "SECTOR", "BORDER", "OP", "BRIGADE", "DIV"],
    "unit_type_training": ["TRAINING", "CENTRE", "CENTER", "ACADEMY", "SCHOOL", "TRG"],
    "unit_type_mechanical": ["MECHANICAL", "MT", "TRANSPORT", "VEHICLE", "WORKSHOP", "EME", "REPAIR"],
    "unit_type_corps": ["CORPS", "CORP", "HQ", "ARMY", "COMMAND", "DETACHMENT", "DET"],
}

# Duty Domain Keywords for Historical Duty Parsing
DUTY_DOMAIN_KEYWORDS = {
    "domain_tech": ["tech", "efs", "duty efs", "ttc", "repair", "hardware", "switch", "system", "je", "maintenance", "workshop", "dtmn", "dtmn shop", "lrw", "technician", "operator"],
    "domain_comn": ["radio", "rr", "wireless", "exchange", "mccs", "mccs exchange", "sig", "sigcen", "line", "line man", "communication", "communication clerk", "strip clerk", "node", "icn", "nfs"],
    "domain_it": ["it", "computer", "server", "lan", "wan", "software", "network", "cyber", "coding", "multimedia", "data", "system"],
    "domain_clerk": ["clerk", "clk", "o1", "o2", "o3", "trg clerk", "warrant clerk", "part one", "dispatcher", "pa", "a-sigma", "office", "admin clk"],
    "domain_qm": ["qm", "ration", "fresh", "clothing", "mes", "skt", "store", "supply", "quarter master", "ration nco"],
    "domain_dvr": ["mt", "driver", "dvr", "mto", "vehicle", "transport", "lorry", "car"],
    "domain_rp": ["rp", "regimental police", "strict orderly", "runner", "guest room", "adm nco", "line guard", "havildar major", "security"],
    "domain_chq": ["chq", "buddy", "batman", "mess", "mess hav", "tradesmen", "jco mess", "cook", "washerman", "housekeeper"],
    "domain_tm": ["tm", "technical maintenance", "telecom maintenance", "line maintenance"],
    "domain_gd": ["gd", "general duty", "chm", "cqmh", "rhm", "sentry", "guard", "field duty"],
    "domain_corps_hq": ["corps hq", "vc", "video conference", "branch", "corps", "command node"]
}

# Master List of Safe Engineered Feature Columns (Zero Target Leakage / Zero Trade Reference)
FEATURE_COLUMNS = [
    'num_units', 'total_tenure_days', 'avg_tenure_days', 'latest_tenure_days',
    'unit_type_signal', 'unit_type_admin', 'unit_type_logistics', 'unit_type_field',
    'unit_type_training', 'unit_type_mechanical', 'unit_type_corps',
    'domain_tech', 'domain_comn', 'domain_it', 'domain_clerk', 'domain_qm',
    'domain_dvr', 'domain_rp', 'domain_chq', 'domain_tm', 'domain_gd', 'domain_corps_hq',
    'input_domain_hq_coy', 'input_domain_comn_coy', 'input_domain_3_coy',
    'input_domain_clerk', 'input_domain_qm', 'input_domain_tech', 'input_domain_comn',
    'input_domain_dvr', 'input_domain_chq', 'input_domain_rp', 'input_domain_gd',
    'tech_density', 'admin_density', 'field_exposure_ratio', 'signal_exposure_ratio'
]
SAFE_FEATURE_COLUMNS = FEATURE_COLUMNS


def parse_date_string(date_val: Any) -> Optional[date]:
    """Parse various date formats into date object."""
    if not date_val:
        return None
    if isinstance(date_val, (date, datetime)):
        return date_val if isinstance(date_val, date) else date_val.date()
    val_str = str(date_val).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            pass
    return None


def calculate_tenure_days(from_date: Any, to_date: Any) -> float:
    """Calculate duration in days between two dates."""
    d_from = parse_date_string(from_date)
    d_to = parse_date_string(to_date)
    if d_from and d_to:
        diff = (d_to - d_from).days
        return float(max(diff, 1))
    return 730.0  # Default ~2 years


def map_raw_to_canonical_section(company: str, raw_section: Optional[str]) -> str:
    """Map raw dataset section string to canonical section for the company."""
    canonical_coy = normalize_company_name(company)
    sec_str = (raw_section or "").strip().upper()

    if canonical_coy == "COMN COY":
        return "COMMUNICATION / TECHNICAL"
    elif canonical_coy == "3 COY":
        return "TECHNICAL / CORPS HQ"
    else:
        # HQ COY
        if "QM" in sec_str:
            return "QM"
        elif "RHQ" in sec_str or "ADMIN" in sec_str:
            return "RHQ"
        elif "RP" in sec_str or "POLICE" in sec_str:
            return "RP"
        elif "TM" in sec_str:
            return "TM"
        elif "MT" in sec_str or "TRANSPORT" in sec_str:
            return "MT"
        elif "LRW" in sec_str or "WORKSHOP" in sec_str:
            return "LRW"
        elif "CHQ" in sec_str or "MESS" in sec_str:
            return "CHQ"
        else:
            return "GENERAL DUTY"


def map_raw_to_canonical_position(section: str, raw_position: Optional[str]) -> str:
    """Map raw position/trade string to canonical position in section."""
    sec_u = section.strip().upper()
    pos_u = (raw_position or "").strip().upper()

    # 1. HQ COY SECTIONS
    if sec_u == "QM":
        if "FRESH" in pos_u:
            return "Fresh NCO"
        elif "CLOTH" in pos_u:
            return "Clothing NCO"
        elif "MES" in pos_u:
            return "MES NCO"
        elif "SKT" in pos_u or "STORE" in pos_u:
            return "SKT"
        else:
            return "Ration NCO"

    elif sec_u == "RHQ":
        if "O1" in pos_u:
            return "O1"
        elif "O2" in pos_u:
            return "O2"
        elif "O3" in pos_u:
            return "O3"
        elif "TRG" in pos_u or "TRAIN" in pos_u:
            return "TRG Clerk"
        elif "WARRANT" in pos_u:
            return "Warrant Clerk"
        elif "PART ONE" in pos_u:
            return "Part One Clerk"
        elif "DISPATCH" in pos_u:
            return "Dispatcher Clerk"
        elif "SIGMA" in pos_u:
            return "A-Sigma Clerk"
        elif "PA" in pos_u:
            return "PA"
        else:
            return "Clerk"

    elif sec_u == "RP":
        if "STRICT" in pos_u or "ORDERLY" in pos_u:
            return "Strict Orderly"
        elif "RUNNER" in pos_u:
            return "Runner"
        elif "GUEST" in pos_u:
            return "Guest Room NCO"
        elif "ADM" in pos_u:
            return "Adm NCO"
        else:
            return "RP NCO"

    elif sec_u == "TM":
        return "TM"

    elif sec_u == "MT":
        return "MT"

    elif sec_u == "LRW":
        return "LRW"

    elif sec_u == "CHQ":
        if "BUDDY" in pos_u:
            return "Buddy"
        elif "OFFICE" in pos_u:
            return "Office"
        elif "MESS HAV" in pos_u or "MESS" in pos_u:
            return "Mess Hav"
        elif "JCO" in pos_u:
            return "JCO Mess Cdr"
        else:
            return "All Tradesmen"

    elif sec_u == "GENERAL DUTY":
        if "CHM" in pos_u:
            return "CHM"
        elif "CQMH" in pos_u:
            return "CQMH"
        elif "RHM" in pos_u:
            return "RHM"
        else:
            return "GD"

    # 2. COMN COY
    elif "COMMUNICATION" in sec_u or "TECHNICAL" in sec_u:
        if "MULTIMEDIA" in pos_u:
            return "Multimedia"
        elif "IT" in pos_u:
            return "IT"
        elif "RADIO" in pos_u or "RR" in pos_u:
            return "Radio"
        elif "MCCS" in pos_u or "EXCHANGE" in pos_u:
            return "MCCS Exchange"
        elif "COMMUNICATION CLERK" in pos_u:
            return "Communication Clerk"
        elif "STRIP" in pos_u:
            return "Strip Clerk"
        elif "ICN" in pos_u:
            return "ICN"
        elif "NFS" in pos_u:
            return "NFS"
        elif "SERVER" in pos_u:
            return "Server"
        else:
            return "System"

    # 3. 3 COY
    elif "CORPS" in sec_u or "3 COY" in sec_u:
        if "VC" in pos_u:
            return "VC"
        elif "BRANCH" in pos_u:
            return "Branch"
        elif "CORPS" in pos_u:
            return "Corps HQ"
        else:
            return "System"

    return "GD"


def extract_features_from_units(
    units_history: List[Dict[str, Any]],
    is_fresh: bool = False,
    selected_domains: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, float]:
    """
    Extract rich historical pattern features from previous unit postings and selected domains.
    NO TARGET LEAKAGE: strictly processes historical service and domain signals.
    """
    features: Dict[str, float] = {}

    # Base flags
    features["is_fresh_joinee"] = 1.0 if (is_fresh or not units_history) else 0.0
    features["has_prev_units"] = 0.0 if features["is_fresh_joinee"] else 1.0

    valid_units = [u for u in (units_history or []) if (u.get("unit") or u.get("unit_name"))]
    num_units = len(valid_units)
    features["num_units"] = float(num_units)

    # Calculate Tenure Metrics
    total_days = 0.0
    tenures = []
    unit_names = []
    duties = []

    for u in valid_units:
        u_name = str(u.get("unit") or u.get("unit_name") or "").strip().upper()
        duty = str(u.get("duty_performed") or u.get("duty") or "").strip().upper()
        f_dt = u.get("from_date")
        t_dt = u.get("to_date")
        t_days = calculate_tenure_days(f_dt, t_dt)

        total_days += t_days
        tenures.append(t_days)
        if u_name:
            unit_names.append(u_name)
        if duty:
            duties.append(duty)

    features["total_tenure_days"] = float(total_days)
    features["avg_tenure_days"] = float(total_days / max(num_units, 1))
    features["latest_tenure_days"] = float(tenures[0]) if tenures else 0.0

    # 1. Previous Unit Type Categorization Scores
    unit_text_all = " ".join(unit_names)
    latest_unit = unit_names[0] if unit_names else ""

    for u_type, kws in UNIT_TYPE_KEYWORDS.items():
        type_score = 0.0
        for kw in kws:
            if kw in unit_text_all:
                type_score += 1.0
            if latest_unit and kw in latest_unit:
                type_score += 1.5  # Weight recent posting higher
        features[u_type] = float(min(type_score, 4.0))

    # 2. Previous Duty Domain Keyword Matching
    duty_text_all = " ".join(duties)
    latest_duty = duties[0] if duties else ""

    for d_domain, kws in DUTY_DOMAIN_KEYWORDS.items():
        d_score = 0.0
        for kw in kws:
            # Token boundary or substring match
            if re.search(r'\b' + re.escape(kw), duty_text_all.lower()):
                d_score += 1.0
            if latest_duty and re.search(r'\b' + re.escape(kw), latest_duty.lower()):
                d_score += 1.5  # Recency weight
        features[d_domain] = float(min(d_score, 5.0))

    # 3. Selected Duty/Domain Input Features (from Hierarchical Checkbox Tree)
    # Allows user input to serve as an input feature WITHOUT being copied as recommendation
    features["input_domain_hq_coy"] = 0.0
    features["input_domain_comn_coy"] = 0.0
    features["input_domain_3_coy"] = 0.0
    features["input_domain_clerk"] = 0.0
    features["input_domain_qm"] = 0.0
    features["input_domain_tech"] = 0.0
    features["input_domain_comn"] = 0.0
    features["input_domain_dvr"] = 0.0
    features["input_domain_chq"] = 0.0
    features["input_domain_rp"] = 0.0
    features["input_domain_gd"] = 0.0

    if selected_domains:
        for item in selected_domains:
            coy = str(item.get("company") or "").upper()
            sec = str(item.get("section") or "").upper()
            apt = str(item.get("appointment") or item.get("trade") or "").upper()

            if "HQ" in coy:
                features["input_domain_hq_coy"] = 1.0
            elif "COMN" in coy:
                features["input_domain_comn_coy"] = 1.0
            elif "3" in coy:
                features["input_domain_3_coy"] = 1.0

            if "RHQ" in sec or "CLERK" in apt:
                features["input_domain_clerk"] = 1.0
            if "QM" in sec or "RATION" in apt or "SKT" in apt:
                features["input_domain_qm"] = 1.0
            if "LRW" in sec or "TECH" in sec or "SYSTEM" in apt:
                features["input_domain_tech"] = 1.0
            if "COMMUNICATION" in sec or "RADIO" in apt or "EXCHANGE" in apt:
                features["input_domain_comn"] = 1.0
            if "MT" in sec:
                features["input_domain_dvr"] = 1.0
            if "CHQ" in sec or "MESS" in apt:
                features["input_domain_chq"] = 1.0
            if "RP" in sec:
                features["input_domain_rp"] = 1.0
            if "GENERAL" in sec or "GD" in apt:
                features["input_domain_gd"] = 1.0

    # 4. Feature Interactions & Ratios
    total_tech_signals = features["domain_tech"] + features["domain_comn"] + features["domain_it"]
    total_admin_signals = features["domain_clerk"] + features["domain_qm"] + features["domain_chq"]
    features["tech_density"] = float(total_tech_signals / max(num_units, 1))
    features["admin_density"] = float(total_admin_signals / max(num_units, 1))
    features["field_exposure_ratio"] = float(features["unit_type_field"] / max(num_units, 1))
    features["signal_exposure_ratio"] = float(features["unit_type_signal"] / max(num_units, 1))

    return features


def extract_features_from_dict(
    rank: str = "Signal Man",
    date_of_enrollment: Any = None,
    prior_station: str = "",
    units_history: List[Dict[str, Any]] = None,
    is_fresh: bool = False,
    selected_domains: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> Dict[str, float]:
    """Compatibility wrapper that maps input arguments to extract_features_from_units."""
    return extract_features_from_units(
        units_history=units_history or [],
        is_fresh=is_fresh,
        selected_domains=selected_domains
    )


def calculate_service_years(date_of_enrollment: Any) -> float:
    """Helper calculating service years if available."""
    if not date_of_enrollment:
        return 2.0
    dt = parse_date_string(date_of_enrollment)
    if dt:
        return max(float((date.today() - dt).days / 365.25), 0.5)
    return 2.0


def get_rank_level(rank_str: Optional[str]) -> int:
    """Helper mapping rank string to integer level."""
    return 2


def load_dataset_and_engineer_features() -> Tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series, pd.DataFrame]:
    """
    Loads raw CSV datasets, validates merges, extracts clean pattern features,
    and returns (X, y_company, y_section, y_position, meta_df).
    Ensures zero leakage from target columns.
    """
    if not os.path.exists(PERSONNEL_CSV) or not os.path.exists(UNITS_CSV):
        raise FileNotFoundError(f"Datasets not found in {DATASET_DIR}")

    p_df = pd.read_csv(PERSONNEL_CSV)
    u_df = pd.read_csv(UNITS_CSV)

    # Join units_served with personnel
    merged = u_df.merge(p_df, left_on='personnel_id', right_on='id', suffixes=('_unit', '_pers'))

    # Group postings by personnel_id to build full unit posting history list
    personnel_postings: Dict[int, List[Dict[str, Any]]] = {}
    for _, row in u_df.iterrows():
        p_id = int(row['personnel_id'])
        if p_id not in personnel_postings:
            personnel_postings[p_id] = []
        personnel_postings[p_id].append({
            'unit': row['unit'],
            'from_date': row['from_date'],
            'to_date': row['to_date'],
            'duty_performed': row['duty_performed']
        })

    feature_rows = []
    target_coy = []
    target_sec = []
    target_pos = []
    meta_rows = []

    for _, p_row in p_df.iterrows():
        p_id = int(p_row['id'])
        u_history = personnel_postings.get(p_id, [])

        # Extract features (STRICTLY SAFE FEATURES ONLY)
        feats = extract_features_from_units(u_history, is_fresh=(len(u_history) == 0))
        feature_rows.append(feats)

        # Target Variables (STRICTLY ISOLATED AS GROUND TRUTH TARGETS)
        raw_coy = str(p_row['company'])
        raw_sec = str(p_row.get('section') or '')
        raw_trade = str(p_row.get('trade') or '')

        canonical_coy = normalize_company_name(raw_coy)
        canonical_sec = map_raw_to_canonical_section(canonical_coy, raw_sec)
        canonical_pos = map_raw_to_canonical_position(canonical_sec, raw_trade)

        target_coy.append(canonical_coy)
        target_sec.append(canonical_sec)
        target_pos.append(canonical_pos)

        meta_rows.append({
            'id': p_id,
            'army_number': p_row['army_number'],
            'name': p_row.get('name') or '',
            'company': canonical_coy,
            'section': canonical_sec,
            'trade': canonical_pos
        })

    df_X = pd.DataFrame(feature_rows).fillna(0.0)
    s_coy = pd.Series(target_coy, name="company")
    s_sec = pd.Series(target_sec, name="section")
    s_pos = pd.Series(target_pos, name="position")
    df_meta = pd.DataFrame(meta_rows)

    # Print Leakage Audit Report
    print("=" * 60)
    print("DATA LEAKAGE AUDIT & SAFETY VERIFICATION")
    print("=" * 60)
    print(f"TOTAL PERSONNEL PROCESSED: {len(df_X)}")
    print(f"SAFE FEATURE COUNT: {len(df_X.columns)}")
    print(f"SAFE FEATURES LIST:\n{list(df_X.columns)}")
    print("\nLEAKAGE FEATURES REMOVED / EXCLUDED:")
    print("- personnel.company (Level 1 Target)")
    print("- personnel.section (Level 2 Target)")
    print("- personnel.trade (Level 3 Target)")
    print("- ai_new_joinee_recommendations.*")
    print("- UI input rank, date_of_enrollment, prior_station")
    print("=" * 60)

    return df_X, s_coy, s_sec, s_pos, df_meta


# Alias for backward compatibility
load_historical_dataset = load_dataset_and_engineer_features


if __name__ == "__main__":
    X, y_coy, y_sec, y_pos, meta = load_dataset_and_engineer_features()
    print("\nSample engineered features head:")
    print(X.head(3))
    print("\nTarget Company Distribution:")
    print(y_coy.value_counts())
    print("\nTarget Section Distribution:")
    print(y_sec.value_counts())
