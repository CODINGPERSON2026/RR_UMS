from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd
import json

from .config import (
    BEST_MODEL_FILE,
    BEST_MODEL_INFO_FILE,
    PREPROCESSOR_FILE,
    CANONICAL_COMPANIES
)
from .feature_engineering import build_features_for_personnel
from .preprocessing import CompanyPreprocessor
from .data_loader import load_single_personnel
from .utils import get_logger

logger = get_logger("predict")

class CompanyPredictor:
    """
    Inference engine that loads production model & preprocessor to generate
    ranked company assignment probabilities for any registered or newly registered soldier.
    """
    def __init__(self):
        self.model = None
        self.preprocessor: Optional[CompanyPreprocessor] = None
        self.model_info: Dict[str, Any] = {}
        self.is_ready = False
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads model and preprocessor if available."""
        try:
            if BEST_MODEL_FILE.exists() and PREPROCESSOR_FILE.exists():
                self.model = joblib.load(BEST_MODEL_FILE)
                self.preprocessor = CompanyPreprocessor().load()
                
                if BEST_MODEL_INFO_FILE.exists():
                    with open(BEST_MODEL_INFO_FILE, "r") as f:
                        self.model_info = json.load(f)
                else:
                    self.model_info = {"selected_model": "Production Model"}
                    
                self.is_ready = True
                logger.info(f"CompanyPredictor ready with model: {self.model_info.get('selected_model')}")
            else:
                self.is_ready = False
                logger.warning("Production model or preprocessor not found. Training required.")
        except Exception as e:
            self.is_ready = False
            logger.error(f"Error loading prediction artifacts: {e}")

    def reload(self):
        """Reloads artifacts after retraining."""
        self._load_artifacts()

    def predict_for_features(self, feat_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates ranked company probabilities for a given feature dictionary.
        """
        if not self.is_ready:
            self._load_artifacts()
            if not self.is_ready:
                return {
                    "success": False,
                    "error": "Model is not trained yet. Please train the initial model from the testing dashboard.",
                    "status": "not_trained"
                }

        df_feat = pd.DataFrame([feat_dict])
        X_trans = self.preprocessor.transform(df_feat)
        probs = self.model.predict_proba(X_trans)[0] # Shape: (3,)

        class_names = list(self.preprocessor.label_encoder.classes_)
        
        # Sort by probability descending
        prob_pairs = [(class_names[i], float(probs[i])) for i in range(len(class_names))]
        prob_pairs.sort(key=lambda x: x[1], reverse=True)

        ranked_list = []
        prob_map = {}
        for rank_idx, (cname, pval) in enumerate(prob_pairs, start=1):
            c_str = str(cname)
            ranked_list.append({
                "rank": rank_idx,
                "company": c_str,
                "probability": round(float(pval), 4),
                "percentage": round(float(pval) * 100, 2)
            })
            prob_map[c_str] = round(float(pval), 4)

        top_company = str(prob_pairs[0][0])
        top_prob = float(prob_pairs[0][1])

        # Confidence level
        if top_prob >= 0.60:
            confidence = "High"
        elif top_prob >= 0.45:
            confidence = "Moderate"
        else:
            confidence = "Low"

        return {
            "success": True,
            "recommended_company": top_company,
            "top_probability": round(top_prob, 4),
            "top_percentage": round(top_prob * 100, 2),
            "confidence": confidence,
            "ranked_recommendations": ranked_list,
            "probabilities": prob_map,
            "model_name": self.model_info.get("selected_model", "Random Forest / XGBoost"),
            "has_unit_history": bool(feat_dict.get("has_unit_history", 0))
        }

    def predict_for_personnel_id(self, personnel_id: int) -> Dict[str, Any]:
        """
        Fetches personnel and units_served from DB and generates prediction.
        """
        personnel_id = int(personnel_id)
        personnel_row, units_df = load_single_personnel(personnel_id)
        if not personnel_row:
            return {
                "success": False,
                "error": f"Personnel with ID {personnel_id} not found."
            }

        feat_dict = build_features_for_personnel(personnel_row, units_df)
        pred_res = self.predict_for_features(feat_dict)
        if pred_res.get("success"):
            pred_res["personnel_id"] = personnel_id
            pred_res["army_number"] = personnel_row.get("army_number", "")
            pred_res["name"] = personnel_row.get("name", "")
            pred_res["trade"] = feat_dict.get("trade", "UNKNOWN")
            pred_res["rank"] = feat_dict.get("rank", "UNKNOWN")
            pred_res["units_served_count"] = len(units_df) if units_df is not None else 0
            pred_res["previous_units"] = units_df["unit"].dropna().tolist() if units_df is not None and len(units_df) > 0 else []
            pred_res["previous_duties"] = units_df["duty_performed"].dropna().tolist() if units_df is not None and len(units_df) > 0 else []
        return pred_res
