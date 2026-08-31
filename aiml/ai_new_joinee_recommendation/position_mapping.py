"""
Unit 15 CESR - Company, Section, and Position Master Definition & Compatibility Engine
Strictly enforces Unit 15 CESR organizational hierarchy:

UNIT: 15 CESR
├── 1. HQ COY (HQ Company)
│   ├── 1.1 QM: Ration NCO, Fresh NCO, Clothing NCO, MES NCO, SKT
│   ├── 1.2 RHQ: O1, O2, O3, TRG Clerk, Clerk, Warrant Clerk, Part One Clerk, Dispatcher Clerk, A-Sigma Clerk, PA
│   ├── 1.3 RP: Adm NCO, Strict Orderly, Runner, RP NCO, Guest Room NCO
│   ├── 1.4 TM: TM
│   ├── 1.5 MT: MT
│   ├── 1.6 LRW: LRW
│   ├── 1.7 CHQ: Buddy, Office, Mess Hav, All Tradesmen, JCO Mess Cdr
│   └── 1.8 GENERAL DUTY: CHM, CQMH, RHM, GD
├── 2. COMN COY (COMN Company)
│   └── 2.1 COMMUNICATION / TECHNICAL: Multimedia, IT, System, Radio RR, MCCS Exchange, Communication Clerk, Strip Clerk, ICN, NFS, Server
└── 3. 3 COY (3 Company)
    └── 3.1 TECHNICAL / CORPS HQ: VC, Corps HQ, System, Branch
"""

import re
from typing import Dict, List, Any, Optional, Tuple

# =============================================================================
# 1. CANONICAL COMPANY NORMALIZATION
# =============================================================================

COMPANY_ALIASES = {
    # HQ COY aliases
    "hq coy": "HQ COY",
    "hq company": "HQ COY",
    "hq": "HQ COY",
    "hq_coy": "HQ COY",
    # COMN COY aliases
    "comn coy": "COMN COY",
    "comn company": "COMN COY",
    "comn": "COMN COY",
    "communication coy": "COMN COY",
    "communication company": "COMN COY",
    "comn_coy": "COMN COY",
    # 3 COY aliases
    "3 coy": "3 COY",
    "3 company": "3 COY",
    "3_coy": "3 COY",
    "3": "3 COY",
    "third company": "3 COY"
}

# Mapping between canonical short name and DB canonical name
CANONICAL_TO_DB_COMPANY = {
    "HQ COY": "HQ company",
    "COMN COY": "COMN Company",
    "3 COY": "3 Company"
}

DB_TO_CANONICAL_COMPANY = {
    "HQ company": "HQ COY",
    "COMN Company": "COMN COY",
    "3 Company": "3 COY",
    "HQ Coy": "HQ COY",
    "Comn Coy": "COMN COY",
    "3 Coy": "3 COY"
}

VALID_COMPANIES = ["HQ COY", "COMN COY", "3 COY"]
CANONICAL_COMPANIES = VALID_COMPANIES
VALID_DB_COMPANIES = ["HQ company", "COMN Company", "3 Company"]


def normalize_company_name(coy_str: Optional[str]) -> str:
    """Normalize any company string variation to canonical name ('HQ COY', 'COMN COY', '3 COY')."""
    if not coy_str:
        return "HQ COY"
    clean = str(coy_str).strip().lower()
    return COMPANY_ALIASES.get(clean, DB_TO_CANONICAL_COMPANY.get(str(coy_str).strip(), "HQ COY"))


def to_db_company_name(coy_str: Optional[str]) -> str:
    """Convert canonical or display company string to database representation."""
    canonical = normalize_company_name(coy_str)
    return CANONICAL_TO_DB_COMPANY.get(canonical, "HQ company")


def to_display_company_name(db_coy_str: Optional[str]) -> str:
    """Convert database company name to standard display name."""
    if not db_coy_str:
        return "HQ COY"
    return DB_TO_CANONICAL_COMPANY.get(db_coy_str, normalize_company_name(db_coy_str))


