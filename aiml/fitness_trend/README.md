# UMS — AI/ML Individual Fitness Prediction & Personalized Fitness Report

Comprehensive production documentation for the AI/ML Physical Readiness & Fitness Trend module in the Unit Management System (15 CESR / 15 Corps).

---

## 1. Feature Purpose & Overview

The **AI/ML Individual Fitness Prediction & Personalized Fitness Report** feature analyzes a soldier's vital demographic, physiological, physical testing, sports participation, and medical restriction records in UMS to produce:

1. **Soldier Profile** &mdash; Unified view with standardized heights, weights, ideal benchmarks, BPET/PPT gradings, and medical status.
2. **Body Composition & Physiological Analysis** &mdash; Precise BMI categorization, weight deviation percentage from Indian Army standards, and 5-axis readiness radar.
3. **AI Physical Readiness Prediction** &mdash; Grounded 0-100 Physical Readiness Score, Multi-class Category (`EXCELLENT`, `GOOD`, `AVERAGE`, `NEEDS_IMPROVEMENT`), Prediction Confidence meter, and Explainable Positive/Improvement Factors.
4. **Personalized Tactical Recommendations** &mdash; Energy requirements (kcal), macronutrient distribution, hydration guidance, daily mess meal schedule, and structured exercise tables (`Exercise | Sets | Reps | Duration | Frequency | Intensity`).
5. **Medical Safety Filter** &mdash; Automatic contraindication blocking (e.g. disc/PIVD, knee/ACL, cardiac/hypertension) with safe rehabilitation alternatives and explicit clearance disclaimers.
6. **Goal-based Progression** &mdash; Transparent 30, 60, and 90-day physiological and performance milestone trajectory.
7. **Personalized PDF Report** &mdash; Instant generation of official printable reports via `xhtml2pdf`.

---

## 2. Architecture & Isolation

All feature logic is isolated strictly inside:

```text
aiml/fitness_trend/
├── __init__.py                     # Blueprint export
├── config.py                       # Thresholds, sports maps, & bounds
├── routes.py                       # Flask Blueprint & endpoints (/fitness)
├── api.py                          # Core business logic API
│
├── data/
│   ├── db_loader.py                # Parameterized DB queries across 4 tables
│   ├── data_validator.py           # Source-priority rules & dirty data cleaning
│   └── data_aggregator.py          # Sports aggregation (strictly 1 row per soldier)
│
├── features/
│   ├── bmi.py                      # Division-by-zero guarded BMI engine
│   ├── ideal_weight.py             # Height/age matching vs ideal_weights table
│   ├── sports_features.py          # Category taxonomy & activity scores
│   ├── medical_features.py         # Restriction parsing & contraindication flags
│   └── feature_engineering.py      # Unified feature vector generation
│
├── training/
│   ├── preprocessing.py            # Leakage-free transformation pipeline
│   ├── model_selection.py          # Classifier & regressor candidate definitions
│   ├── evaluate.py                 # Classification & regression metrics
│   └── train.py                    # End-to-end training & persistence pipeline
│
├── models/
│   ├── fitness_classifier_v1.joblib # Active classification model
│   ├── fitness_regressor_v1.joblib  # Active regression model
│   ├── preprocessor_v1.joblib       # Fitted preprocessor pipeline
│   └── metadata_v1.json            # Model schema, training date, metrics
│
├── prediction/
│   ├── predictor.py                # In-memory cached inference engine
│   └── confidence.py               # Prediction confidence & factor explainability
│
├── recommendations/
│   ├── diet.py                     # Dietary & macronutrient engine
│   ├── exercise.py                 # Structured tactical workout generator
│   ├── safety.py                   # Medical restriction blocker & filter
│   └── recommendation_engine.py    # Unified recommendation orchestrator
│
├── progression/
│   └── progression.py              # 30/60/90-day progress estimation engine
│
├── reports/
│   └── fitness_report.py           # xhtml2pdf PDF report compiler
│
├── templates/
│   └── fitness_trend/              # Isolated Jinja2 templates
│
├── static/
│   ├── css/fitness_trend.css       # Tactical theme stylesheet
│   └── js/fitness_trend.js         # Interactive workflow controller & charts
│
├── tests/                          # 26 automated unit & integration tests
├── sql/fitness_trend.sql           # Schema migration script
└── requirements.txt                # Module dependencies
```

