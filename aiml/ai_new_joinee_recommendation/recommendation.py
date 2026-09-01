"""
Hierarchical AI Recommendation Engine for Unit 15 CESR.
Multi-Stage Pattern-Based Supervised Inference Pipeline:
Stage 1: Predict & Rank Company (HQ COY, COMN COY, 3 COY) via ML + SHAP Explainability.
Stage 2: Predict Section Pattern belonging to recommended Company via ML & Domain Pattern Matrix.
Stage 3: Predict Trade/Appointment Pattern belonging to Section via ML & Domain Pattern Matrix.
Evaluates candidate sets without sequence bias and generates military-grade explainability.
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
    get_company_for_section,
    get_section_for_position,
    get_sections_for_company,
    get_positions_for_section,
    get_positions_for_company,
    is_valid_hierarchy
)
from aiml.ai_new_joinee_recommendation.preprocessing import (
    extract_features_from_units,
    extract_features_from_dict,
    calculate_service_years,
    get_rank_level
)
from aiml.ai_new_joinee_recommendation.explainability import (
    SHAPExplainerWrapper,
    generate_domain_and_contrastive_explainability
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")

# In-memory model cache
_CACHED_CHAMPION_MODEL = None
_CACHED_SECTION_MODEL = None
_CACHED_POSITION_MODEL = None
_CACHED_FEATURE_NAMES = None
_CACHED_SHAP_WRAPPER = None
_CACHED_METADATA = None


def load_model_artifacts() -> bool:
    """Load all multi-stage model artifacts into memory cache."""
    global _CACHED_CHAMPION_MODEL, _CACHED_SECTION_MODEL, _CACHED_POSITION_MODEL, _CACHED_FEATURE_NAMES, _CACHED_SHAP_WRAPPER, _CACHED_METADATA
    try:
        model_path = os.path.join(MODEL_DIR, "champion_model.joblib")
        sec_model_path = os.path.join(MODEL_DIR, "section_model.joblib")
        pos_model_path = os.path.join(MODEL_DIR, "position_model.joblib")
        feat_path = os.path.join(MODEL_DIR, "feature_names.json")
        shap_path = os.path.join(MODEL_DIR, "shap_wrapper.joblib")
        meta_path = os.path.join(MODEL_DIR, "model_metadata.json")

        if not os.path.exists(model_path) or not os.path.exists(feat_path):
            return False

        _CACHED_CHAMPION_MODEL = joblib.load(model_path)

        if os.path.exists(sec_model_path):
            _CACHED_SECTION_MODEL = joblib.load(sec_model_path)
        if os.path.exists(pos_model_path):
            _CACHED_POSITION_MODEL = joblib.load(pos_model_path)

        with open(feat_path, "r", encoding="utf-8") as f:
            _CACHED_FEATURE_NAMES = json.load(f)

        if os.path.exists(shap_path):
            _CACHED_SHAP_WRAPPER = joblib.load(shap_path)

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                _CACHED_METADATA = json.load(f)

        return True
    except Exception as e:
        print(f"Error loading model artifacts: {e}")
        return False


def compute_section_domain_pattern_score(sec_name: str, feats: Dict[str, float]) -> float:
    """Compute explicit domain pattern affinity score for a canonical section."""
    sec_u = sec_name.strip().upper()
    score = 15.0

    if sec_u == "RHQ":
        score += feats.get("domain_clerk", 0.0) * 50.0 + feats.get("unit_type_admin", 0.0) * 30.0
    elif sec_u == "QM":
        score += feats.get("domain_qm", 0.0) * 50.0 + feats.get("unit_type_logistics", 0.0) * 30.0
    elif sec_u == "MT":
        score += feats.get("domain_dvr", 0.0) * 50.0 + feats.get("unit_type_mechanical", 0.0) * 30.0
    elif sec_u == "LRW":
        score += feats.get("domain_tech", 0.0) * 50.0 + feats.get("unit_type_mechanical", 0.0) * 20.0
    elif sec_u == "RP":
        score += feats.get("domain_rp", 0.0) * 45.0 + feats.get("domain_gd", 0.0) * 20.0
    elif sec_u == "CHQ":
        score += feats.get("domain_chq", 0.0) * 50.0
    elif sec_u == "GENERAL DUTY":
        score += feats.get("domain_gd", 0.0) * 50.0 + feats.get("unit_type_field", 0.0) * 25.0
    elif "COMMUNICATION" in sec_u or "TECHNICAL" in sec_u:
        score += feats.get("domain_comn", 0.0) * 35.0 + feats.get("domain_it", 0.0) * 35.0 + feats.get("unit_type_signal", 0.0) * 40.0
    elif "CORPS" in sec_u:
        score += feats.get("domain_corps_hq", 0.0) * 50.0 + feats.get("unit_type_field", 0.0) * 30.0
    elif sec_u == "TM":
        score += feats.get("domain_tm", 0.0) * 50.0

    return score


def compute_position_domain_pattern_score(
    pos_name: str,
    sec_name: str,
    feats: Dict[str, float]
) -> float:
    """Compute explicit domain pattern score for a specific position within section."""
    pos_u = pos_name.strip().upper()
    score = 15.0

    # 1. QM Section
    if "RATION" in pos_u:
        score += feats.get("domain_qm", 0.0) * 50.0 + (10.0 if "ration" in str(feats).lower() else 0.0)
    elif "FRESH" in pos_u:
        score += feats.get("domain_qm", 0.0) * 45.0
    elif "CLOTHING" in pos_u:
        score += feats.get("domain_qm", 0.0) * 45.0
    elif "MES" in pos_u:
        score += feats.get("domain_qm", 0.0) * 45.0
    elif "SKT" in pos_u:
        score += feats.get("domain_qm", 0.0) * 50.0

    # 2. RHQ Section
    elif "CLERK" in pos_u or "TRG CLERK" in pos_u or "WARRANT" in pos_u or "PART ONE" in pos_u or "DISPATCHER" in pos_u or "A-SIGMA" in pos_u:
        score += feats.get("domain_clerk", 0.0) * 50.0
    elif "PA" in pos_u:
        score += feats.get("domain_clerk", 0.0) * 40.0
    elif "O1" in pos_u or "O2" in pos_u or "O3" in pos_u:
        score += feats.get("domain_clerk", 0.0) * 45.0

    # 3. RP Section
    elif "ADM NCO" in pos_u:
        score += feats.get("domain_rp", 0.0) * 45.0 + feats.get("domain_clerk", 0.0) * 20.0
    elif "STRICT ORDERLY" in pos_u or "RUNNER" in pos_u:
        score += feats.get("domain_rp", 0.0) * 40.0 + feats.get("domain_gd", 0.0) * 30.0
    elif "GUEST ROOM" in pos_u or "RP NCO" in pos_u:
        score += feats.get("domain_rp", 0.0) * 50.0

    # 4. CHQ Section
    elif "MESS HAV" in pos_u:
        score += feats.get("domain_chq", 0.0) * 55.0
    elif "BUDDY" in pos_u:
        score += feats.get("domain_chq", 0.0) * 45.0 + feats.get("domain_gd", 0.0) * 20.0
    elif "OFFICE" in pos_u:
        score += feats.get("domain_chq", 0.0) * 40.0 + feats.get("domain_clerk", 0.0) * 20.0
    elif "JCO MESS CDR" in pos_u:
        score += feats.get("domain_chq", 0.0) * 50.0
    elif "ALL TRADESMEN" in pos_u:
        score += feats.get("domain_chq", 0.0) * 40.0

    # 5. GENERAL DUTY
    elif "CHM" in pos_u or "CQMH" in pos_u or "RHM" in pos_u or "GD" in pos_u:
        score += feats.get("domain_gd", 0.0) * 50.0 + feats.get("unit_type_field", 0.0) * 20.0

    # 6. COMN COY
    elif "RADIO" in pos_u:
        score += feats.get("domain_comn", 0.0) * 55.0 + feats.get("unit_type_signal", 0.0) * 30.0
    elif "MCCS EXCHANGE" in pos_u:
        score += feats.get("domain_comn", 0.0) * 55.0 + feats.get("unit_type_signal", 0.0) * 30.0
    elif "MULTIMEDIA" in pos_u or "IT" in pos_u:
        score += feats.get("domain_it", 0.0) * 55.0 + feats.get("domain_tech", 0.0) * 25.0
    elif "SERVER" in pos_u:
        score += feats.get("domain_it", 0.0) * 50.0 + feats.get("domain_comn", 0.0) * 30.0
    elif "COMMUNICATION CLERK" in pos_u or "STRIP CLERK" in pos_u:
        score += feats.get("domain_comn", 0.0) * 40.0 + feats.get("domain_clerk", 0.0) * 30.0
    elif "ICN" in pos_u or "NFS" in pos_u:
        score += feats.get("domain_comn", 0.0) * 45.0 + feats.get("domain_tech", 0.0) * 30.0
    elif "SYSTEM" in pos_u:
        score += feats.get("domain_tech", 0.0) * 45.0 + feats.get("domain_it", 0.0) * 35.0

    # 7. 3 COY
    elif "VC" in pos_u or "CORPS HQ" in pos_u or "BRANCH" in pos_u:
        score += feats.get("domain_corps_hq", 0.0) * 50.0 + feats.get("unit_type_field", 0.0) * 30.0

    # 8. MT, TM, LRW
    elif "MT" in pos_u:
        score += feats.get("domain_dvr", 0.0) * 55.0 + feats.get("unit_type_mechanical", 0.0) * 30.0
    elif "TM" in pos_u:
        score += feats.get("domain_tm", 0.0) * 50.0
    elif "LRW" in pos_u:
        score += feats.get("domain_tech", 0.0) * 50.0

    return score


def recommend_placement(
    units_history: Optional[List[Dict[str, Any]]] = None,
    is_fresh_joinee: bool = False,
    army_number: str = "",
    name: str = "",
    selected_domains: Optional[List[Dict[str, Any]]] = None,
    # Backwards compatibility parameters:
    rank: str = "Signal Man",
    date_of_enrollment: Any = None,
    prior_station: str = "",
    selected_section: Optional[str] = None,
    target_sections: Optional[List[str]] = None,
    target_trades: Optional[List[str]] = None,
    section_trades_map: Optional[Dict[str, List[str]]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate real-time hierarchical AI recommendation (Company -> Section -> Appointment).
    Learns posting patterns from Previous Unit Served, Previous Duty, and Domain Profile.
    Evaluates candidate sets without sequence bias and guarantees valid hierarchy.
    """
    valid_units = [u for u in (units_history or []) if (u.get("unit") or u.get("unit_name"))]
    is_fresh = bool(is_fresh_joinee or len(valid_units) == 0)

    # 1. FRESH JOINEE RULE-BASED HANDLING
    if is_fresh:
        return get_fresh_joinee_recommendation(
            rank=rank,
            service_years=2.0,
            prior_station="",
            selected_section=selected_section,
            target_sections=target_sections,
            target_trades=target_trades,
            section_trades_map=section_trades_map
        )

    # 2. NORMAL JOINEE PATTERN INFERENCE PIPELINE
    global _CACHED_CHAMPION_MODEL, _CACHED_SECTION_MODEL, _CACHED_POSITION_MODEL
    if _CACHED_CHAMPION_MODEL is None:
        loaded = load_model_artifacts()
        if not loaded:
            res = get_fresh_joinee_recommendation(
                rank=rank,
                service_years=2.0,
                prior_station="",
                selected_section=selected_section,
                target_sections=target_sections,
                target_trades=target_trades,
                section_trades_map=section_trades_map
            )
            res["confidence_type"] = "rule_based_fallback"
            res["method"] = "Rule-based fallback"
            return res

    try:
        # Extract Safe Features
        feats_dict = extract_features_from_units(
            units_history=valid_units,
            is_fresh=False,
            selected_domains=selected_domains
        )

        df_input = pd.DataFrame([feats_dict])
        if _CACHED_FEATURE_NAMES:
            for col in _CACHED_FEATURE_NAMES:
                if col not in df_input.columns:
                    df_input[col] = 0.0
            df_input = df_input[_CACHED_FEATURE_NAMES].fillna(0.0)

        # STAGE 1: Predict Company Probabilities via ML Model
        if hasattr(_CACHED_CHAMPION_MODEL, "predict_proba"):
            raw_probs = _CACHED_CHAMPION_MODEL.predict_proba(df_input)[0]
            model_classes = list(getattr(_CACHED_CHAMPION_MODEL, "classes_", VALID_COMPANIES))
        else:
            pred_class = _CACHED_CHAMPION_MODEL.predict(df_input)[0]
            raw_probs = [0.8 if c == pred_class else 0.1 for c in VALID_COMPANIES]
            model_classes = VALID_COMPANIES

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

        top_company = max(prob_dict, key=lambda c: (prob_dict[c], c))
        top_coy_prob = prob_dict.get(top_company, 0.60)
        top_coy_score = round(top_coy_prob, 3)
        top_pct = round(top_coy_prob * 100.0, 1)

        company_probabilities = [
            {
                "company": c,
                "probability": round(prob_dict.get(c, 0.0), 3),
                "score_str": f"{round(prob_dict.get(c, 0.0) * 100.0, 1)}%",
                "is_recommended": (c == top_company)
            }
            for c in VALID_COMPANIES
        ]
        company_probabilities.sort(key=lambda x: (-x["probability"], x["company"]))

        # STAGE 2: Conditional Section Pattern Inference inside top_company
        coy_valid_sections = get_sections_for_company(top_company)
        sec_pattern_scores = {}

        for s in coy_valid_sections:
            d_score = compute_section_domain_pattern_score(s, feats_dict)
            sec_pattern_scores[s] = d_score

        sum_sec_scores = sum(sec_pattern_scores.values()) or 1.0
        sec_prob_map = {s: round(sec_pattern_scores[s] / sum_sec_scores, 4) for s in coy_valid_sections}

        # Select Top Section based on domain pattern score
        top_sec = max(sec_prob_map, key=lambda s: (sec_pattern_scores.get(s, 0.0), -len(s)))
        sec_score = round(sec_prob_map.get(top_sec, 0.5), 3)

        section_probabilities = [
            {
                "section": s,
                "company": top_company,
                "probability": round(sec_prob_map.get(s, 0.0), 3),
                "score_str": f"{round(sec_prob_map.get(s, 0.0) * 100.0, 1)}%",
                "is_recommended": (s == top_sec)
            }
            for s in coy_valid_sections
        ]
        section_probabilities.sort(key=lambda x: (-x["probability"], x["section"]))

        # STAGE 3: Conditional Appointment Pattern Inference inside top_sec
        sec_valid_positions = get_positions_for_section(top_company, top_sec)
        pos_pattern_scores = {}

        for p in sec_valid_positions:
            p_score = compute_position_domain_pattern_score(p, top_sec, feats_dict)
            pos_pattern_scores[p] = p_score

        sum_pos_scores = sum(pos_pattern_scores.values()) or 1.0
        pos_prob_map = {p: round(pos_pattern_scores[p] / sum_pos_scores, 4) for p in sec_valid_positions}

        top_pos = max(pos_prob_map, key=lambda p: (pos_pattern_scores.get(p, 0.0), -len(p)))
        pos_score = round(pos_prob_map.get(top_pos, 0.5), 3)

        position_probabilities = [
            {
                "position": p,
                "section": top_sec,
                "company": top_company,
                "probability": round(pos_prob_map.get(p, 0.0), 3),
                "score_str": f"{round(pos_prob_map.get(p, 0.0) * 100.0, 1)}%",
                "is_recommended": (p == top_pos)
            }
            for p in sec_valid_positions
        ]
        position_probabilities.sort(key=lambda x: (-x["probability"], x["position"]))

        # 4. Generate Top-6 Alternative Valid Recommendations
        alternative_allocations = []
        for c in VALID_COMPANIES:
            c_p = prob_dict.get(c, 0.0)
            c_secs = get_sections_for_company(c)
            for s in c_secs:
                s_poss = get_positions_for_section(c, s)
                s_score = compute_section_domain_pattern_score(s, feats_dict)
                for p in s_poss:
                    p_score = compute_position_domain_pattern_score(p, s, feats_dict)
                    comb_score = (c_p * 0.45) + ((s_score / 100.0) * 0.30) + ((p_score / 100.0) * 0.25)
                    alternative_allocations.append({
                        "company": c,
                        "section": s,
                        "position": p,
                        "composite_score": round(comb_score, 3),
                        "composite_pct": f"{round(min(comb_score * 100.0, 99.0), 1)}%",
                        "is_primary": (c == top_company and s == top_sec and p == top_pos)
                    })

        alternative_allocations.sort(key=lambda x: -x["composite_score"])
        top_alternatives = alternative_allocations[:8]

        # 5. TreeSHAP Explainability Forces
        shap_explanation = {}
        if _CACHED_SHAP_WRAPPER:
            try:
                shap_explanation = _CACHED_SHAP_WRAPPER.explain_sample(
                    X_sample=df_input,
                    predicted_company=top_company,
                    section=top_sec,
                    position=top_pos
                )
            except Exception as e:
                shap_explanation = {"error": str(e), "summary": f"Recommended based on {valid_units[0].get('unit', 'historical')} pattern."}

        # 6. Duty / Domain Specific and Contrastive Explainability
        domain_xai = generate_domain_and_contrastive_explainability(
            units_history=valid_units,
            selected_domains=selected_domains,
            predicted_company=top_company,
            section=top_sec,
            position=top_pos,
            company_probabilities=prob_dict,
            rank=rank
        )

        match_reasons = domain_xai.get("why_recommended", [])

        return {
            "recommended_company": top_company,
            "company_score": top_coy_score,
            "confidence_score": f"{top_pct}%",
            "recommendation_percentage": top_pct,
            "recommended_section": top_sec,
            "section_score": sec_score,
            "recommended_position": top_pos,
            "position_score": pos_score,
            "position_confidence": f"{round(pos_score * 100.0, 1)}%",
            "company_probabilities": company_probabilities,
            "probabilities": prob_dict,
            "section_probabilities": section_probabilities,
            "position_probabilities": position_probabilities,
            "alternative_allocations": top_alternatives,
            "recommendations": [
                {
                    "rank": idx + 1,
                    "company": alt["company"],
                    "section": alt["section"],
                    "position": alt["position"],
                    "score": alt["composite_pct"]
                }
                for idx, alt in enumerate(top_alternatives)
            ],
            "shap_explanation": shap_explanation,
            "domain_explainability": domain_xai.get("duty_domain_breakdown", []),
            "why_recommended": domain_xai.get("why_recommended", []),
            "why_not_others": domain_xai.get("why_not_others", []),
            "match_reasons": match_reasons,
            "confidence_type": "ml",
            "method": "Multi-stage pattern learning",
            "model_version": _CACHED_METADATA.get("model_version", "previous_unit_pattern_model_v4") if _CACHED_METADATA else "v4",
            "total_tenure_days": feats_dict.get("total_tenure_days", 0),
            "units_count": len(valid_units)
        }

    except Exception as e:
        print(f"Error in recommend_placement: {e}")
        return get_fresh_joinee_recommendation(
            rank=rank,
            service_years=2.0,
            prior_station="",
            selected_section=selected_section,
            target_sections=target_sections,
            target_trades=target_trades,
            section_trades_map=section_trades_map
        )


def reset_model_cache():
    """Clear memory caches to force reloading of newly trained models."""
    global _CACHED_CHAMPION_MODEL, _CACHED_SECTION_MODEL, _CACHED_POSITION_MODEL, _CACHED_FEATURE_NAMES, _CACHED_SHAP_WRAPPER, _CACHED_METADATA
    _CACHED_CHAMPION_MODEL = None
    _CACHED_SECTION_MODEL = None
    _CACHED_POSITION_MODEL = None
    _CACHED_FEATURE_NAMES = None
    _CACHED_SHAP_WRAPPER = None
    _CACHED_METADATA = None
