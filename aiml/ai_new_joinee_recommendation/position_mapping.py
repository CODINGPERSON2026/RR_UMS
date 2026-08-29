"""
Unit 15 CESR - Company, Section, and Position Master Definition & Compatibility Engine
Strictly enforces Unit 15 CESR organizational hierarchy:
UNIT: 15 CESR
├── HQ Coy (HQ Company)
│   ├── QM: Ration NCO, Fresh NCO, Clothing NCO, MES NCO, SKT
│   ├── RHQ: O1, O2, O3, TRG Clerk, Clerk, Warrant Clerk, Part One Clerk, Dispatcher Clerk, A-Sigma Clerk, PA
│   ├── RP: Adm NCO, Strict Orderly, Runner, RP NCO, Guest Room NCO
│   ├── TM: TM
│   ├── MT: MT
│   ├── LRW: LRW
│   ├── CHQ: Buddy, Office, Mess Hav, All Tradesmen, JCO Mess Cdr
│   └── GENERAL DUTY: CHM, CQMH, RHM, GD
├── Comn Coy (COMN Company)
│   └── COMMUNICATION / TECHNICAL: Multimedia, IT, System, Radio RR, MCCS Exchange, Communication Clerk, Strip Clerk, ICN, NFS, Server
└── 3 Coy (3 Company)
    └── TECHNICAL / CORPS HQ: VC, Corps HQ, System, Branch
"""

import re
from typing import Dict, List, Any, Optional, Tuple

# =============================================================================
# 1. CANONICAL COMPANY NORMALIZATION
# =============================================================================

COMPANY_ALIASES = {
    # HQ Coy aliases
    "hq coy": "HQ Coy",
    "hq company": "HQ Coy",
    "hq": "HQ Coy",
    "hq_coy": "HQ Coy",
    # Comn Coy aliases
    "comn coy": "Comn Coy",
    "comn company": "Comn Coy",
    "comn": "Comn Coy",
    "communication coy": "Comn Coy",
    "communication company": "Comn Coy",
    "comn_coy": "Comn Coy",
    # 3 Coy aliases
    "3 coy": "3 Coy",
    "3 company": "3 Coy",
    "3_coy": "3 Coy",
    "3": "3 Coy",
    "third company": "3 Coy"
}

# Mapping between canonical short name and DB canonical name
CANONICAL_TO_DB_COMPANY = {
    "HQ Coy": "HQ company",
    "Comn Coy": "COMN Company",
    "3 Coy": "3 Company"
}

DB_TO_CANONICAL_COMPANY = {
    "HQ company": "HQ Coy",
    "COMN Company": "Comn Coy",
    "3 Company": "3 Coy"
}

VALID_COMPANIES = ["HQ Coy", "Comn Coy", "3 Coy"]
VALID_DB_COMPANIES = ["HQ company", "COMN Company", "3 Company"]


def normalize_company_name(coy_str: Optional[str]) -> str:
    """Normalize any company string variation to canonical name ('HQ Coy', 'Comn Coy', '3 Coy')."""
    if not coy_str:
        return "HQ Coy"
    clean = str(coy_str).strip().lower()
    return COMPANY_ALIASES.get(clean, "HQ Coy")


def to_db_company_name(coy_str: Optional[str]) -> str:
    """Convert canonical or display company string to database representation."""
    canonical = normalize_company_name(coy_str)
    return CANONICAL_TO_DB_COMPANY.get(canonical, "HQ company")


def to_display_company_name(db_coy_str: Optional[str]) -> str:
    """Convert database company name to standard display name."""
    if not db_coy_str:
        return "HQ Coy"
    return DB_TO_CANONICAL_COMPANY.get(db_coy_str, normalize_company_name(db_coy_str))


# =============================================================================
# 2. UNIT 15 CESR HIERARCHY MASTER
# =============================================================================

