"""
Model serialization, versioning, and metadata utility for AI Company Readiness.
"""

import os
import json
import joblib
from typing import Dict, Any, Optional
from datetime import datetime

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
MODEL_FILE = os.path.join(MODELS_DIR, "readiness_risk_model.joblib")
METADATA_FILE = os.path.join(MODELS_DIR, "model_metadata.json")


def save_model_artifacts(
    model: Any,
    scaler: Any,
    metadata: Dict[str, Any]
) -> None:
    """Saves model binary and metadata JSON to models directory."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    payload = {
        "model": model,
        "scaler": scaler,
        "saved_at": datetime.now().isoformat()
    }
    joblib.dump(payload, MODEL_FILE)
    
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def load_model_artifacts() -> Optional[Dict[str, Any]]:
    """Loads trained model, scaler, and metadata if available."""
    if not os.path.exists(MODEL_FILE) or not os.path.exists(METADATA_FILE):
        return None
    try:
        payload = joblib.load(MODEL_FILE)
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return {
            "model": payload.get("model"),
            "scaler": payload.get("scaler"),
            "metadata": metadata
        }
    except Exception as e:
        return None


def get_model_metadata() -> Optional[Dict[str, Any]]:
    """Reads model metadata without loading model binary."""
    if not os.path.exists(METADATA_FILE):
        return None
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
