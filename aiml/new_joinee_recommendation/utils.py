import json
import logging
import threading
from datetime import datetime, date
from decimal import Decimal
import numpy as np

# Global thread lock for auto-retraining synchronization
RETRAIN_LOCK = threading.Lock()

def get_logger(name: str) -> logging.Logger:
    """Configures and returns a logger for the recommendation system."""
    logger = logging.getLogger(f"aiml.new_joinee_recommendation.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [AI-Company-Rec.%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

class CustomJSONEncoder(json.JSONEncoder):
    """JSON Encoder that handles dates, decimals, numpy types, and NaN/Infs safely."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def parse_date_safe(val, allow_future: bool = False, max_future_cutoff: date = None) -> date:
    """
    Safely parse various date formats or return None.
    If allow_future is False, dates after today (or max_future_cutoff) are clamped/ignored safely.
    """
    if val is None or pd_is_na(val):
        return None
    
    parsed = None
    if isinstance(val, datetime):
        parsed = val.date()
    elif isinstance(val, date):
        parsed = val
    else:
        s = str(val).strip()
        # Try multiple formats
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(s, fmt).date()
                break
            except Exception:
                pass
        if parsed is None:
            try:
                parsed = datetime.fromisoformat(s).date()
            except Exception:
                parsed = None

    if parsed is not None and not allow_future:
        cutoff = max_future_cutoff or date.today()
        if parsed > cutoff:
            # Clamping future dates to cutoff to prevent negative service years or invalid model calculations
            parsed = cutoff

    return parsed

def sanitize_text(val, default: str = "UNKNOWN") -> str:
    """Sanitizes text inputs, stripping whitespace and standardizing empty/null."""
    if val is None or pd_is_na(val):
        return default
    s = str(val).strip()
    if s.upper() in ["", "NONE", "NAN", "NULL", "NAT", "UNDEFINED", "UNKNOWN"]:
        return default
    return s

def pd_is_na(val) -> bool:
    """Helper to detect NA/None/Empty string."""
    if val is None:
        return True
    if isinstance(val, str) and val.strip().lower() in ["", "none", "nan", "null", "nat"]:
        return True
    try:
        import pandas as pd
        return pd.isna(val)
    except Exception:
        return False

