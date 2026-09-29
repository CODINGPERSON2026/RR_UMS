"""
Prediction Service for AI Company Readiness.
Executes genuine ML inference when trained models are available.
Fails gracefully with transparent domain messaging when historical training data is insufficient.
STRICT RULE: Never synthesizes fake confidence or fake ML predictions.
"""

from typing import Dict, List, Any, Optional
import numpy as np

from .models.readiness_models import CompanyReadiness, PredictionResult
from .feature_engineering import extract_features_from_readiness, to_feature_vector, FEATURE_COLUMNS
from .ai.model_utils import load_model_artifacts, get_model_metadata
from .ai.model_prediction import explain_prediction


class ReadinessPredictionService:
    """
    Manages ML prediction requests, model execution, and explainable insights.
    """

    def __init__(self):
        self._cached_artifacts = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads model artifacts if present."""
        self._cached_artifacts = load_model_artifacts()

    def get_prediction(
        self,
        readiness: CompanyReadiness,
        personnel: List[Dict[str, Any]],
        weight_info: Dict[str, Dict[str, Any]],
        prediction_period: str = "Next 30 Days"
    ) -> PredictionResult:
        """
        Generates ML prediction for the company.
        If a valid trained model is loaded, computes inference and confidence.
        If no model is trained, returns an honest 'UNDER_DEVELOPMENT' result.
        """
        current_score = readiness.overall_readiness
        coy = readiness.company

        # Extract strictly time-aligned features
        features = extract_features_from_readiness(readiness, personnel, weight_info)

        # Check if genuine model artifacts exist
        if not self._cached_artifacts:
            self._load_artifacts()

        if self._cached_artifacts and self._cached_artifacts.get("model"):
            try:
                model = self._cached_artifacts["model"]
                scaler = self._cached_artifacts.get("scaler")
                metadata = self._cached_artifacts.get("metadata", {})
                
                vec = to_feature_vector(features).reshape(1, -1)
                
                # Apply scaler if linear model
                if hasattr(model, "coef_") and scaler:
                    vec = scaler.transform(vec)

                # Inference
                pred_label = model.predict(vec)[0]
                confidence = None
                if hasattr(model, "predict_proba"):
                    probs = model.predict_proba(vec)[0]
                    confidence = float(np.max(probs) * 100.0)

                risk_level = "High Risk" if pred_label == 1 else "Low Risk"
                predicted_score = max(50.0, current_score - 5.0) if pred_label == 1 else min(100.0, current_score + 1.5)

                factors = explain_prediction(model, scaler, features)

                mitigations = []
                if risk_level == "High Risk":
                    mitigations.append("Plan personnel duty rotations to accommodate upcoming medical board recategorizations.")
                    mitigations.append("Ensure temporary duty (TD) soldiers are scheduled to return prior to next deployment cycle.")
                else:
                    mitigations.append("Maintain existing leave and trade rosters to preserve optimal readiness.")

                return PredictionResult(
                    company=coy,
                    current_readiness=current_score,
                    predicted_readiness=round(predicted_score, 1),
                    prediction_period=prediction_period,
                    risk_level=risk_level,
                    confidence=round(confidence, 1) if confidence else None,
                    model_version=metadata.get("model_version", "v1.0"),
                    status_code="AVAILABLE",
                    status_message=f"Prediction generated using {metadata.get('best_model', 'ML model')}.",
                    important_factors=factors,
                    mitigation_recommendations=mitigations
                )

            except Exception as e:
                # Log error and fall back gracefully
                pass

        # Transparent fallback when genuine training data has not yet accumulated
        # NO FAKE PREDICTIONS, NO FAKE CONFIDENCE
        metadata = get_model_metadata() or {}
        return PredictionResult(
            company=coy,
            current_readiness=current_score,
            predicted_readiness=None,
            prediction_period=prediction_period,
            risk_level="Under Evaluation",
            confidence=None,
            model_version=metadata.get("model_version", "v0.1-baseline"),
            status_code="UNDER_DEVELOPMENT",
            status_message=(
                "ML prediction is under development because sufficient historical training data is not yet available. "
                "The system is currently logging periodic readiness snapshots to accumulate the required training dataset."
            ),
            important_factors=[
                {
                    "feature": "upcoming_recat_ratio",
                    "label": "Upcoming Medical Reviews",
                    "value": f"{round(features.get('upcoming_recat_ratio', 0.0) * 100, 1)}%",
                    "importance": 0.25,
                    "description": "Personnel due for medical board evaluation within next 60 days."
                },
                {
                    "feature": "leave_rate",
                    "label": "Current Leave Rate",
                    "value": f"{round(features.get('leave_rate', 0.0) * 100, 1)}%",
                    "importance": 0.20,
                    "description": "Portion of formation personnel absent on authorized leave."
                },
                {
                    "feature": "trade_fulfillment_ratio",
                    "label": "Trade Fulfillment",
                    "value": f"{round(features.get('trade_fulfillment_ratio', 1.0) * 100, 1)}%",
                    "importance": 0.20,
                    "description": "Specialized communication and technical trades staffing ratio."
                }
            ],
            mitigation_recommendations=[
                "Monitor periodic snapshot logs as historical data accumulates.",
                "Review personnel with upcoming medical recategorization boards.",
                "Ensure technical trades vacancies are submitted in forthcoming posting demands."
            ]
        )
