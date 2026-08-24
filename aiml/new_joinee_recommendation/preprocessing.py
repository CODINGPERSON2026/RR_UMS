from typing import Tuple, Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder

from .config import (
    PREPROCESSOR_FILE,
    LABEL_ENCODER_FILE,
    FEATURE_NAMES_FILE,
    PREPROCESSING_DIR,
    CANONICAL_COMPANIES,
    RANDOM_STATE
)
from .utils import get_logger

logger = get_logger("preprocessing")

CATEGORICAL_FEATURES = [
    "trade",
    "rank",
    "prior_station",
    "previous_unit_1",
    "previous_unit_2",
    "previous_unit_3",
    "most_frequent_unit",
    "most_recent_duty",
    "most_frequent_duty"
]

NUMERICAL_FEATURES = [
    "service_years",
    "age_years",
    "has_course",
    "has_unit_history",
    "previous_unit_count",
    "unique_previous_unit_count",
    "duty_count",
    "total_service_duration_days",
    "avg_posting_duration_days",
    "days_since_last_posting"
]

class CompanyPreprocessor:
    """
    Column transformer and label encoder pipeline for company recommendation modeling.
    """
    def __init__(self):
        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="UNKNOWN")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])

        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])

        self.column_transformer = ColumnTransformer(
            transformers=[
                ("cat", cat_pipeline, CATEGORICAL_FEATURES),
                ("num", num_pipeline, NUMERICAL_FEATURES)
            ],
            remainder="drop"
        )
        self.label_encoder = LabelEncoder()
        self.encoded_feature_names: List[str] = []
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series):
        """Fits feature preprocessor and target encoder."""
        self.column_transformer.fit(X)
        self.label_encoder.fit(y)
        
        try:
            self.encoded_feature_names = list(self.column_transformer.get_feature_names_out())
        except Exception:
            self.encoded_feature_names = []

        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transforms features."""
        # Ensure all expected columns exist in X
        for col in CATEGORICAL_FEATURES:
            if col not in X.columns:
                X[col] = "UNKNOWN"
        for col in NUMERICAL_FEATURES:
            if col not in X.columns:
                X[col] = 0.0

        return self.column_transformer.transform(X)

    def encode_target(self, y: pd.Series) -> np.ndarray:
        """Encodes target strings into integers."""
        return self.label_encoder.transform(y)

    def decode_target(self, y_encoded: np.ndarray) -> np.ndarray:
        """Decodes integer targets back to company strings."""
        return self.label_encoder.inverse_transform(y_encoded)

    def save(self):
        """Persists preprocessor artifacts to disk."""
        PREPROCESSING_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.column_transformer, PREPROCESSOR_FILE)
        joblib.dump(self.label_encoder, LABEL_ENCODER_FILE)
        joblib.dump(self.encoded_feature_names, FEATURE_NAMES_FILE)
        logger.info("Saved preprocessor artifacts successfully.")

    def load(self):
        """Loads preprocessor artifacts from disk."""
        if PREPROCESSOR_FILE.exists() and LABEL_ENCODER_FILE.exists():
            self.column_transformer = joblib.load(PREPROCESSOR_FILE)
            self.label_encoder = joblib.load(LABEL_ENCODER_FILE)
            if FEATURE_NAMES_FILE.exists():
                self.encoded_feature_names = joblib.load(FEATURE_NAMES_FILE)
            self.is_fitted = True
            logger.info("Loaded preprocessor artifacts successfully.")
        return self

def apply_smote(
    X_train_trans: np.ndarray,
    y_train_encoded: np.ndarray,
    label_encoder: LabelEncoder
) -> Tuple[np.ndarray, np.ndarray, Dict[str, int], Dict[str, int]]:
    """
    Applies SMOTE exclusively to the training split to balance class distribution.
    """
    classes = list(label_encoder.classes_)
    unique, counts = np.unique(y_train_encoded, return_counts=True)
    before_dist = {classes[u]: int(c) for u, c in zip(unique, counts)}

    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=RANDOM_STATE)
        X_resampled, y_resampled = smote.fit_resample(X_train_trans, y_train_encoded)
        
        u_res, c_res = np.unique(y_resampled, return_counts=True)
        after_dist = {classes[u]: int(c) for u, c in zip(u_res, c_res)}
        logger.info(f"SMOTE applied: Before={before_dist}, After={after_dist}")
        return X_resampled, y_resampled, before_dist, after_dist
    except Exception as e:
        logger.warning(f"SMOTE application failed or not available ({e}), continuing with raw training set.")
        return X_train_trans, y_train_encoded, before_dist, before_dist
