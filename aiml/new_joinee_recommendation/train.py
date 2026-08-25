from datetime import datetime
import json
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from .config import (
    RANDOM_STATE,
    TEST_SIZE,
    CANONICAL_COMPANIES,
    RF_MODEL_DIR,
    XGB_MODEL_DIR,
    METRICS_DIR,
    REPORTS_DIR,
    MODELS_DIR,
    BEST_MODEL_FILE,
    BEST_MODEL_INFO_FILE,
    MODEL_METADATA_FILE,
    RETRAINING_LOG_FILE
)
from .data_loader import load_raw_data, profile_dataset
from .feature_engineering import build_dataset
from .preprocessing import CompanyPreprocessor, apply_smote
from .evaluate import evaluate_model, run_cross_validation
from .utils import get_logger, CustomJSONEncoder

logger = get_logger("train")

def ensure_directories():
    """Ensures all artifact and model directories exist."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RF_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    XGB_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def get_feature_importances(model: Any, feature_names: list, top_n: int = 15) -> Dict[str, float]:
    """Extracts normalized feature importance dictionary."""
    try:
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            feat_imp = {feat: float(imp) for feat, imp in zip(feature_names, importances)}
            sorted_imp = dict(sorted(feat_imp.items(), key=lambda item: item[1], reverse=True)[:top_n])
            return sorted_imp
    except Exception as e:
        logger.warning(f"Could not compute feature importances: {e}")
    return {}

def train_pipeline() -> Dict[str, Any]:
    """
    Executes the complete end-to-end training, evaluation, comparison, and artifact saving pipeline
    on combined database and CSV dataset records.
    """
    logger.info("=" * 60)
    logger.info("STARTING AI NEW JOINEE COMPANY RECOMMENDATION TRAINING PIPELINE")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    ensure_directories()

    # 1. Load combined raw data (DB + CSV Datasets)
    personnel_df, units_df = load_raw_data()
    
    # 2. Data profiling
    profile = profile_dataset(personnel_df, units_df)
    logger.info(f"Dataset Profile: Total={profile.get('total_eligible')} (DB={profile.get('database_records')}, CSV={profile.get('synthetic_csv_records')})")
    
    # 3. Build feature dataset
    X, y = build_dataset(personnel_df, units_df)
    
    total_records = len(X)
    if total_records < 10:
        raise ValueError(f"Insufficient training records ({total_records}). Minimum 10 required.")

    # 4. Stratified Train / Test Split (Strictly before SMOTE & preprocessing)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE
    )
    logger.info(f"Train/Test split complete: Train samples={len(X_train)}, Test samples={len(X_test)}")

    # 5. Preprocessing & Encoding
    preprocessor = CompanyPreprocessor()
    preprocessor.fit(X_train, y_train)
    
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    
    y_train_encoded = preprocessor.encode_target(y_train)
    y_test_encoded = preprocessor.encode_target(y_test)
    
    # Save preprocessor artifacts
    preprocessor.save()

    # 6. Apply SMOTE exclusively on training data
    X_train_resampled, y_train_resampled, before_dist, after_dist = apply_smote(
        X_train_trans,
        y_train_encoded,
        preprocessor.label_encoder
    )

    class_names = list(preprocessor.label_encoder.classes_)
    feature_names = preprocessor.encoded_feature_names

    # 7. Train & Evaluate Model 1: Random Forest
    logger.info("Training Model 1: RandomForestClassifier...")
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    rf_cv = run_cross_validation(rf_model, X_train_resampled, y_train_resampled)
    rf_model.fit(X_train_resampled, y_train_resampled)
    rf_metrics = evaluate_model(rf_model, X_test_trans, y_test_encoded, class_names, model_name="Random Forest")
    rf_metrics.update(rf_cv)
    rf_metrics["feature_importance"] = get_feature_importances(rf_model, feature_names)

    # Save RF Model
    joblib.dump(rf_model, RF_MODEL_DIR / "rf_model.joblib")

    # 8. Train & Evaluate Model 2: XGBoost
    logger.info("Training Model 2: XGBClassifier...")
    xgb_model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="multi:softprob",
        num_class=len(class_names),
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    xgb_cv = run_cross_validation(xgb_model, X_train_resampled, y_train_resampled)
    xgb_model.fit(X_train_resampled, y_train_resampled)
    xgb_metrics = evaluate_model(xgb_model, X_test_trans, y_test_encoded, class_names, model_name="XGBoost")
    xgb_metrics.update(xgb_cv)
    xgb_metrics["feature_importance"] = get_feature_importances(xgb_model, feature_names)

    # Save XGBoost Model
    joblib.dump(xgb_model, XGB_MODEL_DIR / "xgb_model.joblib")

    # 9. Model Selection based on validation/test metrics
    logger.info("Comparing Random Forest vs XGBoost...")
    # Selection criteria: Test Accuracy -> Macro F1 -> CV Mean Accuracy
    rf_score = (rf_metrics["accuracy"] * 0.40) + (rf_metrics["macro_f1"] * 0.35) + (rf_metrics["cv_mean_accuracy"] * 0.25)
    xgb_score = (xgb_metrics["accuracy"] * 0.40) + (xgb_metrics["macro_f1"] * 0.35) + (xgb_metrics["cv_mean_accuracy"] * 0.25)

    if xgb_score >= rf_score:
        selected_model_name = "XGBoost"
        selected_model = xgb_model
        selected_metrics = xgb_metrics
    else:
        selected_model_name = "Random Forest"
        selected_model = rf_model
        selected_metrics = rf_metrics

    logger.info(f"==> Selected Best Model: {selected_model_name} (Composite Score: {max(rf_score, xgb_score):.4f})")

    # Save Best Model pointer & binary
    joblib.dump(selected_model, BEST_MODEL_FILE)
    
    best_model_info = {
        "selected_model": selected_model_name,
        "trained_at": datetime.now().isoformat(),
        "accuracy": selected_metrics["accuracy"],
        "macro_f1": selected_metrics["macro_f1"],
        "top_1_accuracy": selected_metrics["top_1_accuracy"],
        "top_2_accuracy": selected_metrics["top_2_accuracy"],
        "cv_mean_accuracy": selected_metrics["cv_mean_accuracy"]
    }
    with open(BEST_MODEL_INFO_FILE, "w") as f:
        json.dump(best_model_info, f, indent=2)

    # 10. Save Model Comparison & Metadata
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "selected_model": selected_model_name,
        "dataset_summary": {
            "total_records": total_records,
            "train_records": len(X_train),
            "test_records": len(X_test),
            "database_records": profile.get("database_records", 0),
            "synthetic_csv_records": profile.get("synthetic_csv_records", 0),
            "feature_count": len(feature_names),
            "class_distribution_before_smote": before_dist,
            "class_distribution_after_smote": after_dist
        },
        "models": {
            "Random Forest": rf_metrics,
            "XGBoost": xgb_metrics
        }
    }
    with open(METRICS_DIR / "model_comparison.json", "w") as f:
        json.dump(comparison, f, cls=CustomJSONEncoder, indent=2)

    # Load existing retraining history
    history = []
    if RETRAINING_LOG_FILE.exists():
        try:
            with open(RETRAINING_LOG_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = []

    last_count = history[-1]["record_count"] if history else total_records
    delta_records = total_records - last_count if history else 0

    log_entry = {
        "training_time": datetime.now().isoformat(),
        "record_count": total_records,
        "database_records": profile.get("database_records", 0),
        "synthetic_csv_records": profile.get("synthetic_csv_records", 0),
        "new_records_since_previous_training": delta_records,
        "random_forest_accuracy": rf_metrics["accuracy"],
        "xgboost_accuracy": xgb_metrics["accuracy"],
        "selected_model": selected_model_name,
        "selected_accuracy": selected_metrics["accuracy"],
        "macro_f1": selected_metrics["macro_f1"],
        "top_1_accuracy": selected_metrics["top_1_accuracy"],
        "top_2_accuracy": selected_metrics["top_2_accuracy"]
    }
    history.append(log_entry)
    with open(RETRAINING_LOG_FILE, "w") as f:
        json.dump(history, f, indent=2)

    # Full Model Metadata
    metadata = {
        "version": "2.0.0",
        "last_trained_at": datetime.now().isoformat(),
        "total_eligible_records": total_records,
        "database_records": profile.get("database_records", 0),
        "synthetic_csv_records": profile.get("synthetic_csv_records", 0),
        "selected_model": selected_model_name,
        "canonical_classes": class_names,
        "feature_count": len(feature_names),
        "smote_distribution": {
            "before": before_dist,
            "after": after_dist
        },
        "metrics": selected_metrics,
        "dataset_profile": profile,
        "training_duration_seconds": round((datetime.now() - start_time).total_seconds(), 2)
    }
    with open(MODEL_METADATA_FILE, "w") as f:
        json.dump(metadata, f, cls=CustomJSONEncoder, indent=2)

    logger.info("=" * 60)
    logger.info(f"TRAINING COMPLETE. Selected: {selected_model_name} | Accuracy: {selected_metrics['accuracy']:.4f} | Macro-F1: {selected_metrics['macro_f1']:.4f}")
    logger.info("=" * 60)
    
    return metadata

if __name__ == "__main__":
    train_pipeline()

