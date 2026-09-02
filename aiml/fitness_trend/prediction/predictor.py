"""
Model Inference and Prediction Engine for AI/ML Fitness Trend.
Caches trained models in memory and generates predictions with explainable factors.
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from ..config import (
    MODELS_DIR,
    CLASSIFIER_MODEL_PATH,
    REGRESSOR_MODEL_PATH,
    PREPROCESSOR_PATH,
    METADATA_PATH,
    DEFAULT_MODEL_VERSION,
    FITNESS_CATEGORIES
)
from ..features.feature_engineering import ML_FEATURE_COLUMNS, score_to_fitness_category
from .confidence import compute_prediction_confidence, extract_explainable_factors

logger = logging.getLogger("fitness_trend.predictor")

# In-memory model cache
_CACHED_MODELS = {
    'version': None,
    'classifier': None,
    'regressor': None,
    'preprocessor': None,
    'metadata': None
}


def load_cached_models(version=DEFAULT_MODEL_VERSION, force_reload=False):
    """
    Loads trained model artifacts into memory if not already cached.
    """
    global _CACHED_MODELS
    
    if not force_reload and _CACHED_MODELS['version'] == version and _CACHED_MODELS['classifier'] is not None:
        return _CACHED_MODELS
        
    clf_path = os.path.join(MODELS_DIR, f"fitness_classifier_{version}.joblib")
    reg_path = os.path.join(MODELS_DIR, f"fitness_regressor_{version}.joblib")
    prep_path = os.path.join(MODELS_DIR, f"preprocessor_{version}.joblib")
    meta_path = os.path.join(MODELS_DIR, f"metadata_{version}.json")
    
    if not (os.path.exists(clf_path) and os.path.exists(prep_path) and os.path.exists(meta_path)):
        logger.warning(f"Model artifacts for version {version} not found on disk at {MODELS_DIR}.")
        return None
        
    try:
        classifier = joblib.load(clf_path)
        regressor = joblib.load(reg_path) if os.path.exists(reg_path) else None
        preprocessor = joblib.load(prep_path)
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
        _CACHED_MODELS['version'] = version
        _CACHED_MODELS['classifier'] = classifier
        _CACHED_MODELS['regressor'] = regressor
        _CACHED_MODELS['preprocessor'] = preprocessor
        _CACHED_MODELS['metadata'] = metadata
        
        logger.info(f"Loaded fitness models version {version} successfully into cache.")
        return _CACHED_MODELS
    except Exception as e:
        logger.error(f"Failed to load model artifacts: {e}")
        return None


def get_model_info():
    """
    Returns metadata about the active ML models.
    """
    models = load_cached_models()
    if not models or not models.get('metadata'):
        return {
            'available': False,
            'message': 'No trained fitness models available on server.'
        }
    meta = models['metadata']
    return {
        'available': True,
        'model_version': meta.get('model_version'),
        'trained_at': meta.get('trained_at'),
        'dataset_size_valid': meta.get('dataset_size_valid'),
        'selected_classifier': meta.get('selected_classifier'),
        'classifier_metrics': meta.get('classifier_metrics'),
        'selected_regressor': meta.get('selected_regressor'),
        'regressor_metrics': meta.get('regressor_metrics'),
        'feature_importances': meta.get('feature_importances', {})
    }


def predict_soldier_fitness(soldier_features):
    """
    Generates AI Fitness Prediction for a soldier.
    
    Returns structured dict with:
    - prediction_status: 'SUCCESS' or 'INSUFFICIENT_DATA' or 'MODEL_UNAVAILABLE'
    - fitness_score: float (0 - 100)
    - fitness_category: 'EXCELLENT', 'GOOD', 'AVERAGE', 'NEEDS_IMPROVEMENT'
    - category_label: str
    - category_color: str
    - confidence_score: float
    - strengths: list of str
    - improvements: list of str
    - explainable_factors: dict
    """
    # 1. Check Data Sufficiency
    if not soldier_features.get('is_sufficient_for_prediction'):
        return {
            'prediction_status': 'INSUFFICIENT_DATA',
            'error_message': 'Insufficient vital fitness records (height, weight, or age missing) to generate a reliable AI prediction.',
            'fitness_score': None,
            'fitness_category': 'UNKNOWN',
            'category_label': 'Insufficient Data',
            'category_color': '#94a3b8',
            'confidence_score': 0.0,
            'strengths': [],
            'improvements': soldier_features.get('data_quality_flags', ["Missing vital metrics."]),
            'model_version': 'N/A'
        }
        
    # 2. Load Model
    models = load_cached_models()
    if not models:
        # Graceful rule-based fallback
        gt_score = soldier_features.get('ground_truth_score', 70.0)
        gt_cat = soldier_features.get('ground_truth_category', 'AVERAGE')
        cat_meta = FITNESS_CATEGORIES.get(gt_cat, FITNESS_CATEGORIES['AVERAGE'])
        factors = extract_explainable_factors(soldier_features)
        
        return {
            'prediction_status': 'RULE_BASED_BASELINE',
            'warning_message': 'ML Model file not active; baseline evaluation generated.',
            'fitness_score': gt_score,
            'fitness_category': gt_cat,
            'category_label': cat_meta['label'],
            'category_color': cat_meta['color'],
            'category_badge': cat_meta['badge'],
            'confidence_score': 78.0,
            'strengths': factors['strengths'],
            'improvements': factors['improvements'],
            'model_version': 'Rule-Based Baseline'
        }
        
    # 3. Assemble Feature Vector
    row_dict = {}
    for col in ML_FEATURE_COLUMNS:
        val = soldier_features.get(col)
        row_dict[col] = float(val) if val is not None else np.nan
        
    df_sample = pd.DataFrame([row_dict], columns=ML_FEATURE_COLUMNS)
    
    try:
        # Preprocess features
        X_prep = models['preprocessor'].transform(df_sample)
        
        # Predict Fitness Score via Regressor
        if models['regressor']:
            score_pred = float(models['regressor'].predict(X_prep)[0])
            score_pred = round(max(15.0, min(100.0, score_pred)), 1)
        else:
            score_pred = soldier_features.get('ground_truth_score', 70.0)
            
        # Predict Category via Classifier
        clf = models['classifier']
        meta = models['metadata']
        classes = meta.get('label_encoder_classes', ['AVERAGE', 'EXCELLENT', 'GOOD', 'NEEDS_IMPROVEMENT'])
        
        pred_idx = clf.predict(X_prep)[0]
        if isinstance(pred_idx, (int, np.integer)) and pred_idx < len(classes):
            cat_pred = classes[pred_idx]
        else:
            cat_pred = str(pred_idx)
            
        # Align category with score if regression and classification slightly differ
        aligned_cat = score_to_fitness_category(score_pred)
        if aligned_cat in FITNESS_CATEGORIES:
            cat_pred = aligned_cat
            
        cat_info = FITNESS_CATEGORIES.get(cat_pred, FITNESS_CATEGORIES['AVERAGE'])
        
        # Compute Confidence Score
        confidence = compute_prediction_confidence(clf, X_prep, soldier_features)
        
        # Extract Strengths & Improvement Factors
        factors = extract_explainable_factors(soldier_features)
        
        return {
            'prediction_status': 'SUCCESS',
            'fitness_score': score_pred,
            'fitness_category': cat_pred,
            'category_label': cat_info['label'],
            'category_color': cat_info['color'],
            'category_badge': cat_info['badge'],
            'confidence_score': confidence,
            'strengths': factors['strengths'],
            'improvements': factors['improvements'],
            'model_version': models['version'],
            'algorithm': meta.get('selected_classifier')
        }
    except Exception as e:
        logger.error(f"Inference error for soldier {soldier_features.get('army_number')}: {e}")
        # Fallback to calculated readiness score
        gt_score = soldier_features.get('ground_truth_score', 70.0)
        gt_cat = soldier_features.get('ground_truth_category', 'AVERAGE')
        cat_meta = FITNESS_CATEGORIES.get(gt_cat, FITNESS_CATEGORIES['AVERAGE'])
        factors = extract_explainable_factors(soldier_features)
        
        return {
            'prediction_status': 'FALLBACK_BASELINE',
            'fitness_score': gt_score,
            'fitness_category': gt_cat,
            'category_label': cat_meta['label'],
            'category_color': cat_meta['color'],
            'category_badge': cat_meta['badge'],
            'confidence_score': 75.0,
            'strengths': factors['strengths'],
            'improvements': factors['improvements'],
            'model_version': 'Fallback Baseline'
        }
