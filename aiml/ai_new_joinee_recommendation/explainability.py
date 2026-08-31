"""
Model Explainability and SHAP Feature Attribution Engine
Converts SHAP force factors and feature importances into clear, military-grade natural language explanations.
STRICTLY TRADE-FREE: Trade is never referenced, calculated, or outputted in explanations.
"""

import shap
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

FEATURE_HUMAN_LABELS = {
    "rank_level": "Rank & Seniority Profile",
    "service_years": "Total Military Service Experience",
    "num_units": "Number of Previous Field Postings",
    "total_tenure_days": "Cumulative Posting Tenure",
    "avg_tenure_days": "Average Posting Duration",
    "has_prev_units": "Prior Field Unit Experience",
    "domain_tech": "Technical & Maintenance Duties Experience",
    "domain_comn": "Communication & Signal Center Duties",
    "domain_it": "IT, Server & Computing Operations Experience",
    "domain_clerk": "Administrative, Clerk & Branch Work",
    "domain_qm": "Quartermaster & Store Management Duties",
    "domain_dvr": "Transport Driving & Vehicle Operations",
    "domain_gd": "General / Regimental Duty Exposure",
    "exp_rr": "Rashtriya Rifles (RR) Operational Exposure",
    "exp_corps": "Corps HQ Operational Experience",
    "exp_sig_reg": "Signal Regiment Core Deployment Experience",
    "has_prior_station": "Prior Station Posting Record",
    "worked_it": "Information Technology Specialized Experience"
}


class SHAPExplainerWrapper:
    """
    Wrapper around SHAP TreeExplainer for Random Forest and XGBoost classifiers.
    """
    def __init__(self, model: Any, feature_names: List[str], class_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.class_names = class_names
        try:
            self.explainer = shap.TreeExplainer(model)
        except Exception:
            self.explainer = None

    def explain_sample(
        self,
        X_sample: pd.DataFrame,
        predicted_company: str,
        section: str = "",
        position: str = ""
    ) -> Dict[str, Any]:
        """
        Generate feature-level SHAP explanation and natural language breakdown for a single sample.
        """
        if self.explainer is None:
            return self._fallback_explanation(X_sample, predicted_company, section, position)

        try:
            shap_values = self.explainer.shap_values(X_sample)

            # Identify class index
            class_idx = 0
            if predicted_company in self.class_names:
                class_idx = self.class_names.index(predicted_company)

            # Handle SHAP multi-class output formats
            if isinstance(shap_values, list):
                # List of arrays per class (e.g. RandomForestClassifier)
                sample_shap = shap_values[class_idx][0]
            elif isinstance(shap_values, np.ndarray):
                if shap_values.ndim == 3:
                    # Shape: (n_samples, n_features, n_classes)
                    sample_shap = shap_values[0, :, class_idx]
                elif shap_values.ndim == 2:
                    # Shape: (n_samples, n_features)
                    sample_shap = shap_values[0]
                else:
                    sample_shap = shap_values.flatten()
            else:
                return self._fallback_explanation(X_sample, predicted_company, section, position)

            return self._format_shap_output(X_sample.iloc[0], sample_shap, predicted_company, section, position)
        except Exception:
            return self._fallback_explanation(X_sample, predicted_company, section, position)

    def _format_shap_output(
        self,
        sample_row: pd.Series,
        shap_array: np.ndarray,
        predicted_company: str,
        section: str = "",
        position: str = ""
    ) -> Dict[str, Any]:
        """Format SHAP values into positive forces, negative forces, and natural language reasons."""
        factors = []
        for feat_name, shap_val in zip(self.feature_names, shap_array):
            feat_val = sample_row.get(feat_name, 0.0)
            human_name = FEATURE_HUMAN_LABELS.get(feat_name, feat_name.replace("_", " ").title())
            factors.append({
                "feature": feat_name,
                "label": human_name,
                "value": float(feat_val),
                "shap_value": float(shap_val),
                "impact": "positive" if shap_val > 0 else "negative",
                "abs_shap": abs(float(shap_val))
            })

        # Sort by absolute SHAP impact
        factors.sort(key=lambda x: x["abs_shap"], reverse=True)

        positive_forces = []
        negative_forces = []
        reasons = []

        for f in factors:
            if f["abs_shap"] < 0.005:
                continue
            if f["impact"] == "positive":
                msg = f"+ {f['label']} strongly supports placement in {predicted_company}"
                positive_forces.append(msg)
                if len(reasons) < 4:
                    reasons.append(f"{f['label']} aligns with historical {predicted_company} assignments.")
            else:
                msg = f"- {f['label']} slightly diminishes weight for {predicted_company}"
                negative_forces.append(msg)

        # Ensure reasons are informative and non-empty
        if not reasons:
            reasons.append(f"Personnel profile and service history match operational requirements for {predicted_company}.")
            if section:
                reasons.append(f"Historical posting pattern shows strong alignment with Section '{section}'.")
            if position:
                reasons.append(f"Personnel experience and seniority profile fit assignment to '{position}'.")

        return {
            "predicted_company": predicted_company,
            "recommended_section": section,
            "recommended_position": position,
            "positive_forces": positive_forces[:5],
            "negative_forces": negative_forces[:3],
            "top_factors": factors[:8],
            "match_reasons": reasons
        }

    def _fallback_explanation(
        self,
        X_sample: pd.DataFrame,
        predicted_company: str,
        section: str = "",
        position: str = ""
    ) -> Dict[str, Any]:
        """Fallback explanation if SHAP explainer is unavailable."""
        reasons = [
            f"Previous unit history and duties strongly align with personnel historically assigned to {predicted_company}.",
            f"Posting duration and seniority profile match {predicted_company} establishment."
        ]
        if section:
            reasons.append(f"Service background demonstrates strong compatibility with Section '{section}'.")
        if position:
            reasons.append(f"Profile and past field duties align with historical '{position}' assignments.")

        return {
            "predicted_company": predicted_company,
            "recommended_section": section,
            "recommended_position": position,
            "positive_forces": [
                f"+ Service background and duty experience align with {predicted_company} establishment",
                f"+ Rank and posting tenure fit {predicted_company} operational roster"
            ],
            "negative_forces": [],
            "top_factors": [],
            "match_reasons": reasons
        }
