"""
Feature engineering modules for AI/ML Fitness Trend.
"""

from .bmi import calculate_bmi, get_bmi_category
from .ideal_weight import calculate_ideal_weight_and_deviation
from .sports_features import extract_sports_features
from .medical_features import extract_medical_features
from .feature_engineering import generate_features_for_soldier, generate_dataset_features

__all__ = [
    'calculate_bmi',
    'get_bmi_category',
    'calculate_ideal_weight_and_deviation',
    'extract_sports_features',
    'extract_medical_features',
    'generate_features_for_soldier',
    'generate_dataset_features'
]
