from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODELS_DIR = BASE_DIR / "models"
PREPROCESSING_DIR = ARTIFACTS_DIR / "preprocessing"
METRICS_DIR = ARTIFACTS_DIR / "metrics"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

# Model artifact directories
RF_MODEL_DIR = MODELS_DIR / "random_forest"
XGB_MODEL_DIR = MODELS_DIR / "xgboost"

# Specific artifact files
BEST_MODEL_FILE = MODELS_DIR / "best_model.joblib"
BEST_MODEL_INFO_FILE = MODELS_DIR / "best_model_info.json"
MODEL_METADATA_FILE = ARTIFACTS_DIR / "model_metadata.json"
RETRAINING_LOG_FILE = REPORTS_DIR / "retraining_log.json"
PREPROCESSOR_FILE = PREPROCESSING_DIR / "preprocessor.joblib"
LABEL_ENCODER_FILE = PREPROCESSING_DIR / "label_encoder.joblib"
FEATURE_NAMES_FILE = PREPROCESSING_DIR / "feature_names.joblib"

# Model and training configuration
CANONICAL_COMPANIES = ["3 Coy", "Comn Coy", "HQ Coy"]
RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5
AUTO_RETRAIN_THRESHOLD_RECORDS = 10
