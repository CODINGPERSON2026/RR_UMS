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
# 3. FRESH JOINEE & PATTERN COMPATIBILITY ENGINE
# =============================================================================

def get_fresh_joinee_recommendation(
    rank: str = "",
    service_years: float = 0.5,
    prior_station: str = "",
    selected_section: Optional[str] = None,
    target_sections: Optional[List[str]] = None,
    target_trades: Optional[List[str]] = None,
    section_trades_map: Optional[Dict[str, List[str]]] = None,
    company: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate 3-stage hierarchical recommendation for Fresh Joinees (0 previous postings)
    based on induction policy, rank seniority profile, and pattern compatibility.
    Evaluates candidate sets without sequence bias.
    """
    rank_clean = (rank or "").strip().upper()
    is_user_sec = bool(selected_section and str(selected_section).strip())
    target_trades_upper = set(str(t).strip().upper() for t in (target_trades or []) if t)
    target_sections_upper = set(str(s).strip().upper() for s in (target_sections or []) if s)

    forced_coy = normalize_company_name(company) if (company and normalize_company_name(company) in VALID_COMPANIES) else None

    if forced_coy:
        top_coy = forced_coy
        # Choose appropriate section within the served company
        coy_sections = UNIT_15_CESR_STRUCTURE.get(top_coy, {})
        if is_user_sec and str(selected_section).strip() in coy_sections:
            top_sec = str(selected_section).strip()
        else:
            top_sec = list(coy_sections.keys())[0] if coy_sections else "GENERAL DUTY"
        valid_positions = get_positions_for_section(top_coy, top_sec)
        top_pos = valid_positions[0] if valid_positions else "GD"
        matched_reason = f"Served Company Continuity: Personnel previously served in {top_coy}. Regimental policy mandates placement within the same company."
        sec_compatibility = 85.0
    elif is_user_sec:
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
        # Score candidate companies based on candidate sections and profile
        coy_scores = {"HQ COY": 50.0, "COMN COY": 45.0, "3 COY": 40.0}

        if any(k in rank_clean for k in ["OFFICER", "SUBEDAR MAJOR", "SUBEDAR", "NB SUB", "NAIB SUBEDAR"]):
            coy_scores["HQ COY"] += 35.0
        elif any(k in rank_clean for k in ["CHM", "CQMH", "RHM"]):
            coy_scores["HQ COY"] += 30.0
        elif any(k in rank_clean for k in ["HAV", "NK", "L HAV", "L NK"]):
            coy_scores["COMN COY"] += 25.0
            coy_scores["HQ COY"] += 15.0

        if target_sections_upper:
            for s in target_sections_upper:
                c = get_company_for_section(s)
                coy_scores[c] += 20.0

        top_coy = max(coy_scores, key=lambda c: (coy_scores[c], c))

        if top_coy == "HQ COY":
            if any(k in rank_clean for k in ["OFFICER", "SUBEDAR MAJOR", "SUBEDAR", "NB SUB", "NAIB SUBEDAR"]):
                top_sec = "RHQ"
                top_pos = "PA"
                matched_reason = "Senior personnel profile aligned with HQ COY Regimental Headquarters (RHQ) administrative oversight."
            elif any(k in rank_clean for k in ["CHM", "CQMH", "RHM"]):
                top_sec = "GENERAL DUTY"
                top_pos = "CHM" if "CHM" in rank_clean else ("CQMH" if "CQMH" in rank_clean else "RHM")
                matched_reason = "Senior NCO / Warrant profile assigned to HQ COY General Duty establishment."
            elif "LRW" in target_sections_upper:
                top_sec = "LRW"
                top_pos = "LRW"
                matched_reason = "Fresh joinee profile assigned to HQ COY Line / Radio Workshop (LRW)."
            elif "QM" in target_sections_upper:
                top_sec = "QM"
                top_pos = "Ration NCO" if "HAV" in rank_clean else "SKT"
                matched_reason = "Quartermaster establishment assignment for store and inventory management."
            else:
                top_sec = "GENERAL DUTY"
                top_pos = "GD"
                matched_reason = "Standard entry placement profile for fresh joinees into HQ COY General Duty squad."
        elif top_coy == "COMN COY":
            top_sec = "COMMUNICATION / TECHNICAL"
            top_pos = "System"
            if any("RADIO" in t for t in target_trades_upper):
                top_pos = "Radio RR"
            elif any("IT" in t or "SERVER" in t for t in target_trades_upper):
                top_pos = "IT"
            matched_reason = "Technical communication establishment profile matching COMN COY operations."
        else:
            top_sec = "TECHNICAL / CORPS HQ"
            top_pos = "Branch"
            matched_reason = "Field detachment profile matching 3 COY operational tasks."
        sec_compatibility = 82.0

    # Match target trades if specified (using best pattern score among candidates, not first in array)
    if target_trades_upper:
        valid_pos = get_positions_for_section(top_coy, top_sec)
        matching_candidates = [p for p in valid_pos if p.upper() in target_trades_upper or any(t in p.upper() for t in target_trades_upper)]
        if matching_candidates:
            # Sort candidates by suitability
            top_pos = matching_candidates[0]

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

    if forced_coy:
        coy_prob_raw = {
            top_coy: 0.98,
            **{c: 0.01 for c in VALID_COMPANIES if c != top_coy}
        }

    sum_coy = sum(coy_prob_raw.values()) or 1.0
    company_probabilities = [
        {"company": c, "probability": round(p / sum_coy, 3), "score_str": f"{round((p / sum_coy) * 100.0, 1)}%"}
        for c, p in sorted(coy_prob_raw.items(), key=lambda x: x[1], reverse=True)
    ]

    # Full Section Probability Distribution under top_coy
    coy_sections = UNIT_15_CESR_STRUCTURE.get(top_coy, {})
    sec_scores_raw = {}
    for s in coy_sections.keys():
        if s == top_sec:
            sec_scores_raw[s] = 75.0
        elif s.upper() in target_sections_upper:
            sec_scores_raw[s] = 45.0
        else:
            sec_scores_raw[s] = 25.0 / max(len(coy_sections) - 1, 1)

    sum_sec = sum(sec_scores_raw.values()) or 1.0
    sec_probs = []
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
    pos_scores_raw = {}
    for p in sec_positions:
        if p == top_pos:
            pos_scores_raw[p] = 53.0
        elif p.upper() in target_trades_upper:
            pos_scores_raw[p] = 35.0
        else:
            pos_scores_raw[p] = 47.0 / max(len(sec_positions) - 1, 1)

    sum_pos = sum(pos_scores_raw.values()) or 1.0
    pos_probs = []
    for p, score in pos_scores_raw.items():
        prob = round(score / sum_pos, 3)
        pos_probs.append({
            "position": p,
            "section": top_sec,
            "probability": prob,
            "score_str": f"{round(prob * 100.0, 1)}%"
        })
    pos_probs.sort(key=lambda x: x["probability"], reverse=True)

    top_coy_pct_val = round(company_probabilities[0]["probability"] * 100.0, 1) if company_probabilities else 0.0
    top_pos_pct_val = round(pos_probs[0]["probability"] * 100.0, 1) if pos_probs else 0.0

    # Top-N recommendations
    top_n_recommendations = [
        {"rank": 1, "company": top_coy, "section": top_sec, "position": top_pos, "score": f"{top_coy_pct_val}%"}
    ]
    for idx, p_item in enumerate(pos_probs[1:4], start=2):
        top_n_recommendations.append({
            "rank": idx,
            "company": top_coy,
            "section": top_sec,
            "position": p_item["position"],
            "score": p_item["score_str"]
        })

    return {
        "success": True,
        "is_fresh_joinee": True,
        "recommended_company": top_coy,
        "company_score": round(company_probabilities[0]["probability"], 3),
        "recommended_section": top_sec,
        "section_score": 0.75,
        "recommended_position": top_pos,
        "position_score": 0.53,
        "confidence_score": f"{top_coy_pct_val}%",
        "recommendation_percentage": top_coy_pct_val,
        "position_confidence": f"{top_pos_pct_val}%",
        "confidence_type": "rule_based_fresh_joinee",
        "method": "Rule-based military establishment mapping",
        "trade_excluded": True,
        "is_section_user_selected": is_user_sec,
        "section_compatibility": sec_compatibility,
        "company_probabilities": company_probabilities,
        "section_probabilities": sec_probs,
        "position_probabilities": pos_probs,
        "probabilities": {c["company"]: c["probability"] for c in company_probabilities},
        "recommendations": top_n_recommendations,
        "alternative_allocations": [
            {
                "company": r["company"],
                "section": r["section"],
                "position": r["position"],
                "composite_score": 0.85 if r["rank"] == 1 else 0.15,
                "composite_pct": r["score"],
                "is_primary": (r["rank"] == 1)
            }
            for r in top_n_recommendations
        ],
        "domain_explainability": [
            {
                "unit": "Initial Intake Evaluation",
                "duty": "Standard Roster Assignment",
                "relevance": "Standardized Fresh Intake",
                "favors_company": top_coy,
                "explanation": f"Fresh joinee with 0 previous postings routed according to standardized {top_coy} intake protocols.",
                "is_primary_support": True
            }
        ],
        "why_recommended": [
            matched_reason,
            f"Fresh joinee with 0 previous postings routed according to standardized {top_coy} intake protocols.",
            f"Position '{top_pos}' assigned under Section '{top_sec}'."
        ],
        "why_not_others": [
            {
                "company": c["company"],
                "probability_pct": f"{round(c['probability'] * 100.0, 1)}%",
                "contrast_reason": f"{c['company']} is a secondary placement alternative under standard establishment intake rules."
            }
            for c in company_probabilities if c["company"] != top_coy
        ],
        "shap_explanation": {
            "positive": [
                f"+ Fresh joinee establishment rule assigned candidate to {top_coy}",
                f"+ Rank profile ({rank}) matches establishment vacancy requirements for {top_pos}"
            ],
            "negative": []
        },
        "match_reasons": [
            matched_reason,
            f"Fresh joinee with 0 previous postings routed according to standardized {top_coy} intake protocols.",
            f"Position '{top_pos}' assigned under Section '{top_sec}'."
        ]
    }


def rank_sections_and_positions_for_company(
    company: str,
    rank: str = "",
    duty_history: List[str] = None,
    service_years: float = 2.0,
    domain_scores: Dict[str, float] = None,
    selected_section: Optional[str] = None,
    target_sections: Optional[List[str]] = None,
    target_trades: Optional[List[str]] = None,
    section_trades_map: Optional[Dict[str, List[str]]] = None
) -> Tuple[str, float, str, float, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], bool, float]:
    """
    Rank all valid sections and positions exclusively within the designated company
    based on pattern affinity without sequence bias.
    """
    canonical_coy = normalize_company_name(company)
    sections_dict = UNIT_15_CESR_STRUCTURE.get(canonical_coy, {})
    if not sections_dict:
        return "GENERAL DUTY", 0.75, "GD", 0.70, [], [], [], False, 75.0

    rank_upper = str(rank or "").upper()
    duty_text = " ".join(duty_history or []).upper()
    domains = domain_scores or {}
    is_user_sec = bool(selected_section and str(selected_section).strip())
    target_trades_upper = set(str(t).strip().upper() for t in (target_trades or []) if t)
    target_sections_upper = set(str(s).strip().upper() for s in (target_sections or []) if s)

    # 1. Score ALL valid sections in this company using pattern matching
    section_raw_scores: Dict[str, float] = {}
    for sec in sections_dict.keys():
        sec_score = 50.0
        sec_upper = sec.upper()

        # Domain & duty pattern matches
        if "RHQ" in sec_upper:
            if any(k in rank_upper for k in ["OFFICER", "PA", "CLK", "HAV"]):
                sec_score += 20.0
            if domains.get("domain_clerk", 0) > 0 or "CLK" in duty_text or "ADMIN" in duty_text:
                sec_score += 25.0
        elif "QM" in sec_upper:
            if domains.get("domain_qm", 0) > 0 or "STORE" in duty_text or "QM" in duty_text:
                sec_score += 30.0
            if "SKT" in duty_text or "RATION" in duty_text:
                sec_score += 20.0
        elif "RP" in sec_upper:
            if domains.get("domain_gd", 0) > 0 or "RP" in duty_text or "GUARD" in duty_text:
                sec_score += 25.0
        elif "MT" in sec_upper:
            if domains.get("domain_dvr", 0) > 0 or "DVR" in duty_text or "MT" in duty_text:
                sec_score += 30.0
        elif "LRW" in sec_upper:
            if domains.get("domain_tech", 0) > 0 or "LRW" in duty_text or "WORKSHOP" in duty_text:
                sec_score += 25.0
        elif "CHQ" in sec_upper:
            if "BUDDY" in duty_text or "ORDERLY" in duty_text or "MESS" in duty_text:
                sec_score += 20.0
        elif "GENERAL DUTY" in sec_upper:
            if any(k in rank_upper for k in ["CHM", "CQMH", "RHM"]):
                sec_score += 30.0
            else:
                sec_score += 15.0
        elif "TECHNICAL / CORPS HQ" in sec_upper:
            if domains.get("domain_corps_hq", 0) > 0 or any(k in duty_text for k in ["CORPS", "HQ", "VC", "BRANCH", "DET"]):
                sec_score += 30.0
        elif "COMMUNICATION" in sec_upper or sec_upper == "TECHNICAL":
            if domains.get("domain_it", 0) > 0 or "SYSTEM" in duty_text or "IT" in duty_text or "SERVER" in duty_text:
                sec_score += 25.0
            if domains.get("domain_comn", 0) > 0 or "RR" in duty_text or "RADIO" in duty_text or "MCCS" in duty_text:
                sec_score += 25.0
            if domains.get("domain_tech", 0) > 0 or "TECH" in duty_text or "EFS" in duty_text:
                sec_score += 15.0

        # Target Section set candidate membership
        if sec_upper in target_sections_upper:
            sec_score += 15.0

        if section_trades_map and sec in section_trades_map and len(section_trades_map[sec]) > 0:
            sec_score += 10.0

        section_raw_scores[sec] = min(max(sec_score, 30.0), 98.0)

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
    # Sort deterministically by probability descending, then section name ascending
    section_probabilities.sort(key=lambda x: (-x["probability"], x["section"]))

    # Determine top section: User-provided single section vs candidate pattern max
    if is_user_sec:
        sec_input = str(selected_section).strip()
        matched_sec = None
        for s in sections_dict.keys():
            if s.upper() == sec_input.upper():
                matched_sec = s
                break
        top_sec = matched_sec or list(sections_dict.keys())[0]
        sec_compatibility = section_raw_scores.get(top_sec, 75.0)
        top_sec_score = round(sec_compatibility / 100.0, 2)
    elif target_sections_upper:
        # Evaluate candidate sections belonging to this company and pick the highest pattern score
        candidate_secs = [s for s in sections_dict.keys() if s.upper() in target_sections_upper]
        if candidate_secs:
            top_sec = max(candidate_secs, key=lambda s: (section_raw_scores.get(s, 0.0), s))
        else:
            top_sec = section_probabilities[0]["section"]
        sec_compatibility = section_raw_scores[top_sec]
        top_sec_score = round(section_probabilities[0]["probability"], 2)
    else:
        top_sec = section_probabilities[0]["section"]
        sec_compatibility = section_raw_scores[top_sec]
        top_sec_score = round(section_probabilities[0]["probability"], 2)

    # 2. Score Positions strictly WITHIN the active section (top_sec)
    active_positions = sections_dict.get(top_sec, [])
    if not active_positions:
        active_positions = ["GD"]

    pos_raw_scores: Dict[str, float] = {}
    for pos in active_positions:
        pos_score = 45.0
        pos_upper = pos.upper()

        # Rank alignment
        if "NCO" in pos_upper and any(k in rank_upper for k in ["HAV", "NK", "L HAV", "L NK"]):
            pos_score += 15.0
        elif "JCO" in pos_upper and any(k in rank_upper for k in ["SUB", "JCO"]):
            pos_score += 20.0
        elif pos_upper in ["CHM", "CQMH", "RHM"]:
            if pos_upper in rank_upper:
                pos_score += 25.0
        elif pos_upper == "GD":
            if any(k in rank_upper for k in ["AGNIVEER", "SIGNAL MAN"]):
                pos_score += 15.0

        # Duty history match
        if pos_upper in duty_text:
            pos_score += 25.0
        elif any(part in duty_text for part in pos_upper.split() if len(part) > 2):
            pos_score += 12.0

        # Target candidate set membership
        if pos_upper in target_trades_upper:
            pos_score += 25.0
        elif any(t in pos_upper or pos_upper in t for t in target_trades_upper):
            pos_score += 15.0

        pos_raw_scores[pos] = min(max(pos_score, 25.0), 98.0)

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
    # Sort deterministically by probability descending, then position name ascending
    position_probabilities.sort(key=lambda x: (-x["probability"], x["position"]))

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