UNIT_15_CESR_STRUCTURE: Dict[str, Dict[str, List[str]]] = {
    "HQ Coy": {
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
    "Comn Coy": {
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
    "3 Coy": {
        "TECHNICAL / CORPS HQ": [
            "VC",
            "Corps HQ",
            "System",
            "Branch"
        ]
    }
}


def get_sections_for_company(company: str) -> List[str]:
    """Get all valid section names for a given company."""
    canonical = normalize_company_name(company)
    return list(UNIT_15_CESR_STRUCTURE.get(canonical, {}).keys())


def get_positions_for_company(company: str) -> List[str]:
    """Get flat list of all valid positions within a given company."""
    canonical = normalize_company_name(company)
    sections = UNIT_15_CESR_STRUCTURE.get(canonical, {})
    positions = []
    for pos_list in sections.values():
        positions.extend(pos_list)
    return positions


def get_section_for_position(company: str, position: str) -> str:
    """Find the section that owns a position within a company."""
    canonical = normalize_company_name(company)
    sections = UNIT_15_CESR_STRUCTURE.get(canonical, {})
    pos_lower = position.strip().lower()
    for sec_name, pos_list in sections.items():
        for p in pos_list:
            if p.lower() == pos_lower:
                return sec_name
    # Fallback to first section of that company
    return list(sections.keys())[0] if sections else "GENERAL"


def is_position_valid_for_company(company: str, position: str) -> bool:
    """Validate that a position strictly belongs to the specified company."""
    valid_positions = [p.lower() for p in get_positions_for_company(company)]
    return position.strip().lower() in valid_positions


# =============================================================================
# 3. SPECIALTY & TRADE AFFINITY MATRICES
# =============================================================================

# Known specialties supported in the frontend and feature engineering
VALID_SPECIALTIES = [
    "IT",
    "Radio",
    "Technical",
    "Clerk",
    "System",
    "Network",
    "Security",
    "Admin",
    "QM / Logistics",
    "MT / Driver",
    "Signal / Comn",
    "General Duty"
]

# Trade / Specialty keyword mappings
SPECIALTY_KEYWORDS: Dict[str, List[str]] = {
    "IT": ["it", "computer", "software", "programmer", "server", "lan", "wan", "cyber", "system", "je sys", "tech sa"],
    "Radio": ["radio", "rr", "wireless", "mw", "vhf", "uhf", "h/f", "sig", "sigcen", "mccs", "exchange", "dvr mt(rec)"],
    "Technical": ["tech", "technician", "efs", "ttc", "jene", "je ne", "lmn", "line man", "artsan", "artish", "welder", "er", "dtmn"],
    "Clerk": ["clk", "clerk", "sd", "clk sd", "pa", "typist", "dispatcher", "warrant", "admin", "office"],
    "System": ["system", "sys", "server", "database", "nfs", "icn", "multimedia"],
    "Network": ["icn", "nfs", "network", "lan", "optical", "fiber", "switch", "router"],
    "QM / Logistics": ["qm", "skt", "ration", "clothing", "mes", "store", "storekeeper", "atbv", "aebv", "wm", "w/m"],
    "MT / Driver": ["dvr", "driver", "mt", "dmv", "transport", "vehicle", "mechanic"],
    "General Duty": ["gd", "general", "chm", "cqmh", "rhm", "buddy", "runner", "hk", "hkeeper", "h/k", "chef", "stwd"]
}

# Company affinity by trade/specialty (Default prior probabilities)
SPECIALTY_COMPANY_AFFINITY: Dict[str, Dict[str, float]] = {
    "IT": {"Comn Coy": 0.70, "3 Coy": 0.20, "HQ Coy": 0.10},
    "Radio": {"Comn Coy": 0.75, "3 Coy": 0.15, "HQ Coy": 0.10},
    "Technical": {"Comn Coy": 0.45, "3 Coy": 0.35, "HQ Coy": 0.20},
    "Clerk": {"HQ Coy": 0.65, "Comn Coy": 0.25, "3 Coy": 0.10},
    "System": {"Comn Coy": 0.50, "3 Coy": 0.40, "HQ Coy": 0.10},
    "Network": {"Comn Coy": 0.75, "3 Coy": 0.20, "HQ Coy": 0.05},
    "Security": {"HQ Coy": 0.50, "3 Coy": 0.30, "Comn Coy": 0.20},
    "Admin": {"HQ Coy": 0.70, "Comn Coy": 0.20, "3 Coy": 0.10},
    "QM / Logistics": {"HQ Coy": 0.85, "Comn Coy": 0.10, "3 Coy": 0.05},
    "MT / Driver": {"HQ Coy": 0.75, "Comn Coy": 0.15, "3 Coy": 0.10},
    "Signal / Comn": {"Comn Coy": 0.65, "3 Coy": 0.25, "HQ Coy": 0.10},
    "General Duty": {"HQ Coy": 0.75, "Comn Coy": 0.15, "3 Coy": 0.10}
}

# Position-to-specialty qualification weights
POSITION_SPECIALTY_WEIGHTS: Dict[str, Dict[str, float]] = {
    # Comn Coy Positions
    "IT": {"IT": 1.0, "System": 0.8, "Technical": 0.6, "Network": 0.7},
    "Server": {"System": 1.0, "IT": 0.9, "Network": 0.8, "Technical": 0.5},
    "System": {"System": 1.0, "IT": 0.85, "Technical": 0.7, "Network": 0.6},
    "Radio RR": {"Radio": 1.0, "Signal / Comn": 0.9, "Technical": 0.6},
    "ICN": {"Network": 1.0, "IT": 0.8, "Signal / Comn": 0.7, "System": 0.6},
    "NFS": {"Network": 0.9, "System": 0.8, "IT": 0.7, "Technical": 0.6},
    "Multimedia": {"IT": 0.8, "System": 0.7, "Technical": 0.6, "Admin": 0.5},
    "MCCS Exchange": {"Radio": 0.9, "Signal / Comn": 0.9, "Technical": 0.6},
    "Communication Clerk": {"Clerk": 1.0, "Signal / Comn": 0.7, "Admin": 0.6},
    "Strip Clerk": {"Clerk": 1.0, "Radio": 0.7, "Signal / Comn": 0.6},

    # HQ Coy Positions
    "Ration NCO": {"QM / Logistics": 1.0, "Admin": 0.6, "General Duty": 0.5},
    "Fresh NCO": {"QM / Logistics": 1.0, "Admin": 0.5, "General Duty": 0.5},
    "Clothing NCO": {"QM / Logistics": 1.0, "Admin": 0.5, "General Duty": 0.5},
    "MES NCO": {"QM / Logistics": 0.9, "Technical": 0.7, "Admin": 0.5},
    "SKT": {"QM / Logistics": 1.0, "Technical": 0.7, "Clerk": 0.6},
    "O1": {"Admin": 0.9, "Clerk": 0.8, "General Duty": 0.6},
    "O2": {"Admin": 0.9, "Clerk": 0.8, "General Duty": 0.6},
    "O3": {"Admin": 0.9, "Clerk": 0.8, "General Duty": 0.6},
    "TRG Clerk": {"Clerk": 1.0, "Admin": 0.8, "IT": 0.5},
    "Clerk": {"Clerk": 1.0, "Admin": 0.8},
    "Warrant Clerk": {"Clerk": 1.0, "Admin": 0.8},
    "Part One Clerk": {"Clerk": 1.0, "Admin": 0.8},
    "Dispatcher Clerk": {"Clerk": 1.0, "Admin": 0.8},
    "A-Sigma Clerk": {"Clerk": 1.0, "Radio": 0.7, "Signal / Comn": 0.6},
    "PA": {"Clerk": 1.0, "Admin": 0.9, "IT": 0.6},
    "Adm NCO": {"Admin": 1.0, "General Duty": 0.8},
    "Strict Orderly": {"Admin": 0.7, "General Duty": 0.9},
    "Runner": {"General Duty": 1.0},
    "RP NCO": {"Admin": 0.8, "General Duty": 0.9},
    "Guest Room NCO": {"Admin": 0.8, "General Duty": 0.8},
    "TM": {"Technical": 0.9, "Signal / Comn": 0.7},
    "MT": {"MT / Driver": 1.0, "Technical": 0.6},
    "LRW": {"Technical": 1.0, "Radio": 0.7},
    "Buddy": {"General Duty": 1.0},
    "Office": {"Admin": 0.9, "Clerk": 0.8},
    "Mess Hav": {"General Duty": 0.9, "QM / Logistics": 0.6},
    "All Tradesmen": {"Technical": 0.9, "General Duty": 0.7},
    "JCO Mess Cdr": {"General Duty": 0.9, "Admin": 0.8},
    "CHM": {"General Duty": 1.0, "Admin": 0.8},
    "CQMH": {"QM / Logistics": 0.9, "General Duty": 0.9},
    "RHM": {"General Duty": 1.0, "Admin": 0.8},
    "GD": {"General Duty": 1.0},

    # 3 Coy Positions
    "VC": {"Technical": 0.9, "System": 0.8, "Signal / Comn": 0.8},
    "Corps HQ": {"Admin": 0.9, "Signal / Comn": 0.8, "Clerk": 0.7, "System": 0.6},
    "System": {"System": 1.0, "Technical": 0.8, "IT": 0.7},
    "Branch": {"Technical": 0.8, "Signal / Comn": 0.8, "Admin": 0.6}
}


def extract_specialties_from_trade_and_text(trade: str, text: str = "") -> List[str]:
    """
    Extract matching standard specialties from trade name or combined text description.
    """
    combined = f"{trade} {text}".lower()
    matched = []
    for spec, kws in SPECIALTY_KEYWORDS.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', combined):
                if spec not in matched:
                    matched.append(spec)
                break

    # If no specialty could be detected, fallback to General Duty
    if not matched:
        matched.append("General Duty")
    return matched


# =============================================================================
# 4. FRESH JOINEE RULE-BASED ENGINE
# =============================================================================

def get_fresh_joinee_recommendation(
    trade: str,
    specialties: List[str],
    rank: str = "Agniveer"
) -> Dict[str, Any]:
    """
    Produce 100% rule-based recommendation for fresh joinees (0 previous postings).
    Hierarchy: Company -> Section -> Position with 100% confidence.
    Clearly marked as rule-based mapping.
    """
    clean_trade = (trade or "").strip().upper()
    active_specialties = specialties or extract_specialties_from_trade_and_text(trade)

    # 1. Company Mapping Priority based on trade/specialties
    top_coy = "HQ Coy"
    top_pos = "GD"
    matched_reason = "Standard entry placement profile for fresh joinees."

    # Analyze active specialties
    spec_set = set(active_specialties)
    
    if any(s in spec_set for s in ["IT", "System", "Network"]) or any(k in clean_trade for k in ["IT", "SYS", "TTC", "EFS", "JE SYS", "TECH SA"]):
        top_coy = "Comn Coy"
        if "IT" in spec_set or "IT" in clean_trade:
            top_pos = "IT"
            matched_reason = "IT / Computing specialty matches Comn Coy technical infrastructure pipeline."
        elif "System" in spec_set or "Network" in spec_set:
            top_pos = "Server"
            matched_reason = "System and network specialization directly matches Comn Coy server operations."
        else:
            top_pos = "System"
            matched_reason = "Technical trade profile directly aligns with Comn Coy technical division."
    elif any(s in spec_set for s in ["Radio", "Signal / Comn"]) or any(k in clean_trade for k in ["RR", "RADIO", "SIG", "MCCS", "DSR"]):
        top_coy = "Comn Coy"
        top_pos = "Radio RR"
        matched_reason = "Radio / Wireless trade profile directly matches Comn Coy communication wings."
    elif "Clerk" in spec_set or any(k in clean_trade for k in ["CLK", "CLERK", "SD", "PA"]):
        top_coy = "HQ Coy"
        top_pos = "Clerk"
        matched_reason = "Clerk specialty directly qualifies for HQ Coy RHQ administrative section."
    elif "QM / Logistics" in spec_set or any(k in clean_trade for k in ["QM", "SKT", "ATBV", "AEBV", "WM", "W/M", "STWD"]):
        top_coy = "HQ Coy"
        top_pos = "SKT" if "SKT" in clean_trade else "Ration NCO"
        matched_reason = "Logistics / QM store trade aligns with HQ Coy Quartermaster division."
    elif "MT / Driver" in spec_set or any(k in clean_trade for k in ["DVR", "MT", "DMV"]):
        top_coy = "HQ Coy"
        top_pos = "MT"
        matched_reason = "Driver / MT trade matches HQ Coy Mechanical Transport division."
    elif any(k in clean_trade for k in ["LRW", "ER", "WELDER", "ARTSN", "ARTISH"]):
        top_coy = "HQ Coy"
        top_pos = "LRW"
        matched_reason = "Light repair workshop trade fits HQ Coy technical workshop division."
    else:
        # Default fresh joinee assignment
        top_coy = "HQ Coy"
        top_pos = "GD"
        matched_reason = "General induction placement mapped to HQ Coy General Duty squad."

    # Validate position is in top_coy
    if not is_position_valid_for_company(top_coy, top_pos):
        top_pos = get_positions_for_company(top_coy)[0]

    top_section = get_section_for_position(top_coy, top_pos)

    # Compile alternative positions within that company ONLY
    all_coy_positions = get_positions_for_company(top_coy)
    ranked_alternatives = []
    for pos in all_coy_positions:
        if pos != top_pos:
            sec = get_section_for_position(top_coy, pos)
            ranked_alternatives.append({
                "position": pos,
                "section": sec,
                "score": 85.0 if sec == top_section else 70.0,
                "confidence": "85.0%" if sec == top_section else "70.0%"
            })

    # Sort alternatives by score
    ranked_alternatives.sort(key=lambda x: x["score"], reverse=True)

    probabilities = {
        "HQ Coy": 1.0 if top_coy == "HQ Coy" else 0.0,
        "Comn Coy": 1.0 if top_coy == "Comn Coy" else 0.0,
        "3 Coy": 1.0 if top_coy == "3 Coy" else 0.0
    }

    match_reasons = [
        f"Fresh Joinee – Rule-Based Specialty/Position Mapping (0 Previous Postings)",
        f"Trade '{clean_trade or 'N/A'}' & Specialty [{', '.join(active_specialties)}] mapped directly to {top_coy}",
        matched_reason,
        f"Recommended appointment '{top_pos}' resides in Section '{top_section}' under {top_coy}"
    ]

    shap_factors = {
        "positive": [
            f"Trade specialty [{', '.join(active_specialties)}] strongly indicates {top_coy}",
            f"Fresh joinee induction pipeline matches {top_coy} - {top_section} onboarding capacity"
        ],
        "negative": [
            "No previous unit posting history available (Rule-based evaluation applied)"
        ]
    }

    return {
        "recommended_company": top_coy,
        "db_company": to_db_company_name(top_coy),
        "confidence_score": "100.00%",
        "recommendation_percentage": 100.00,
        "confidence_type": "rule_based_fresh_joinee",
        "recommended_section": top_section,
        "recommended_position": top_pos,
        "position_confidence": "100.00%",
        "probabilities": probabilities,
        "match_reasons": match_reasons,
        "shap_explanation": shap_factors,
        "ranked_positions": ranked_alternatives[:5],
        "is_fresh_joinee": True,
        "method": "Fresh Joinee – Rule-Based Specialty/Position Mapping"
    }


# =============================================================================
# 5. CONDITIONAL POSITION RANKER (STAGE 2)
# =============================================================================

def rank_positions_for_predicted_company(
    company: str,
    trade: str,
    specialties: List[str],
    rank: str = "",
    duty_history: List[str] = None
) -> Tuple[str, str, float, List[Dict[str, Any]]]:
    """
    Stage 2: Evaluate and rank positions CONDITIONAL ONLY on the predicted company.
    Strictly forbids positions from any other company.
    Returns: (top_position, top_section, top_score, ranked_alternatives)
    """
    canonical_coy = normalize_company_name(company)
    valid_positions = get_positions_for_company(canonical_coy)
    
    if not valid_positions:
        return "GD", "GENERAL DUTY", 50.0, []

    spec_set = set(specialties or extract_specialties_from_trade_and_text(trade))
    trade_clean = (trade or "").upper()
    duty_text = " ".join(duty_history or []).upper()

    position_scores = []

    for pos in valid_positions:
        sec = get_section_for_position(canonical_coy, pos)
        base_score = 50.0

        weights = POSITION_SPECIALTY_WEIGHTS.get(pos, {})
        for spec, weight in weights.items():
            if spec in spec_set:
                base_score += weight * 35.0

        # Exact match bonus with trade name
        if pos.upper() in trade_clean or trade_clean in pos.upper():
            base_score += 25.0

        # Past duty match bonus
        if duty_text and (pos.upper() in duty_text or sec.upper() in duty_text):
            base_score += 15.0

        # Rank alignment
        rank_upper = (rank or "").upper()
        if "NCO" in pos.upper() and ("HAV" in rank_upper or "NK" in rank_upper):
            base_score += 5.0
        elif "CLERK" in pos.upper() and "CLK" in trade_clean:
            base_score += 20.0
        elif "JCO" in pos.upper() and ("SUB" in rank_upper or "JCO" in rank_upper):
            base_score += 15.0

        # Cap score between 50% and 99.0%
        final_score = min(max(base_score, 52.0), 98.5)
        position_scores.append({
            "position": pos,
            "section": sec,
            "score": round(final_score, 1),
            "confidence": f"{round(final_score, 1)}%"
        })

    # Sort descending by score
    position_scores.sort(key=lambda x: x["score"], reverse=True)

    top_item = position_scores[0]
    top_pos = top_item["position"]
    top_sec = top_item["section"]
    top_score = top_item["score"]

    alternatives = position_scores[1:]
    return top_pos, top_sec, top_score, alternatives