# =============================================================================
# 2. UNIT 15 CESR HIERARCHY MASTER (SINGLE CENTRAL SOURCE OF TRUTH)
# =============================================================================

UNIT_15_CESR_STRUCTURE: Dict[str, Dict[str, List[str]]] = {
    "HQ COY": {
        "QM": [
            "Ration NCO",
            "Fresh NCO",
            "Clothing NCO",
            "MES NCO",
            "SKT"
        ],
        "RHQ": [
            "O1",
            "O2",
            "O3",
            "TRG Clerk",
            "Clerk",
            "Warrant Clerk",
            "Part One Clerk",
            "Dispatcher Clerk",
            "A-Sigma Clerk",
            "PA"
        ],
        "RP": [
            "Adm NCO",
            "Strict Orderly",
            "Runner",
            "RP NCO",
            "Guest Room NCO"
        ],
        "TM": [
            "TM"
        ],
        "MT": [
            "MT"
        ],
        "LRW": [
            "LRW"
        ],
        "CHQ": [
            "Buddy",
            "Office",
            "Mess Hav",
            "All Tradesmen",
            "JCO Mess Cdr"
        ],
        "GENERAL DUTY": [
            "CHM",
            "CQMH",
            "RHM",
            "GD"
        ]
    },
    "COMN COY": {
        "COMMUNICATION / TECHNICAL": [
            "Multimedia",
            "IT",
            "System",
            "Radio RR",
            "MCCS Exchange",
            "Communication Clerk",
            "Strip Clerk",
            "ICN",
            "NFS",
            "Server"
        ]
    },
    "3 COY": {
        "TECHNICAL / CORPS HQ": [
            "VC",
            "Corps HQ",
            "System",
            "Branch"
        ]
    }
}

MASTER_HIERARCHY = UNIT_15_CESR_STRUCTURE


def get_all_companies() -> List[str]:
    """Get list of all valid canonical company names."""
    return list(UNIT_15_CESR_STRUCTURE.keys())


def get_sections_for_company(company: str) -> List[str]:
    """Get all valid section names for a given company."""
    canonical = normalize_company_name(company)
    return list(UNIT_15_CESR_STRUCTURE.get(canonical, {}).keys())


def get_positions_for_section(company: str, section: str) -> List[str]:
    """Get all positions belonging to a specific section within a company."""
    canonical = normalize_company_name(company)
    sections = UNIT_15_CESR_STRUCTURE.get(canonical, {})
    for sec_name, pos_list in sections.items():
        if sec_name.strip().upper() == str(section).strip().upper():
            return pos_list
    return []


def get_positions_for_company(company: str) -> List[str]:
    """Get flat list of all valid positions within a given company."""
    canonical = normalize_company_name(company)
    sections = UNIT_15_CESR_STRUCTURE.get(canonical, {})
    positions: List[str] = []
    for pos_list in sections.values():
        positions.extend(pos_list)
    return positions


def get_company_for_section(section: str) -> str:
    """Find the company that owns a given section."""
    if not section:
        return "HQ COY"
    sec_clean = str(section).strip().upper()
    for coy, sections in UNIT_15_CESR_STRUCTURE.items():
        for s in sections.keys():
            if s.upper() == sec_clean:
                return coy
    return "HQ COY"


def get_section_for_position(company: str, position: str) -> str:
    """Find the section that owns a position within a company."""
    canonical = normalize_company_name(company)
    sections = UNIT_15_CESR_STRUCTURE.get(canonical, {})
    pos_clean = str(position).strip().lower()
    for sec_name, pos_list in sections.items():
        for p in pos_list:
            if p.lower() == pos_clean:
                return sec_name
    return list(sections.keys())[0] if sections else "GENERAL DUTY"


def is_position_valid_for_company(company: str, position: str) -> bool:
    """Validate that a position strictly belongs to the specified company."""
    valid_positions = [p.lower() for p in get_positions_for_company(company)]
    return str(position).strip().lower() in valid_positions


