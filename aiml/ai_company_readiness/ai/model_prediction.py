"""
Model Inference and Explainability Engine for AI Company Readiness.
Extracts model feature importances and formulates explainable contributing factors.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from ..feature_engineering import FEATURE_COLUMNS
from .model_utils import load_model_artifacts

# Human-readable factor descriptions
FEATURE_LABELS: Dict[str, str] = {
    "leave_rate": "Leave Outflow Rate",
    "detachment_rate": "External Detachment Rate",
    "td_rate": "Temporary Duty (TD) Rate",
    "course_away_rate": "Personnel Away on Military Courses",
    "availability_rate": "Ground Personnel Availability",
    "strength_ratio": "Authorized vs Actual Strength Ratio",
    "trade_fulfillment_ratio": "Technical Trade Compliance",
    "qualification_fulfillment_ratio": "Education & Qualification Compliance",
    "course_fulfillment_ratio": "Military Course Specialization Ratio",
    "shape1_ratio": "SHAPE-1 Medical Fitness Compliance",
    "lmc_ratio": "Low Medical Category (LMC) Ratio",
    "bpet_pass_ratio": "Battle Physical Efficiency Test (BPET) Pass Rate",
    "ppt_pass_ratio": "Physical Proficiency Test (PPT) Pass Rate",
    "upcoming_recat_ratio": "Upcoming Medical Recategorization Roster"
}


def explain_prediction(
    model: Any,
    scaler: Any,
    features_dict: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Computes top contributing factors for a prediction based on feature values
    and model weights/importances.
    """
    factors: List[Dict[str, Any]] = []
    vector = np.array([features_dict.get(c, 0.0) for c in FEATURE_COLUMNS], dtype=np.float32)

    # 1. Tree-based feature importance
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        # Combine importance with deviation from ideal (1.0 for positive ratios, 0.0 for negative rates)
        ranked_indices = np.argsort(importances)[::-1]
        
        for idx in ranked_indices[:5]:
            col = FEATURE_COLUMNS[idx]
            val = float(vector[idx])
            imp = float(importances[idx])
            label = FEATURE_LABELS.get(col, col.replace("_", " ").title())
            
            # Formulate explainable observation
            if "rate" in col or "ratio" in col:
                val_pct = f"{round(val * 100, 1)}%"
            else:
                val_pct = str(int(val))

            desc = f"{label} is at {val_pct} (model influence: {round(imp * 100, 1)}%)."
            factors.append({
                "feature": col,
                "label": label,
                "value": val_pct,
                "importance": round(imp, 4),
                "description": desc
            })

    # 2. Linear model coefficients
    elif hasattr(model, "coef_"):
        coefs = model.coef_[0]
        ranked_indices = np.argsort(np.abs(coefs))[::-1]
        for idx in ranked_indices[:5]:
            col = FEATURE_COLUMNS[idx]
            val = float(vector[idx])
            weight = float(coefs[idx])
            label = FEATURE_LABELS.get(col, col.replace("_", " ").title())
            
            val_pct = f"{round(val * 100, 1)}%" if ("rate" in col or "ratio" in col) else str(int(val))
            impact_dir = "Risk factor" if weight > 0 else "Protective factor"
            
            factors.append({
                "feature": col,
                "label": label,
                "value": val_pct,
                "importance": round(abs(weight), 4),
                "description": f"{label} ({val_pct}) acts as a key {impact_dir.lower()} in the model."
            })

    return factors
