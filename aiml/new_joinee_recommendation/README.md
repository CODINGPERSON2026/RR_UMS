# AI New Joinee Company Recommendation System

Self-contained machine learning system for recommending company assignments (`HQ Coy`, `Comn Coy`, `3 Coy`) for new joinees in the Unit Management System (UMS).

## Architecture

- **Target Variable**: `personnel.company` normalized to canonical classes (`HQ Coy`, `Comn Coy`, `3 Coy`).
- **Feature Engineering**:
  - Soldier attributes: `trade`, `rank`, `service_years`, `age_years`, `prior_station`, `has_unit_history`.
  - Historical sequence from `units_served`: sequential units (`previous_unit_1`, `previous_unit_2`, `previous_unit_3`), aggregate units count, `most_frequent_unit`, `most_recent_duty`, `most_frequent_duty`, tenure durations.
- **Leakage Prevention**: `company` is strictly excluded from features. SMOTE is applied exclusively to training splits.
- **Models Trained**:
  - Random Forest Classifier (`RandomForestClassifier`)
  - XGBoost Multi-Class Classifier (`XGBClassifier`)
- **Evaluation**: Stratified 5-Fold Cross-Validation, Top-1 & Top-2 Accuracy, Macro F1, Weighted F1, Multiclass ROC-AUC, Confusion Matrix.
- **Auto-Retraining**: Automatically checks database every prediction/request cycle; triggers safe mutex-locked retraining when $\ge 50$ new eligible records are added.

## Structure

```text
aiml/new_joinee_recommendation/
├── __init__.py
├── config.py
├── data_loader.py
├── feature_engineering.py
├── preprocessing.py
├── train.py
├── evaluate.py
├── predict.py
├── retrain.py
├── recommendation_service.py
├── analytics.py
├── utils.py
├── routes.py
├── models/
│   ├── random_forest/
│   └── xgboost/
└── artifacts/
    ├── preprocessing/
    ├── metrics/
    └── reports/
```

## Running Retraining from CLI

```bash
python -m aiml.new_joinee_recommendation.train
```
