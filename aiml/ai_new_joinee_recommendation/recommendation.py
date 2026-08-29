"""
Two-Stage AI Recommendation Engine for Unit 15 CESR
Stage 1: Predict & Rank Company (HQ Coy, Comn Coy, 3 Coy) with ML + SHAP Explainability.
Stage 2: Evaluate & Rank Positions conditional strictly within the predicted Company.
Also supports Fresh Joinee rule-based mapping and Unknown Trade fallback handling.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

# Ensure workspace root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aiml.ai_new_joinee_recommendation.position_mapping import (
    VALID_COMPANIES,
    VALID_DB_COMPANIES,
    normalize_company_name,
    to_db_company_name,
    to_display_company_name,
    extract_specialties_from_trade_and_text,
    get_fresh_joinee_recommendation,
    rank_positions_for_predicted_company,
    is_position_valid_for_company,
    get_section_for_position
)
from aiml.ai_new_joinee_recommendation.preprocessing import (
    extract_features_from_dict,
    calculate_service_years
)
from aiml.ai_new_joinee_recommendation.explainability import SHAPExplainerWrapper

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")

# In-memory model cache
_CACHED_CHAMPION_MODEL = None
_CACHED_FEATURE_NAMES = None
_CACHED_SHAP_WRAPPER = None
_CACHED_METADATA = None


def load_model_artifacts() -> bool:
    """Load model artifacts into memory cache."""
    global _CACHED_CHAMPION_MODEL, _CACHED_FEATURE_NAMES, _CACHED_SHAP_WRAPPER, _CACHED_METADATA
    try:
        model_path = os.path.join(MODEL_DIR, "champion_model.joblib")
        feat_path = os.path.join(MODEL_DIR, "feature_names.json")
        shap_path = os.path.join(MODEL_DIR, "shap_wrapper.joblib")
        meta_path = os.path.join(MODEL_DIR, "model_metadata.json")

        if not os.path.exists(model_path) or not os.path.exists(feat_path):
            return False

        _CACHED_CHAMPION_MODEL = joblib.load(model_path)
        with open(feat_path, "r") as f:
            _CACHED_FEATURE_NAMES = json.load(f)

        if os.path.exists(shap_path):
            _CACHED_SHAP_WRAPPER = joblib.load(shap_path)

        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                _CACHED_METADATA = json.load(f)

        return True
    except Exception as e:
        print(f"Error loading model artifacts: {e}")
        return False


def recommend_placement(
    trade: str,
    rank: str = "Signal Man",
    specialties: List[str] = None,
    date_of_enrollment: Any = None,
    prior_station: str = "",
    units_history: List[Dict[str, Any]] = None,
    is_fresh_joinee: bool = False,
    army_number: str = "",
    name: str = ""
) -> Dict[str, Any]:
    """
    Main recommendation entrypoint.
    Executes 2-Stage Recommendation Architecture with SHAP explainability.
    """
    clean_trade = (trade or "").strip().upper()
    active_specialties = specialties or extract_specialties_from_trade_and_text(trade)
    valid_units = [u for u in (units_history or []) if u.get("unit") or u.get("unit_name")]

    # 1. FRESH JOINEE FLOW (0 Previous Postings)
    if is_fresh_joinee or len(valid_units) == 0:
        return get_fresh_joinee_recommendation(
            trade=trade,
            specialties=active_specialties,
            rank=rank
        )

    # 2. NORMAL JOINEE FLOW (WITH POSTING HISTORY)
    # Ensure model is loaded
    global _CACHED_CHAMPION_MODEL
    if _CACHED_CHAMPION_MODEL is None:
        loaded = load_model_artifacts()
        if not loaded:
            # Fallback to rule-based recommendation if model is not trained yet
            res = get_fresh_joinee_recommendation(trade, active_specialties, rank)
            res["confidence_type"] = "rule_based_fallback"
            res["method"] = "Rule-based fallback"
            return res

    try:
        # Extract features for Stage 1
        feats_dict = extract_features_from_dict(
            trade=trade,
            rank=rank,
            specialties=active_specialties,
            date_of_enrollment=date_of_enrollment,
            units_history=valid_units,
            is_fresh=False
        )

        df_input = pd.DataFrame([feats_dict])
        if _CACHED_FEATURE_NAMES:
            for col in _CACHED_FEATURE_NAMES:
                if col not in df_input.columns:
                    df_input[col] = 0.0
            df_input = df_input[_CACHED_FEATURE_NAMES].fillna(0.0)

        # STAGE 1: Predict Company Probabilities
        if hasattr(_CACHED_CHAMPION_MODEL, "predict_proba"):
            raw_probs = _CACHED_CHAMPION_MODEL.predict_proba(df_input)[0]
            model_classes = list(getattr(_CACHED_CHAMPION_MODEL, "classes_", VALID_COMPANIES))
        else:
            pred_class = _CACHED_CHAMPION_MODEL.predict(df_input)[0]
            raw_probs = [0.8 if c == pred_class else 0.1 for c in VALID_COMPANIES]
            model_classes = VALID_COMPANIES

        # Normalize probability map
        prob_dict = {}
        for c in VALID_COMPANIES:
            if c in model_classes:
                idx = model_classes.index(c)
                prob_dict[c] = float(raw_probs[idx])
            else:
                prob_dict[c] = 0.0

        # Calibrate & identify top company
        sum_p = sum(prob_dict.values()) or 1.0
        for c in prob_dict:
            prob_dict[c] = round(prob_dict[c] / sum_p, 4)

        top_company = max(prob_dict, key=prob_dict.get)
        top_prob = prob_dict[top_company]
        top_pct = round(top_prob * 100.0, 2)
        confidence_score_str = f"{top_pct}%"

        # Explainability via SHAP
        if _CACHED_SHAP_WRAPPER:
            shap_result = _CACHED_SHAP_WRAPPER.explain_sample(df_input, top_company)
            shap_explanation = {
                "positive": shap_result.get("positive_forces", []),
                "negative": shap_result.get("negative_forces", [])
            }
            match_reasons = shap_result.get("match_reasons", [])
        else:
            shap_explanation = {
                "positive": [f"+ Trade specialty [{', '.join(active_specialties)}] strongly indicates {top_company}"],
                "negative": []
            }
            match_reasons = [f"Profile matches historical deployment patterns for {top_company}."]

        # Add posting history alignment context to reasons
        duty_list = [str(u.get("duty_performed") or u.get("duty") or "") for u in valid_units]
        duty_str = ", ".join([d for d in duty_list if d])
        if duty_str:
            match_reasons.append(f"Previous duty experience ({duty_str}) directly transfers to {top_company}.")
        else:
            match_reasons.append(f"Posting tenure across {len(valid_units)} unit(s) supports placement in {top_company}.")

        # STAGE 2: Conditional Position Recommendation inside top_company ONLY
        top_pos, top_sec, pos_score, alt_positions = rank_positions_for_predicted_company(
            company=top_company,
            trade=trade,
            specialties=active_specialties,
            rank=rank,
            duty_history=duty_list
        )

        match_reasons.append(f"Recommended appointment '{top_pos}' in Section '{top_sec}' within {top_company}.")

        return {
            "recommended_company": top_company,
            "db_company": to_db_company_name(top_company),
            "confidence_score": confidence_score_str,
            "recommendation_percentage": top_pct,
            "confidence_type": "ml",
            "model_version": (_CACHED_METADATA or {}).get("model_version", "v2.0-cesr"),
            "recommended_section": top_sec,
            "recommended_position": top_pos,
            "position_confidence": f"{pos_score}%",
            "probabilities": prob_dict,
            "match_reasons": match_reasons,
            "shap_explanation": shap_explanation,
            "ranked_positions": alt_positions[:5],
            "is_fresh_joinee": False,
            "method": "Supervised ML (Two-Stage Architecture)"
        }

    except Exception as e:
        print(f"Error in ML recommendation: {e}, falling back to rule-based engine.")
        # Fallback cleanly without crashing
        res = get_fresh_joinee_recommendation(trade, active_specialties, rank)
        res["confidence_type"] = "rule_based_fallback"
        res["method"] = "Rule-based fallback"
        res["match_reasons"].insert(0, "Rule-based fallback applied due to unknown profile or prediction fallback.")
        return res