---

## 3. Database Tables & Integration

The system integrates four database tables with zero fabrication of data:

1. **`personnel`**: `name`, `army_number`, `rank`, `trade`, `company`, `section`, `date_of_birth`, `date_of_enrollment`, `height`, `weight`, `bpet_grading`, `ppt_grading`, `bpet_date`, `med_cat`, `medical_problem`, `restrictions`.
2. **`weight_info`**: `actual_weight`, `height`, `age`, `status_type` (`shape`/`category`), `category_type` (`temporary`/`permanent`), `restrictions`.
3. **`ideal_weights`**: `height_cm`, `age_range`, `ideal_weight_kg`.
4. **`personnel_sports`**: `sport_type`, `sport_name`.

### Data Cleaning & Source Priority Rules
- **Height**: Sourced from `weight_info.height` if within valid bounds `[130cm, 225cm]`; fallback to `personnel.height` if valid; else flagged as missing.
- **Weight**: Sourced from `weight_info.actual_weight` if within valid bounds `[35kg, 160kg]`; fallback to `personnel.weight` if valid; else flagged as missing.
- **Age**: Calculated from `personnel.date_of_birth` relative to the current date; fallback to `weight_info.age` if valid `[17, 65]`; else flagged.
- **Sports Aggregation**: Aggregated by soldier `army_number` to prevent duplicate ML rows.

---

## 4. Machine Learning Pipeline

### Ground Truth Target Formulation
Physical readiness is derived from military testing standards and official weight limits:
- **BPET Score** (35% weight)
- **PPT Score** (35% weight)
- **Weight / BMI Deviation Compliance** (20% weight)
- **Sports & Athletics Bonus** (10% weight)
- **Medical Category Penalty** (deductions for LMC / restrictions)

### Model Selection & Evaluation
- **Classification Candidate Models Evaluated**: `RandomForestClassifier`, `GradientBoostingClassifier`, `XGBClassifier`, `LogisticRegression`.
- **Selected Classifier**: `GradientBoostingClassifier`
- **Regression Candidate Models Evaluated**: `RandomForestRegressor`, `GradientBoostingRegressor`, `RidgeRegressor`, `XGBRegressor`.
- **Selected Regressor**: `RidgeRegressor`
- **Data Leakage Prevention**: Preprocessor transformations (median imputer and standard scaler) are fitted exclusively on the 80% training split.

---

## 5. Medical Safety & Contraindications

The engine enforces strict medical safety filters:
- **Spine / Back / PIVD**: Automatically blocks heavy deadlifts, squats, and forward bending; substitutes with core stabilization (Bird-Dog, McGill curl-ups) and swimming.
- **Knee / ACL / Meniscus**: Blocks deep squats, box jumps, and sprints; substitutes with straight leg raises and glute bridges.
- **Cardiovascular / Hypertension**: Blocks maximal 1RM straining and valsalva maneuvers.

---

## 6. How to Run, Test, and Retrain

### Running the Test Suite
```bash
umsvenv\Scripts\python.exe -m unittest discover -s aiml/fitness_trend/tests -p "test_*.py"
```

### Retraining the Models
- **Via CLI**:
  ```bash
  umsvenv\Scripts\python.exe aiml/fitness_trend/training/train.py
  ```
- **Via Web UI**: Click **Retrain Model** in the top navigation bar of `/fitness`.

### Accessing the Feature in UMS
1. Log in to UMS (`/admin_login`).
2. Click **AI Fitness Prediction** in the sidebar navigation or navigate to `/fitness/`.
3. Search for any soldier by Army Number (e.g. `JC393919L` or `15744604X`).
4. View the 6-stage workflow and download the personalized PDF report.
