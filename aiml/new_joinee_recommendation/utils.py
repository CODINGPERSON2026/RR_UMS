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

def parse_date_safe(val):
    """Safely parse various date formats or return None."""
    if val is None or pd_is_na(val):
        return None
    if isinstance(val, (datetime, date)):
        return val
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.fromisoformat(str(val).strip()).date()
        except Exception:
            return None

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
