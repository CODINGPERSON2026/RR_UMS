import json
from typing import Dict, Any, Optional
from pathlib import Path

from .config import (
    METRICS_DIR,
    REPORTS_DIR,
    MODEL_METADATA_FILE,
    RETRAINING_LOG_FILE,
    ARTIFACTS_DIR
)
from .utils import get_logger

logger = get_logger("analytics")

def get_analytics_data() -> Dict[str, Any]:
    """
    Loads all model comparison, dataset profile, confusion matrix,
    feature importance, and retraining log artifacts for dashboard display.
    """
    analytics = {
        "status": "not_trained",
        "selected_model": "None",
        "metadata": {},
        "comparison": {},
        "retraining_log": []
    }

    # 1. Load Metadata
    if MODEL_METADATA_FILE.exists():
        try:
            with open(MODEL_METADATA_FILE, "r") as f:
                analytics["metadata"] = json.load(f)
                analytics["status"] = "ready"
                analytics["selected_model"] = analytics["metadata"].get("selected_model", "Random Forest")
        except Exception as e:
            logger.error(f"Error reading model metadata: {e}")

    # 2. Load Model Comparison
    comp_file = METRICS_DIR / "model_comparison.json"
    if comp_file.exists():
        try:
            with open(comp_file, "r") as f:
                analytics["comparison"] = json.load(f)
        except Exception as e:
            logger.error(f"Error reading model comparison: {e}")

    # 3. Load Retraining Log
    if RETRAINING_LOG_FILE.exists():
        try:
            with open(RETRAINING_LOG_FILE, "r") as f:
                analytics["retraining_log"] = json.load(f)
        except Exception as e:
            logger.error(f"Error reading retraining log: {e}")

    return analytics
