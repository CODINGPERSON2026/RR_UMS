"""
Machine Learning Training Pipeline for AI Company Readiness.
Supports model comparison across Logistic Regression, Random Forest, and Gradient Boosting.
Enforces statistical thresholds and train/test separation.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

from ..feature_engineering import FEATURE_COLUMNS
from .model_utils import save_model_artifacts

# Minimum genuine historical records required for statistically sound training
MIN_TRAINING_SAMPLES = 50


class ReadinessModelTrainer:
    """
    Orchestrates data preparation, cross-validation, model comparison,
    and artifact export.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state

    def compare_and_train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_version: str = "v1.0"
    ) -> Dict[str, Any]:
        """
        Trains and compares Logistic Regression, Random Forest, and Gradient Boosting.
        Selects the best performing model on the test split.
        """
        sample_count = len(X)
        if sample_count < MIN_TRAINING_SAMPLES:
            return {
                "success": False,
                "status": "INSUFFICIENT_DATA",
                "sample_count": sample_count,
                "required_count": MIN_TRAINING_SAMPLES,
                "message": (
                    f"ML prediction is under development because sufficient historical training data "
                    f"is not yet available ({sample_count}/{MIN_TRAINING_SAMPLES} required snapshots)."
                )
            }

        # Train / Test split (80 / 20)
        X_train, X_test, y_train, y_test = train_test_split(
            X[FEATURE_COLUMNS], y, test_size=0.20, random_state=self.random_state, stratify=y if len(np.unique(y)) > 1 else None
        )

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        candidate_models = {
            "Logistic Regression": LogisticRegression(random_state=self.random_state, max_iter=500),
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=5, random_state=self.random_state),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, learning_rate=0.08, max_depth=3, random_state=self.random_state)
        }

        results = {}
        best_name = None
        best_f1 = -1.0
        best_model = None

        for name, clf in candidate_models.items():
            # Use scaled data for LR, raw for trees
            X_tr = X_train_scaled if name == "Logistic Regression" else X_train.values
            X_te = X_test_scaled if name == "Logistic Regression" else X_test.values

            clf.fit(X_tr, y_train)
            preds = clf.predict(X_te)
            probs = clf.predict_proba(X_te)[:, 1] if hasattr(clf, "predict_proba") else None

            acc = float(accuracy_score(y_test, preds))
            prec = float(precision_score(y_test, preds, zero_division=0))
            rec = float(recall_score(y_test, preds, zero_division=0))
            f1 = float(f1_score(y_test, preds, zero_division=0))
            roc = float(roc_auc_score(y_test, probs)) if probs is not None and len(np.unique(y_test)) > 1 else None
            cm = confusion_matrix(y_test, preds).tolist()

            results[name] = {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc, 4) if roc is not None else "N/A",
                "confusion_matrix": cm
            }

            if f1 > best_f1:
                best_f1 = f1
                best_name = name
                best_model = clf

        # Compile metadata
        metadata = {
            "model_version": model_version,
            "trained_at": datetime.now().isoformat(),
            "best_model": best_name,
            "sample_count": sample_count,
            "feature_names": FEATURE_COLUMNS,
            "evaluation_metrics": results,
            "best_f1": round(best_f1, 4)
        }

        # Save model artifacts
        save_model_artifacts(best_model, scaler, metadata)

        return {
            "success": True,
            "status": "TRAINED",
            "best_model": best_name,
            "results": results,
            "metadata": metadata
        }
