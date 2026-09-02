"""
Configuration and constants for AI/ML Fitness Trend & Personalized Fitness Report.
All thresholds, sports mappings, and model parameters are defined here.
"""

import os

# Base paths
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(MODULE_DIR, 'models')
REPORTS_DIR = os.path.join(MODULE_DIR, 'reports')
STATIC_DIR = os.path.join(MODULE_DIR, 'static')
TEMPLATES_DIR = os.path.join(MODULE_DIR, 'templates')

# Create directories if not existing
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Model configuration
DEFAULT_MODEL_VERSION = "v1"
CLASSIFIER_MODEL_PATH = os.path.join(MODELS_DIR, f"fitness_classifier_{DEFAULT_MODEL_VERSION}.joblib")
REGRESSOR_MODEL_PATH = os.path.join(MODELS_DIR, f"fitness_regressor_{DEFAULT_MODEL_VERSION}.joblib")
PREPROCESSOR_PATH = os.path.join(MODELS_DIR, f"preprocessor_{DEFAULT_MODEL_VERSION}.joblib")
METADATA_PATH = os.path.join(MODELS_DIR, f"metadata_{DEFAULT_MODEL_VERSION}.json")

# Retraining threshold (minimum new records to trigger automated retrain)
RETRAIN_NEW_RECORDS_THRESHOLD = 20

# Physical readiness score grading thresholds (0 - 100 scale)
FITNESS_CATEGORIES = {
    "EXCELLENT": {"min_score": 85, "label": "Excellent Readiness", "color": "#10b981", "badge": "success"},
    "GOOD": {"min_score": 70, "label": "Good Fitness", "color": "#3b82f6", "badge": "primary"},
    "AVERAGE": {"min_score": 50, "label": "Satisfactory / Average", "color": "#f59e0b", "badge": "warning"},
    "NEEDS_IMPROVEMENT": {"min_score": 0, "label": "Needs Improvement / At-Risk", "color": "#ef4444", "badge": "danger"}
}

# Standard Military BPET / PPT score conversions
BPET_SCORE_MAP = {
    'EX': 100,
    'EXCELLENT': 100,
    'GOOD': 80,
    'SAT': 60,
    'SATISFACTORY': 60,
    'LMC': 40,
    'A2P': 40,
    'FAIL': 30
}

PPT_SCORE_MAP = {
    'EX': 100,
    'EXCELLENT': 100,
    'GOOD': 80,
    'SAT': 60,
    'SATISFACTORY': 60,
    'LMC': 40,
    'A2P': 40,
    'FAIL': 30
}

# Standard BMI Classifications
BMI_CATEGORIES = [
    {"max": 18.5, "category": "Underweight", "color": "#3b82f6"},
    {"max": 24.9, "category": "Normal (Ideal)", "color": "#10b981"},
    {"max": 29.9, "category": "Overweight", "color": "#f59e0b"},
    {"max": 34.9, "category": "Obese Class I", "color": "#f97316"},
    {"max": 999.0, "category": "Obese Class II / Severe", "color": "#ef4444"}
]

# Configurable Sports Category Mapping
SPORTS_CATEGORY_MAP = {
    'volleyball': 'team',
    'football': 'team',
    'basketball': 'team',
    'cricket': 'team',
    'kabaddi': 'team',
    'kabadi': 'team',
    'handball': 'team',
    'hockey': 'team',
    'swimming': 'water_endurance',
    'running': 'endurance',
    'cross_country': 'endurance',
    'athletics': 'endurance',
    'cycling': 'endurance',
    'weightlifting': 'strength',
    'powerlifting': 'strength',
    'gym': 'strength',
    'crossfit': 'strength',
    'boxing': 'combat',
    'martialartboxing': 'combat',
    'wrestling': 'combat',
    'judo': 'combat',
    'karate': 'combat',
    'taekwondo': 'combat',
    'badminton': 'individual',
    'lawn_tennis': 'individual',
    'tennis': 'individual',
    'table_tennis': 'individual',
    'squash': 'individual'
}

# Sanity bounds for soldier data validation
VALID_BOUNDS = {
    'min_height_cm': 130.0,
    'max_height_cm': 225.0,
    'min_weight_kg': 35.0,
    'max_weight_kg': 160.0,
    'min_age_years': 17,
    'max_age_years': 65
}

# Medical restriction keywords and high-risk medical contraindications
RESTRICTION_KEYWORDS = {
    'spine_back': ['pivd', 'back pain', 'disc', 'lumbar', 'sciatica', 'l4-l5', 'l3-l4', 'l5-s1', 'forward bending'],
    'knee_lower_limb': ['acl', 'meniscus', 'knee', 'tibia', 'fibula', 'ankle', 'fracture', 'ligament', 'patella'],
    'shoulder_upper_limb': ['shoulder', 'scaphoid', 'rotator', 'dislocation', 'wrist', 'elbow'],
    'cardiovascular': ['hypertension', 'hyper tension', 'bp', 'blood pressure', 'htn', 'cardiac', 'primary htn'],
    'respiratory': ['asthma', 'bronchial', 'bronchitis', 'tb', 'tuberculosis', 'respiratory'],
    'systemic_general': ['hepatitis', 'adjustment disorder', 'diabetes', 'cns', 'psychiatric']
}
