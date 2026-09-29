"""
Utility functions for AI Company Readiness module.
Provides company normalization, scoring helpers, and status mappings.
"""

from typing import List, Dict, Any, Optional

# Supported canonical company names
SUPPORTED_COMPANIES = ["HQ COY", "COMN COY", "3 COY"]

# Canonical to DB-stored company name mapping
CANONICAL_TO_DB = {
    "HQ COY": "HQ company",
    "COMN COY": "COMN Company",
    "3 COY": "3 Company"
}

# DB company name to canonical mapping
DB_TO_CANONICAL = {
    "HQ company": "HQ COY",
    "HQ Company": "HQ COY",
    "hq company": "HQ COY",
    "HQ COY": "HQ COY",
    "hq coy": "HQ COY",
    "COMN Company": "COMN COY",
    "COMN company": "COMN COY",
    "comn company": "COMN COY",
    "COMN COY": "COMN COY",
    "comn coy": "COMN COY",
    "3 Company": "3 COY",
    "3 company": "3 COY",
    "3 COY": "3 COY",
    "3 coy": "3 COY"
}

# Display full names
DISPLAY_NAMES = {
    "HQ COY": "Headquarters Company (HQ COY)",
    "COMN COY": "Communication Company (COMN COY)",
    "3 COY": "3 Company (3 COY)"
}


def normalize_company_name(name: Optional[str]) -> Optional[str]:
    """
    Normalizes any company name variation to canonical form:
    'HQ COY', 'COMN COY', or '3 COY'.
    Returns None if the company is not recognized.
    """
    if not name:
        return None
    cleaned = name.strip()
    # Direct lookup
    if cleaned in DB_TO_CANONICAL:
        return DB_TO_CANONICAL[cleaned]
    
    cleaned_lower = cleaned.lower()
    for key, val in DB_TO_CANONICAL.items():
        if key.lower() == cleaned_lower:
            return val
            
    if "hq" in cleaned_lower:
        return "HQ COY"
    elif "comn" in cleaned_lower:
        return "COMN COY"
    elif "3" in cleaned_lower:
        return "3 COY"
        
    return None


def to_db_company_name(canonical_name: str) -> str:
    """Returns the primary string stored in personnel.company."""
    return CANONICAL_TO_DB.get(canonical_name, canonical_name)


def get_db_company_variants(canonical_name: str) -> List[str]:
    """Returns all plausible company name variants for SQL matching."""
    variants = [canonical_name]
    primary_db = CANONICAL_TO_DB.get(canonical_name)
    if primary_db and primary_db not in variants:
        variants.append(primary_db)
        
    if canonical_name == "HQ COY":
        variants.extend(["HQ company", "HQ Company", "hq company"])
    elif canonical_name == "COMN COY":
        variants.extend(["COMN Company", "COMN company", "comn company"])
    elif canonical_name == "3 COY":
        variants.extend(["3 Company", "3 company"])
        
    return list(dict.fromkeys(variants))


def safe_div(num: float, denom: float, default: float = 0.0) -> float:
    """Safely divides two numbers avoiding ZeroDivisionError."""
    if not denom or denom == 0:
        return default
    return num / denom


def calculate_percentage(current: float, target: float) -> float:
    """Returns capped percentage between 0 and 100 rounded to 1 decimal place."""
    if not target or target <= 0:
        return 100.0 if current > 0 else 0.0
    val = (current / target) * 100.0
    return round(min(100.0, max(0.0, val)), 1)


def get_readiness_status_badge(score: float) -> Dict[str, str]:
    """
    Returns badge class and label for a readiness score.
    85%+ : Optimal / High Readiness
    70-84% : Moderate / Warning
    <70% : Critical / Low Readiness
    """
    if score >= 85.0:
        return {"badge_class": "badge-optimal", "label": "Optimal Readiness", "level": "Optimal", "color": "#10b981"}
    elif score >= 70.0:
        return {"badge_class": "badge-moderate", "label": "Moderate Readiness", "level": "Moderate", "color": "#f59e0b"}
    else:
        return {"badge_class": "badge-critical", "label": "Critical Gaps", "level": "Critical", "color": "#ef4444"}
