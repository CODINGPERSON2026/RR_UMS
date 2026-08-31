"""
Supervised ML Model Training and Retraining Pipeline (Hierarchical & Trade-Free)
Implements 70/30 Stratified Split, SMOTE on Training Only, RF vs XGBoost Comparison,
SHAP Explainer Setup, and Artifact Serialization.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Tuple

# Ensure workspace root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE

from aiml.ai_new_joinee_recommendation.position_mapping import VALID_COMPANIES
from aiml.ai_new_joinee_recommendation.preprocessing import load_historical_dataset
from aiml.ai_new_joinee_recommendation.evaluation import evaluate_company_model, compare_models
from aiml.ai_new_joinee_recommendation.explainability import SHAPExplainerWrapper

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")


def run_training_pipeline() -> Dict[str, Any]:
    """
    Execute the end-to-end model training, evaluation, model selection, and artifact saving pipeline.
    Strictly excludes trade from model features, datasets, and metadata.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    start_time = datetime.now()
    print(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Starting AI New Joinee Model Training Pipeline (Trade-Free)...")

    # 1. Fetch and clean dataset
    df_raw_features, s_targets, df_meta = load_historical_dataset()
    total_records = len(df_raw_features)
    print(f"Loaded {total_records} historical personnel records from database.")

    # Drop non-feature identifiers
    feature_cols = [c for c in df_raw_features.columns if c not in ("personnel_id", "army_number", "target_company", "trade")]
    X = df_raw_features[feature_cols].copy().fillna(0.0)
    y = s_targets.copy()

    # 2. 70% Training / 30% Testing Stratified Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.30,
        random_state=42,
        stratify=y
    )
    print(f"Dataset split: Training Set = {len(X_train)} samples (70%), Unseen Test Set = {len(X_test)} samples (30%).")

    # 3. Apply SMOTE ONLY to the Training Dataset
    min_class_count = y_train.value_counts().min()
    k_neighbors = min(3, max(1, min_class_count - 1))
    smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    print(f"SMOTE applied strictly to training data: Resampled training size = {len(X_train_res)} samples.")

    # 4. Train Random Forest Classifier
    rf_model = RandomForestClassifier(
        n_estimators=160,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced"
    )
    rf_model.fit(X_train_res, y_train_res)
    eval_rf = evaluate_company_model(rf_model, X_test, y_test, model_name="Random Forest")
    print(f"Random Forest Unseen Test Accuracy: {eval_rf['accuracy']}%, F1-Score: {eval_rf['f1_weighted']}%")

    # 5. Train XGBoost Classifier
    class_to_int = {cls: idx for idx, cls in enumerate(VALID_COMPANIES)}
    int_to_class = {idx: cls for idx, cls in enumerate(VALID_COMPANIES)}

    y_train_res_int = y_train_res.map(class_to_int)
    y_test_int = y_test.map(class_to_int)

    xgb_model_raw = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="mlogloss"
    )
    xgb_model_raw.fit(X_train_res, y_train_res_int)

    # Wrap XGBoost to accept class labels natively
    class XGBClassWrapper:
        def __init__(self, raw_model, int_to_cls, classes):
            self.model = raw_model
            self.int_to_class = int_to_cls
            self.classes_ = np.array(classes)

        def predict(self, X_input):
            preds_int = self.model.predict(X_input)
            return np.array([self.int_to_class.get(i, "HQ COY") for i in preds_int])

        def predict_proba(self, X_input):
            return self.model.predict_proba(X_input)

        @property
        def feature_importances_(self):
            return self.model.feature_importances_

    xgb_model = XGBClassWrapper(xgb_model_raw, int_to_class, VALID_COMPANIES)
    eval_xgb = evaluate_company_model(xgb_model, X_test, y_test, model_name="XGBoost")
    print(f"XGBoost Unseen Test Accuracy: {eval_xgb['accuracy']}%, F1-Score: {eval_xgb['f1_weighted']}%")

    # 6. Model Comparison & Selection
    comparison = compare_models(eval_rf, eval_xgb)
    selected_name = comparison["selected_model"]
    champion_model = rf_model if selected_name == "Random Forest" else xgb_model
    champion_eval = eval_rf if selected_name == "Random Forest" else eval_xgb

    print(f"Champion Model Selected: {selected_name}. Reason: {comparison['selection_reason']}")

    # 7. Compute Feature Importance
    if hasattr(champion_model, "feature_importances_"):
        raw_importances = champion_model.feature_importances_
    else:
        raw_importances = rf_model.feature_importances_

    feat_importance_list = []
    for f_name, imp in zip(feature_cols, raw_importances):
        feat_importance_list.append({
            "feature": f_name,
            "importance": round(float(imp) * 100.0, 2)
        })
    feat_importance_list.sort(key=lambda x: x["importance"], reverse=True)

    # 8. SHAP Explainer
    explainer_wrapper = SHAPExplainerWrapper(
        model=rf_model if selected_name == "Random Forest" else xgb_model_raw,
        feature_names=feature_cols,
        class_names=VALID_COMPANIES
    )

    # 9. Save Artifacts to model/ directory
    joblib.dump(champion_model, os.path.join(MODEL_DIR, "champion_model.joblib"))
    joblib.dump(rf_model, os.path.join(MODEL_DIR, "rf_model.joblib"))
    joblib.dump(xgb_model_raw, os.path.join(MODEL_DIR, "xgb_raw.joblib"))
    joblib.dump(explainer_wrapper, os.path.join(MODEL_DIR, "shap_wrapper.joblib"))

    end_time = datetime.now()
    training_duration_sec = round((end_time - start_time).total_seconds(), 2)

    metadata = {
        "model_version": "company_position_model_v2",
        "trade_excluded": True,
        "trained_at": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "training_duration_seconds": training_duration_sec,
        "selected_model": selected_name,
        "champion_metrics": champion_eval,
        "comparison": comparison,
        "total_records": total_records,
        "train_records": len(X_train),
        "test_records": len(X_test),
        "feature_count": len(feature_cols),
        "feature_names": feature_cols,
        "classes": VALID_COMPANIES,
        "hierarchy_structure": {
            "companies": len(VALID_COMPANIES),
            "sections": 10,
            "positions": 34
        }
    }

    with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    with open(os.path.join(MODEL_DIR, "feature_names.json"), "w") as f:
        json.dump(feature_cols, f, indent=2)

    with open(os.path.join(MODEL_DIR, "feature_importance.json"), "w") as f:
        json.dump(feat_importance_list, f, indent=2)

    with open(os.path.join(MODEL_DIR, "evaluation_report.json"), "w") as f:
        json.dump({
            "champion": champion_eval,
            "comparison": comparison,
            "top_features": feat_importance_list[:10]
        }, f, indent=2)

    print(f"Training completed successfully in {training_duration_sec}s. Artifacts saved to: {MODEL_DIR}")
    return metadata


if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"e:\UMS-LATEST")
    run_training_pipeline()