def is_valid_hierarchy(company: str, section: str, position: str) -> bool:
    """Strictly validate that company -> section -> position is a valid combination."""
    canonical = normalize_company_name(company)
    if canonical not in UNIT_15_CESR_STRUCTURE:
        return False
    sections = UNIT_15_CESR_STRUCTURE[canonical]
    matching_sec = None
    for s in sections:
        if s.strip().upper() == str(section).strip().upper():
            matching_sec = s
            break
    if not matching_sec:
        return False
    pos_clean = str(position).strip().lower()
    valid_pos = [p.lower() for p in sections[matching_sec]]
    return pos_clean in valid_pos


def get_full_hierarchy_dict() -> Dict[str, Dict[str, List[str]]]:
    """Return complete hierarchical structure as a nested dict."""
    return UNIT_15_CESR_STRUCTURE


# =============================================================================
# 3. FRESH JOINEE RULE-BASED ENGINE (NO TRADE USED)
# =============================================================================

def get_fresh_joinee_recommendation(
    rank: str = "Agniveer",
    service_years: float = 0.5,
    prior_station: str = "",
    selected_section: Optional[str] = None
) -> Dict[str, Any]:
    """
    Produce structured hierarchical recommendation for fresh joinees (0 previous postings).
    Based strictly on non-trade personnel attributes: rank seniority and induction profile.
    Hierarchy: Company -> Section -> Position.
    Supports Mode A (Auto-predict Section) & Mode B (User-provided Section).
    """
    rank_clean = (rank or "Agniveer").strip().upper()
    is_user_sec = bool(selected_section and str(selected_section).strip())

    if is_user_sec:
        sec_clean = str(selected_section).strip()
        top_coy = get_company_for_section(sec_clean)
        top_sec = sec_clean
        # Ensure section exists in top_coy
        if top_sec not in UNIT_15_CESR_STRUCTURE.get(top_coy, {}):
            for s in UNIT_15_CESR_STRUCTURE.get(top_coy, {}).keys():
                if s.upper() == top_sec.upper():
                    top_sec = s
                    break
        valid_positions = get_positions_for_section(top_coy, top_sec)
        top_pos = valid_positions[0] if valid_positions else "GD"
        matched_reason = f"User selected Section '{top_sec}' mapped to parent Company '{top_coy}'."
        sec_compatibility = 75.0
    else:
        # Determine company placement based on induction and rank cohort
        if any(k in rank_clean for k in ["OFFICER", "SUBEDAR MAJOR", "SUBEDAR", "NB SUB", "NAIB SUBEDAR"]):
            top_coy = "HQ COY"
            top_sec = "RHQ"
            top_pos = "PA"
            matched_reason = "Senior personnel profile aligned with HQ COY Regimental Headquarters (RHQ) administrative oversight."
        elif any(k in rank_clean for k in ["CHM", "CQMH", "RHM"]):
            top_coy = "HQ COY"
            top_sec = "GENERAL DUTY"
            top_pos = "CHM" if "CHM" in rank_clean else ("CQMH" if "CQMH" in rank_clean else "RHM")
            matched_reason = "Senior NCO / Warrant profile assigned to HQ COY General Duty establishment."
        elif any(k in rank_clean for k in ["HAV", "NK", "L HAV", "L NK"]):
            top_coy = "COMN COY"
            top_sec = "COMMUNICATION / TECHNICAL"
            top_pos = "System"
            matched_reason = "Experienced NCO rank profile matches COMN COY technical and network infrastructure operations."
        else:
            # Standard induction (Agniveer / Signal Man)
            top_coy = "HQ COY"
            top_sec = "GENERAL DUTY"
            top_pos = "GD"
            matched_reason = "Standard entry placement profile for fresh joinees into HQ COY General Duty squad."
        sec_compatibility = 82.0

    # Validate position is valid for top_coy and top_sec
    if not is_valid_hierarchy(top_coy, top_sec, top_pos):
        top_pos = get_positions_for_section(top_coy, top_sec)[0]

    # Full Company Probability Distribution
    coy_prob_raw = {
        "HQ COY": 0.603 if top_coy == "HQ COY" else 0.20,
        "3 COY": 0.215 if top_coy != "3 COY" else 0.60,
        "COMN COY": 0.182 if top_coy != "COMN COY" else 0.60
    }
    if top_coy == "3 COY":
        coy_prob_raw = {"3 COY": 0.603, "HQ COY": 0.215, "COMN COY": 0.182}
    elif top_coy == "COMN COY":
        coy_prob_raw = {"COMN COY": 0.603, "HQ COY": 0.215, "3 COY": 0.182}

    sum_coy = sum(coy_prob_raw.values()) or 1.0
    company_probabilities = [
        {"company": c, "probability": round(p / sum_coy, 3), "score_str": f"{round((p / sum_coy) * 100.0, 1)}%"}
        for c, p in coy_prob_raw.items()
    ]
    company_probabilities.sort(key=lambda x: x["probability"], reverse=True)

    # Full Section Probability Distribution under top_coy
    coy_sections = UNIT_15_CESR_STRUCTURE.get(top_coy, {})
    sec_probs = []
    sec_scores_raw = {}
    for s in coy_sections.keys():
        if s == top_sec:
            sec_scores_raw[s] = 75.0
        else:
            sec_scores_raw[s] = 25.0 / max(len(coy_sections) - 1, 1)

    sum_sec = sum(sec_scores_raw.values()) or 1.0
    for s, score in sec_scores_raw.items():
        prob = round(score / sum_sec, 3)
        sec_probs.append({
            "section": s,
            "company": top_coy,
            "probability": prob,
            "score_str": f"{round(prob * 100.0, 1)}%",
            "is_selected": (s == top_sec and is_user_sec)
        })
    sec_probs.sort(key=lambda x: x["probability"], reverse=True)

    # Full Position Probability Distribution within top_sec
    sec_positions = coy_sections.get(top_sec, [top_pos])
    pos_probs = []
    pos_scores_raw = {}
    for p in sec_positions:
        if p == top_pos:
            pos_scores_raw[p] = 53.0
        else:
            pos_scores_raw[p] = 47.0 / max(len(sec_positions) - 1, 1)

    sum_pos = sum(pos_scores_raw.values()) or 1.0
    for p, score in pos_scores_raw.items():
        prob = round(score / sum_pos, 3)
        pos_probs.append({
            "position": p,
            "section": top_sec,
            "probability": prob,
            "score_str": f"{round(prob * 100.0, 1)}%"
        })
    pos_probs.sort(key=lambda x: x["probability"], reverse=True)

    # Top-N hierarchical recommendations
    top_recommendations = []
    for idx, p_item in enumerate(pos_probs[:6], start=1):
        top_recommendations.append({
            "rank": idx,
            "company": top_coy,
            "section": top_sec,
            "position": p_item["position"],
            "score": p_item["score_str"]
        })

    match_reasons = [
        f"Fresh Joinee Rule-Based Placement Profile (0 Previous Postings)",
        matched_reason,
        f"Recommended appointment '{top_pos}' resides in Section '{top_sec}' under {top_coy}",
        f"Highest position probability within '{top_sec}' at {pos_probs[0]['score_str']}"
    ]

    shap_factors = {
        "positive": [
            f"+ Rank Profile ({rank_clean}) aligns with {top_coy} - {top_sec} operational capacity",
            f"+ Fresh joinee induction pipeline matches {top_coy} onboarding establishment"
        ],
        "negative": [
            "- No previous unit posting history available (Rule-based evaluation applied)"
        ]
    }

    return {
        "success": True,
        "recommended_company": top_coy,
        "company_score": company_probabilities[0]["probability"],
        "recommended_section": top_sec,
        "section_score": round(sec_compatibility / 100.0, 2),
        "section_compatibility": round(sec_compatibility, 1),
        "is_section_user_selected": is_user_sec,
        "recommended_position": top_pos,
        "position_score": pos_probs[0]["probability"],
        "db_company": to_db_company_name(top_coy),
        "confidence_score": company_probabilities[0]["score_str"],
        "recommendation_percentage": round(company_probabilities[0]["probability"] * 100.0, 1),
        "confidence_type": "rule_based_fresh_joinee",
        "position_confidence": pos_probs[0]["score_str"],
        "probabilities": {item["company"]: item["probability"] for item in company_probabilities},
        "company_probabilities": company_probabilities,
        "section_probabilities": sec_probs,
        "position_probabilities": pos_probs,
        "recommendations": top_recommendations,
        "match_reasons": match_reasons,
        "shap_explanation": shap_factors,
        "is_fresh_joinee": True,
        "trade_excluded": True,
        "method": "Fresh Joinee – Rule-Based Hierarchy Mapping"
    }


