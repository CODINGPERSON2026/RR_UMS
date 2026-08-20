import json
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from .config import (
    AUTO_RETRAIN_THRESHOLD_RECORDS,
    MODEL_METADATA_FILE,
    RETRAINING_LOG_FILE
)
from .data_loader import load_raw_data, normalize_company
from .train import train_pipeline
from .utils import get_logger, RETRAIN_LOCK

logger = get_logger("retrain")

def get_current_eligible_count() -> int:
    """Returns count of personnel in MySQL mapped to canonical target classes."""
    try:
        personnel_df, _ = load_raw_data()
        personnel_df["target_company"] = personnel_df["company"].apply(normalize_company)
        eligible = personnel_df[personnel_df["target_company"].notna()]
        return int(len(eligible))
    except Exception as e:
        logger.error(f"Error querying eligible record count: {e}")
        return 0

def check_retrain_status() -> Dict[str, Any]:
    """
    Checks if new database records have met or exceeded the 50-record retraining threshold.
    """
    current_count = get_current_eligible_count()
    last_count = 0
    last_trained_at = None

    if MODEL_METADATA_FILE.exists():
        try:
            with open(MODEL_METADATA_FILE, "r") as f:
                meta = json.load(f)
                last_count = meta.get("total_eligible_records", 0)
                last_trained_at = meta.get("last_trained_at")
        except Exception as e:
            logger.warning(f"Could not read metadata file: {e}")

    delta_records = max(0, current_count - last_count)
    should_retrain = delta_records >= AUTO_RETRAIN_THRESHOLD_RECORDS and current_count > 0

    return {
        "should_retrain": should_retrain,
        "current_eligible_records": current_count,
        "last_trained_records": last_count,
        "new_records_since_last_training": delta_records,
        "threshold": AUTO_RETRAIN_THRESHOLD_RECORDS,
        "progress_percentage": min(100.0, round((delta_records / AUTO_RETRAIN_THRESHOLD_RECORDS) * 100, 1)),
        "last_trained_at": last_trained_at
    }

def execute_retraining(force: bool = False) -> Dict[str, Any]:
    """
    Safely executes retraining under a mutex lock.
    Preserves the existing model if retraining encounters an unexpected exception.
    """
    if not RETRAIN_LOCK.acquire(blocking=False):
        return {
            "success": False,
            "message": "Retraining is already currently in progress in another thread.",
            "status": "in_progress"
        }

    try:
        status = check_retrain_status()
        if not force and not status["should_retrain"]:
            return {
                "success": False,
                "message": f"Retraining threshold not reached ({status['new_records_since_last_training']}/{AUTO_RETRAIN_THRESHOLD_RECORDS} new records).",
                "status": "threshold_not_met",
                "details": status
            }

        logger.info(f"Triggering retraining (Force={force}, New Records={status['new_records_since_last_training']})...")
        metadata = train_pipeline()
        
        return {
            "success": True,
            "message": "Retraining completed successfully.",
            "status": "completed",
            "selected_model": metadata.get("selected_model"),
            "accuracy": metadata.get("metrics", {}).get("accuracy"),
            "macro_f1": metadata.get("metrics", {}).get("macro_f1"),
            "total_records": metadata.get("total_eligible_records")
        }

    except Exception as e:
        logger.error(f"Retraining failed: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Retraining failed: {str(e)}. Previous model preserved.",
            "status": "error"
        }
    finally:
        RETRAIN_LOCK.release()
