"""
Preprocessing and Data Leakage Prevention Pipeline.
Ensures imputation and standard scaling are fitted strictly on the training partition only.
"""

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from ..features.feature_engineering import ML_FEATURE_COLUMNS


def build_preprocessor_pipeline():
    """
    Constructs a robust scikit-learn preprocessing pipeline for numerical fitness features.
    - Imputes missing numerical values with median strategy.
    - Standardizes features by removing the mean and scaling to unit variance.
    """
    preprocessor = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    return preprocessor


def prepare_ml_data_arrays(features_list):
    """
    Converts list of feature dictionaries into structured Pandas DataFrame X,
    classification target Series y_class, and regression target Series y_score.
    
    Filters out records with invalid basic demographics (height=None, weight=None, age=None).
    """
    valid_rows = []
    y_class_list = []
    y_score_list = []
    
    for feat in features_list:
        # Check basic data sufficiency
        if not feat.get('is_sufficient_for_prediction'):
            continue
            
        row_dict = {}
        for col in ML_FEATURE_COLUMNS:
            val = feat.get(col)
            # Convert None to NaN for imputer
            row_dict[col] = float(val) if val is not None else np.nan
            
        valid_rows.append(row_dict)
        y_class_list.append(feat.get('ground_truth_category', 'AVERAGE'))
        y_score_list.append(float(feat.get('ground_truth_score', 70.0)))
        
    df_X = pd.DataFrame(valid_rows, columns=ML_FEATURE_COLUMNS)
    y_class = pd.Series(y_class_list, name='fitness_category')
    y_score = pd.Series(y_score_list, name='fitness_score')
    
    return df_X, y_class, y_score
