"""
Model candidate definitions for Fitness Classification and Regression.
"""

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


def get_classifier_candidates():
    """
    Returns a dictionary of candidate classification models to evaluate during training.
    """
    candidates = {
        'RandomForestClassifier': RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            min_samples_split=4,
            class_weight='balanced',
            random_state=42
        ),
        'GradientBoostingClassifier': GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=42
        ),
        'LogisticRegression': LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        )
    }
    
    if HAS_XGBOOST:
        candidates['XGBClassifier'] = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=42,
            eval_metric='mlogloss'
        )
        
    return candidates


def get_regressor_candidates():
    """
    Returns a dictionary of candidate regression models to evaluate during training.
    """
    candidates = {
        'RandomForestRegressor': RandomForestRegressor(
            n_estimators=120,
            max_depth=8,
            min_samples_split=4,
            random_state=42
        ),
        'GradientBoostingRegressor': GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=42
        ),
        'RidgeRegressor': Ridge(alpha=1.0, random_state=42)
    }
    
    if HAS_XGBOOST:
        candidates['XGBRegressor'] = XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=42
        )
        
    return candidates