# =============================================================================
# 4. CONDITIONAL SECTION & POSITION RANKER (STAGE 2 & 3 - TRADE-FREE)
# =============================================================================

def rank_sections_and_positions_for_company(
    company: str,
    rank: str = "",
    duty_history: List[str] = None,
    service_years: float = 2.0,
    domain_scores: Dict[str, float] = None,
    selected_section: Optional[str] = None
) -> Tuple[str, float, str, float, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], bool, float]:
    """
    Stage 2 & Stage 3: Evaluate and rank Sections and Positions CONDITIONAL strictly
    on the predicted company and (optionally) user-selected Section without ANY trade features.
    
    Returns:
    (
        top_section,
        section_score,
        top_position,
        position_score,
        top_n_recommendations,
        section_probabilities,
        position_probabilities,
        is_section_user_selected,
        section_compatibility
    )
    """
    canonical_coy = normalize_company_name(company)
    sections_dict = UNIT_15_CESR_STRUCTURE.get(canonical_coy, {})
    if not sections_dict:
        return "GENERAL DUTY", 0.75, "GD", 0.70, [], [], [], False, 75.0

    rank_upper = str(rank or "").upper()
    duty_text = " ".join(duty_history or []).upper()
    domains = domain_scores or {}
    is_user_sec = bool(selected_section and str(selected_section).strip())

    # 1. Score ALL valid sections in this company
    section_raw_scores: Dict[str, float] = {}
    for sec in sections_dict.keys():
        sec_score = 50.0
        sec_upper = sec.upper()

        if "RHQ" in sec_upper:
            if any(k in rank_upper for k in ["OFFICER", "PA", "CLK", "HAV"]):
                sec_score += 25.0
            if domains.get("domain_clerk", 0) > 0 or "CLK" in duty_text or "ADMIN" in duty_text:
                sec_score += 30.0
        elif "QM" in sec_upper:
            if domains.get("domain_qm", 0) > 0 or "STORE" in duty_text or "QM" in duty_text:
                sec_score += 35.0
            if "SKT" in duty_text or "RATION" in duty_text:
                sec_score += 25.0
        elif "RP" in sec_upper:
            if domains.get("domain_gd", 0) > 0 or "RP" in duty_text or "GUARD" in duty_text:
                sec_score += 30.0
        elif "MT" in sec_upper:
            if domains.get("domain_dvr", 0) > 0 or "DVR" in duty_text or "MT" in duty_text:
                sec_score += 35.0
        elif "COMMUNICATION" in sec_upper or "TECHNICAL" in sec_upper:
            if domains.get("domain_it", 0) > 0 or "SYSTEM" in duty_text or "IT" in duty_text or "SERVER" in duty_text:
                sec_score += 30.0
            if domains.get("domain_comn", 0) > 0 or "RR" in duty_text or "RADIO" in duty_text or "MCCS" in duty_text:
                sec_score += 25.0
            if domains.get("domain_tech", 0) > 0 or "TECH" in duty_text or "EFS" in duty_text:
                sec_score += 20.0
        elif "CHQ" in sec_upper:
            if "BUDDY" in duty_text or "ORDERLY" in duty_text or "MESS" in duty_text:
                sec_score += 25.0
        elif "GENERAL DUTY" in sec_upper:
            if any(k in rank_upper for k in ["CHM", "CQMH", "RHM"]):
                sec_score += 35.0
            else:
                sec_score += 15.0

        section_raw_scores[sec] = min(max(sec_score, 45.0), 98.0)

    # Calculate full normalized Section Probability Distribution
    sum_sec_raw = sum(section_raw_scores.values()) or 1.0
    section_probabilities: List[Dict[str, Any]] = []
    for s, raw_s in section_raw_scores.items():
        prob = round(raw_s / sum_sec_raw, 3)
        section_probabilities.append({
            "section": s,
            "company": canonical_coy,
            "probability": prob,
            "score_str": f"{round(prob * 100.0, 1)}%",
            "raw_compatibility": round(raw_s, 1),
            "is_selected": (is_user_sec and s.upper() == str(selected_section).strip().upper())
        })
    section_probabilities.sort(key=lambda x: x["probability"], reverse=True)

    # Determine top section: User-provided vs Model-predicted
    if is_user_sec:
        # User specified section
        sec_input = str(selected_section).strip()
        matched_sec = None
        for s in sections_dict.keys():
            if s.upper() == sec_input.upper():
                matched_sec = s
                break
        top_sec = matched_sec or list(sections_dict.keys())[0]
        sec_compatibility = section_raw_scores.get(top_sec, 75.0)
        top_sec_score = round(sec_compatibility / 100.0, 2)
    else:
        top_sec = max(section_raw_scores, key=section_raw_scores.get)
        sec_compatibility = section_raw_scores[top_sec]
        top_sec_score = round(section_probabilities[0]["probability"], 2)

    # 2. Score Positions strictly WITHIN the active section (top_sec)
    active_positions = sections_dict.get(top_sec, [])
    if not active_positions:
        active_positions = ["GD"]

    pos_raw_scores: Dict[str, float] = {}
    for pos in active_positions:
        pos_score = 50.0
        pos_upper = pos.upper()

        # Rank alignment
        if "NCO" in pos_upper and any(k in rank_upper for k in ["HAV", "NK", "L HAV", "L NK"]):
            pos_score += 15.0
        elif "JCO" in pos_upper and any(k in rank_upper for k in ["SUB", "JCO"]):
            pos_score += 20.0
        elif pos_upper in ["CHM", "CQMH", "RHM"] and pos_upper in rank_upper:
            pos_score += 25.0
        elif pos_upper == "GD" and any(k in rank_upper for k in ["AGNIVEER", "SIGNAL MAN"]):
            pos_score += 15.0

        # Duty history match
        if pos_upper in duty_text:
            pos_score += 20.0
        elif any(part in duty_text for part in pos_upper.split()):
            pos_score += 10.0

        pos_raw_scores[pos] = min(max(pos_score, 45.0), 96.0)

    # Calculate full conditional Position Probability Distribution
    sum_pos_raw = sum(pos_raw_scores.values()) or 1.0
    position_probabilities: List[Dict[str, Any]] = []
    for p, raw_p in pos_raw_scores.items():
        prob = round(raw_p / sum_pos_raw, 3)
        position_probabilities.append({
            "position": p,
            "section": top_sec,
            "probability": prob,
            "score_str": f"{round(prob * 100.0, 1)}%",
            "raw_score": round(raw_p, 1)
        })
    position_probabilities.sort(key=lambda x: x["probability"], reverse=True)

    top_pos_item = position_probabilities[0]
    top_pos = top_pos_item["position"]
    top_pos_score = top_pos_item["probability"]

    # 3. Compile Top-N hierarchical recommendations table
    top_n_recommendations = []
    for idx, item in enumerate(position_probabilities[:6], start=1):
        top_n_recommendations.append({
            "rank": idx,
            "company": canonical_coy,
            "section": top_sec,
            "position": item["position"],
            "score": item["score_str"]
        })

    return (
        top_sec,
        top_sec_score,
        top_pos,
        top_pos_score,
        top_n_recommendations,
        section_probabilities,
        position_probabilities,
        is_user_sec,
        sec_compatibility
    )
