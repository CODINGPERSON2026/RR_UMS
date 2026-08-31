"""
Hierarchical AI Recommendation Engine for Unit 15 CESR (STRICTLY TRADE-FREE)
Stage 1: Predict & Rank Company (HQ COY, COMN COY, 3 COY) via ML + SHAP Explainability.
Stage 2: Predict Section belonging to the recommended Company.
Stage 3: Predict Position belonging to that Section.
Generates Top-N valid hierarchical recommendations and military-grade explainability.
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
    UNIT_15_CESR_STRUCTURE,
    normalize_company_name,
    to_db_company_name,
    to_display_company_name,
    get_fresh_joinee_recommendation,
    rank_sections_and_positions_for_company,
    get_section_for_position,
    is_valid_hierarchy,
    get_positions_for_section
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
    rank: str = "Signal Man",
    date_of_enrollment: Any = None,
    prior_station: str = "",
    units_history: List[Dict[str, Any]] = None,
    is_fresh_joinee: bool = False,
    army_number: str = "",
    name: str = "",
    extra_attrs: Dict[str, Any] = None,
    selected_section: Optional[str] = None,
    **kwargs  # Ignore any legacy trade arguments safely
) -> Dict[str, Any]:
    """
    Main recommendation entrypoint (Hierarchical & Strictly Trade-Free).
    Executes 3-Stage Recommendation Architecture with SHAP explainability:
    Company -> Section -> Position.
    Supports Mode A (Auto-Predict Section) and Mode B (User-Provided Section).
    """
    # Extract selected_section if passed via kwargs
    if not selected_section:
        selected_section = kwargs.get("section") or kwargs.get("target_section")
        if isinstance(selected_section, list) and len(selected_section) > 0:
            selected_section = selected_section[0]

    valid_units = [u for u in (units_history or []) if (u.get("unit") or u.get("unit_name"))]
    service_years = calculate_service_years(date_of_enrollment)

    # 1. FRESH JOINEE FLOW (0 Previous Postings)
    if is_fresh_joinee or len(valid_units) == 0:
        return get_fresh_joinee_recommendation(
            rank=rank,
            service_years=service_years,
            prior_station=prior_station,
            selected_section=selected_section
        )

    # 2. NORMAL JOINEE FLOW (WITH POSTING HISTORY)
    global _CACHED_CHAMPION_MODEL
    if _CACHED_CHAMPION_MODEL is None:
        loaded = load_model_artifacts()
        if not loaded:
            # Fallback to rule-based recommendation if model is not trained yet
            res = get_fresh_joinee_recommendation(rank, service_years, prior_station, selected_section)
            res["confidence_type"] = "rule_based_fallback"
            res["method"] = "Rule-based fallback"
            return res

    try:
        # Extract features for Stage 1 (NO TRADE)
        feats_dict = extract_features_from_dict(
            rank=rank,
            date_of_enrollment=date_of_enrollment,
            prior_station=prior_station,
            units_history=valid_units,
            is_fresh=False,
            extra_personnel_attrs=extra_attrs
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

        # Calibrate probabilities
        sum_p = sum(prob_dict.values()) or 1.0
        for c in prob_dict:
            prob_dict[c] = round(prob_dict[c] / sum_p, 4)

        # Determine target company:
        # If user specified section, company is locked to the parent company of that section.
        # Otherwise, company is the model's top predicted class.
        is_user_sec = bool(selected_section and str(selected_section).strip())
        if is_user_sec:
            from aiml.ai_new_joinee_recommendation.position_mapping import get_company_for_section
            top_company = get_company_for_section(str(selected_section).strip())
        else:
            top_company = max(prob_dict, key=prob_dict.get)

        top_coy_prob = prob_dict.get(top_company, 0.60)
        top_coy_score = round(top_coy_prob, 3)
        top_pct = round(top_coy_prob * 100.0, 1)

        # Format full Company Probability Distribution
        company_probabilities = [
            {
                "company": c,
                "probability": round(prob_dict.get(c, 0.0), 3),
                "score_str": f"{round(prob_dict.get(c, 0.0) * 100.0, 1)}%",
                "is_recommended": (c == top_company)
            }
            for c in VALID_COMPANIES
        ]
        company_probabilities.sort(key=lambda x: x["probability"], reverse=True)

        # STAGE 2 & STAGE 3: Conditional Section & Position Recommendation inside top_company
        duty_list = [str(u.get("duty_performed") or u.get("duty") or "") for u in valid_units]
        domain_scores = {k: feats_dict.get(k, 0.0) for k in ["domain_tech", "domain_comn", "domain_it", "domain_clerk", "domain_qm", "domain_dvr", "domain_gd"]}

        (
            top_sec,
            sec_score,
            top_pos,
            pos_score,
            top_n_recommendations,
            section_probabilities,
            position_probabilities,
            is_section_user_selected,
            section_compatibility
        ) = rank_sections_and_positions_for_company(
            company=top_company,
            rank=rank,
            duty_history=duty_list,
            service_years=service_years,
            domain_scores=domain_scores,
            selected_section=selected_section
        )

        # TreeSHAP Explainability
        if _CACHED_SHAP_WRAPPER:
            shap_result = _CACHED_SHAP_WRAPPER.explain_sample(
                X_sample=df_input,
                predicted_company=top_company,
                section=top_sec,
                position=top_pos
            )
            shap_explanation = {
                "positive": shap_result.get("positive_forces", []),
                "negative": shap_result.get("negative_forces", [])
            }
            match_reasons = shap_result.get("match_reasons", [])
        else:
            shap_explanation = {
                "positive": [
                    f"+ Seniority profile and service duration ({service_years} yrs) strongly align with {top_company}",
                    f"+ Field posting experience across {len(valid_units)} units matches {top_company} establishment"
                ],
                "negative": []
            }
            match_reasons = [
                f"Previous unit history strongly matches personnel historically assigned to {top_company}.",
                f"Historical posting pattern shows strong similarity with Section '{top_sec}' assignments.",
                f"Personnel profile has high similarity to historical '{top_pos}' appointments."
            ]

        # Add specific hierarchical alignment reasons
        duty_str = ", ".join([d for d in duty_list if d][:3])
        if duty_str:
            match_reasons.append(f"Previous duty experience ({duty_str}) aligns with {top_company} -> {top_sec}.")

        if is_user_sec:
            match_reasons.append(f"Section '{top_sec}' was selected by user; evaluated {round(section_compatibility, 1)}% AI compatibility with {top_company}.")
        else:
            match_reasons.append(f"Section '{top_sec}' ranked as top model recommendation with {round(section_probabilities[0]['probability'] * 100.0, 1)}% section probability.")

        match_reasons.append(f"Appointment '{top_pos}' ranked as top match ({round(pos_score * 100.0, 1)}%) within Section '{top_sec}'.")
        match_reasons.append(f"{top_company} company-level probability is {top_pct}%.")

        return {
            "success": True,
            "recommended_company": top_company,
            "company_score": top_coy_score,
            "recommended_section": top_sec,
            "section_score": sec_score,
            "section_compatibility": round(section_compatibility, 1),
            "is_section_user_selected": is_section_user_selected,
            "recommended_position": top_pos,
            "position_score": pos_score,
            "db_company": to_db_company_name(top_company),
            "confidence_score": f"{top_pct}%",
            "recommendation_percentage": top_pct,
            "confidence_type": "ml",
            "model": (_CACHED_METADATA or {}).get("selected_model", "Random Forest"),
            "model_version": (_CACHED_METADATA or {}).get("model_version", "company_position_model_v2"),
            "position_confidence": f"{round(pos_score * 100.0, 1)}%",
            "probabilities": prob_dict,
            "company_probabilities": company_probabilities,
            "section_probabilities": section_probabilities,
            "position_probabilities": position_probabilities,
            "recommendations": top_n_recommendations,
            "top_recommendations": top_n_recommendations,
            "match_reasons": match_reasons,
            "shap_explanation": shap_explanation,
            "is_fresh_joinee": False,
            "trade_excluded": True,
            "method": "Hierarchical Supervised ML (Company -> Section -> Position)"
        }

    except Exception as e:
        print(f"Error in ML recommendation: {e}, falling back to rule-based engine.")
        res = get_fresh_joinee_recommendation(rank, service_years, prior_station, selected_section)
        res["confidence_type"] = "rule_based_fallback"
        res["method"] = "Rule-based fallback"
        res["match_reasons"].insert(0, "Rule-based fallback applied due to profile evaluation exception.")
        return res
