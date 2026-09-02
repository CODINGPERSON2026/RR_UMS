"""
End-to-End Training Pipeline for AI/ML Fitness Trend.
Trains, evaluates, and persists classification & regression models with full metadata audit.
"""

import os
import sys
import json
import logging
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Add root project path if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from aiml.fitness_trend.config import (
    MODELS_DIR,
    CLASSIFIER_MODEL_PATH,
    REGRESSOR_MODEL_PATH,
    PREPROCESSOR_PATH,
    METADATA_PATH,
    DEFAULT_MODEL_VERSION
)
from aiml.fitness_trend.data.db_loader import fetch_all_personnel_fitness_data
from aiml.fitness_trend.features.feature_engineering import generate_dataset_features, ML_FEATURE_COLUMNS
from aiml.fitness_trend.training.preprocessing import build_preprocessor_pipeline, prepare_ml_data_arrays
from aiml.fitness_trend.training.model_selection import get_classifier_candidates, get_regressor_candidates
from aiml.fitness_trend.training.evaluate import evaluate_classifier, evaluate_regressor

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("fitness_trend.training")


def train_and_persist_models(version=DEFAULT_MODEL_VERSION):
    """
    Executes complete training, evaluation, model selection, and persistence workflow.
    
    Returns:
        dict: Training results and metrics summary.
    """
    logger.info("Starting AI/ML Fitness Training Pipeline...")
    
    # 1. Fetch data from DB
    p_rows, w_rows, s_rows, iw_rows = fetch_all_personnel_fitness_data()
    logger.info(f"Loaded {len(p_rows)} personnel, {len(w_rows)} weight records, {len(s_rows)} sports records, {len(iw_rows)} ideal weights.")
    
    if len(p_rows) < 10:
        msg = "Insufficient data in database to train reliable ML models (less than 10 records)."
        logger.warning(msg)
        return {'success': False, 'error': msg}
        
    # 2. Extract features
    features_list = generate_dataset_features(p_rows, w_rows, s_rows, iw_rows)
    logger.info(f"Generated features for {len(features_list)} personnel records.")
    
    # 3. Prepare data arrays
    df_X, y_class, y_score = prepare_ml_data_arrays(features_list)
    logger.info(f"Valid dataset size for ML: {len(df_X)} rows.")
    
    if len(df_X) < 10:
        msg = "Insufficient valid records with complete demographic data."
        logger.warning(msg)
        return {'success': False, 'error': msg}
        
    # 4. Train / Test Split (80% train, 20% test)
    # Stratify by classification target if all classes have >= 2 samples
    class_counts = y_class.value_counts()
    stratify = y_class if (class_counts.min() >= 2 and len(class_counts) > 1) else None
    
    X_train, X_test, y_cls_train, y_cls_test, y_scr_train, y_scr_test = train_test_split(
        df_X, y_class, y_score, test_size=0.20, random_state=42, stratify=stratify
    )
    
    logger.info(f"Train split: {len(X_train)} samples, Test split: {len(X_test)} samples.")
    
    # 5. Fit Preprocessor ONLY on Training Split
    preprocessor = build_preprocessor_pipeline()
    X_train_prep = preprocessor.fit_transform(X_train)
    X_test_prep = preprocessor.transform(X_test)
    
    # 6. Encode Classification Labels
    label_encoder = LabelEncoder()
    y_cls_train_enc = label_encoder.fit_transform(y_cls_train)
    y_cls_test_enc = label_encoder.transform(y_cls_test)
    
    # 7. Evaluate Classification Candidates
    classifier_candidates = get_classifier_candidates()
    best_classifier_name = None
    best_classifier_model = None
    best_classifier_metrics = None
    best_f1 = -1.0
    
    cls_eval_results = {}
    for name, model in classifier_candidates.items():
        try:
            model.fit(X_train_prep, y_cls_train_enc)
            metrics = evaluate_classifier(model, X_test_prep, y_cls_test_enc, class_labels=list(range(len(label_encoder.classes_))))
            # Replace integer labels in metrics with string class names
            metrics['classes'] = list(label_encoder.classes_)
            cls_eval_results[name] = metrics
            logger.info(f"Classifier [{name}] -> Accuracy: {metrics['accuracy']}, F1-Weighted: {metrics['f1_weighted']}")
            
            if metrics['f1_weighted'] > best_f1:
                best_f1 = metrics['f1_weighted']
                best_classifier_name = name
                best_classifier_model = model
                best_classifier_metrics = metrics
        except Exception as e:
            logger.error(f"Error training classifier {name}: {e}")
            
    # 8. Evaluate Regression Candidates
    regressor_candidates = get_regressor_candidates()
    best_regressor_name = None
    best_regressor_model = None
    best_regressor_metrics = None
    best_r2 = -999.0
    
    reg_eval_results = {}
    for name, model in regressor_candidates.items():
        try:
            model.fit(X_train_prep, y_scr_train)
            metrics = evaluate_regressor(model, X_test_prep, y_scr_test)
            reg_eval_results[name] = metrics
            logger.info(f"Regressor [{name}] -> MAE: {metrics['mae']}, R2: {metrics['r2_score']}")
            
            if metrics['r2_score'] > best_r2:
                best_r2 = metrics['r2_score']
                best_regressor_name = name
                best_regressor_model = model
                best_regressor_metrics = metrics
        except Exception as e:
            logger.error(f"Error training regressor {name}: {e}")
            
    # 9. Extract Feature Importances if available
    feature_importances = {}
    if hasattr(best_classifier_model, 'feature_importances_'):
        importances = best_classifier_model.feature_importances_
        for col, imp in zip(ML_FEATURE_COLUMNS, importances):
            feature_importances[col] = round(float(imp), 4)
            
    # 10. Persist Model Artifacts
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    clf_path = os.path.join(MODELS_DIR, f"fitness_classifier_{version}.joblib")
    reg_path = os.path.join(MODELS_DIR, f"fitness_regressor_{version}.joblib")
    prep_path = os.path.join(MODELS_DIR, f"preprocessor_{version}.joblib")
    meta_path = os.path.join(MODELS_DIR, f"metadata_{version}.json")
    
    joblib.dump(best_classifier_model, clf_path)
    joblib.dump(best_regressor_model, reg_path)
    joblib.dump(preprocessor, prep_path)
    
    metadata = {
        'model_version': version,
        'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'dataset_size_total': len(p_rows),
        'dataset_size_valid': len(df_X),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'feature_names': ML_FEATURE_COLUMNS,
        'label_encoder_classes': list(label_encoder.classes_),
        'selected_classifier': best_classifier_name,
        'classifier_metrics': best_classifier_metrics,
        'all_classifier_metrics': cls_eval_results,
        'selected_regressor': best_regressor_name,
        'regressor_metrics': best_regressor_metrics,
        'all_regressor_metrics': reg_eval_results,
        'feature_importances': feature_importances
    }
    
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Models and metadata saved successfully to {MODELS_DIR} (Version: {version})")
    
    return {
        'success': True,
        'version': version,
        'dataset_size': len(df_X),
        'classifier': best_classifier_name,
        'classifier_accuracy': best_classifier_metrics.get('accuracy') if best_classifier_metrics else None,
        'classifier_f1': best_classifier_metrics.get('f1_weighted') if best_classifier_metrics else None,
        'regressor': best_regressor_name,
        'regressor_mae': best_regressor_metrics.get('mae') if best_regressor_metrics else None,
        'regressor_r2': best_regressor_metrics.get('r2_score') if best_regressor_metrics else None
    }


if __name__ == '__main__':
    result = train_and_persist_models()
    print("\nTraining Result Summary:")
    print(json.dumps(result, indent=2))
