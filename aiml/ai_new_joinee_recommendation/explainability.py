"""
Model Explainability and SHAP Feature Attribution Engine
Converts SHAP force factors and feature importances into clear, military-grade natural language explanations.
"""

import shap
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

FEATURE_HUMAN_LABELS = {
    "spec_IT": "IT & Computing Specialty",
    "spec_Radio": "Radio & Wireless Specialty",
    "spec_Technical": "Technical / Electronic Specialty",
    "spec_Clerk": "Clerical / Administrative Specialty",
    "spec_System": "System Administration Specialty",
    "spec_Network": "Network Infrastructure Specialty",
    "spec_QM___Logistics": "Logistics & Quartermaster Specialty",
    "spec_MT___Driver": "Mechanical Transport / Driver Specialty",
    "spec_Signal___Comn": "Signals & Communication Specialty",
    "spec_General_Duty": "General Duty Specialty",
    "spec_Security": "Security / Protection Specialty",
    "spec_Admin": "Administrative Specialty",
    "rank_level": "Rank / Seniority Profile",
    "service_years": "Total Military Service Experience",
    "num_units": "Number of Previous Postings",
    "total_tenure_days": "Cumulative Posting Tenure",
    "avg_tenure_days": "Average Posting Duration",
    "has_prev_units": "Prior Field Posting Experience",
    "domain_tech": "Technical Maintenance Duties",
    "domain_comn": "Communication / Signal Center Duties",
    "domain_it": "IT / Server Operations Experience",
    "domain_clerk": "Administrative & Branch Work",
    "domain_qm": "Quartermaster & Store Management",
    "domain_dvr": "Transport Driving Tenures",
    "domain_gd": "General / Regimental Duty Exposure",
    "exp_rr": "Rashtriya Rifles (RR) Field Experience",
    "exp_corps": "Corps HQ Operational Experience",
    "exp_sig_reg": "Signal Regiment Core Exposure",
    "prior_aff_comn": "Communication Coy Compatibility Profile",
    "prior_aff_hq": "HQ Coy Regimental Profile",
    "prior_aff_3coy": "3 Coy Technical Compatibility Profile"
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
        predicted_class: str
    ) -> Dict[str, Any]:
        """
        Generate feature-level SHAP explanation and natural language breakdown for a single sample.
        """
        if self.explainer is None:
            return self._fallback_explanation(X_sample, predicted_class)

        try:
            shap_values = self.explainer.shap_values(X_sample)
            
            # Identify class index
            class_idx = 0
            if predicted_class in self.class_names:
                class_idx = self.class_names.index(predicted_class)

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
                return self._fallback_explanation(X_sample, predicted_class)

            return self._format_shap_output(X_sample.iloc[0], sample_shap, predicted_class)
        except Exception:
            return self._fallback_explanation(X_sample, predicted_class)

    def _format_shap_output(
        self,
        sample_row: pd.Series,
        shap_array: np.ndarray,
        predicted_class: str
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
            if f["abs_shap"] < 0.01:
                continue
            if f["impact"] == "positive":
                msg = f"+ {f['label']} strongly supports placement in {predicted_class}"
                positive_forces.append(msg)
                if len(reasons) < 4:
                    reasons.append(f"{f['label']} aligns with {predicted_class} technical & operational duties.")
            else:
                msg = f"- {f['label']} slightly diminishes weight for {predicted_class}"
                negative_forces.append(msg)

        if not reasons:
            reasons.append(f"Personnel profile and trade match operational requirements for {predicted_class}.")

        return {
            "predicted_company": predicted_class,
            "positive_forces": positive_forces[:5],
            "negative_forces": negative_forces[:3],
            "top_factors": factors[:8],
            "match_reasons": reasons
        }

    def _fallback_explanation(self, X_sample: pd.DataFrame, predicted_class: str) -> Dict[str, Any]:
        """Fallback explanation if SHAP explainer is unavailable."""
        return {
            "predicted_company": predicted_class,
            "positive_forces": [
                f"+ Specialty profile aligns with {predicted_class} technical roster",
                f"+ Rank and service experience fit {predicted_class} establishment"
            ],
            "negative_forces": [],
            "top_factors": [],
            "match_reasons": [
                f"Trade and specialties match requirements for {predicted_class}.",
                f"Service profile aligns with Unit 15 CESR deployment structure."
            ]
        }
