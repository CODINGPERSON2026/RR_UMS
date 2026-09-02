"""
Prediction and Explainability module for AI/ML Fitness Trend.
"""

from .predictor import predict_soldier_fitness, get_model_info
from .confidence import compute_prediction_confidence, extract_explainable_factors

__all__ = [
    'predict_soldier_fitness',
    'get_model_info',
    'compute_prediction_confidence',
    'extract_explainable_factors'
]
