"""
Comparative validation script: Approach A (Recency Only) vs Approach B (Complete History & Aggregates)
Evaluates Random Forest and XGBoost across 5-fold Stratified Cross-Validation on the 2,000-sample dataset.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import xgboost as xgb

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aiml.ai_new_joinee_recommendation.preprocessing import (
    load_dataset_and_engineer_features,
    PERSONNEL_CSV,
    UNITS_CSV,
    calculate_tenure_days,
    UNIT_TYPE_KEYWORDS,
    DUTY_DOMAIN_KEYWORDS,
    normalize_company_name
)

def extract_features_approach_a(units_history):
    """Approach A: Uses ONLY most recent unit and most recent duty."""
    features = {}
    valid_units = [u for u in (units_history or []) if (u.get("unit") or u.get("unit_name"))]
    if not valid_units:
        for k in ["latest_tenure_days"] + list(UNIT_TYPE_KEYWORDS.keys()) + list(DUTY_DOMAIN_KEYWORDS.keys()):
            features[k] = 0.0
        return features

    latest_u = valid_units[0]
    u_name = str(latest_u.get("unit") or "").strip().upper()
    duty = str(latest_u.get("duty_performed") or "").strip().upper()
    features["latest_tenure_days"] = calculate_tenure_days(latest_u.get("from_date"), latest_u.get("to_date"))

    for u_type, kws in UNIT_TYPE_KEYWORDS.items():
        features[u_type] = 1.0 if any(kw in u_name for kw in kws) else 0.0

    for d_domain, kws in DUTY_DOMAIN_KEYWORDS.items():
        features[d_domain] = 1.0 if any(kw in duty.lower() for kw in kws) else 0.0

    return features

def run_experiment():
    print("=" * 70)
    print("EXPERIMENT: APPROACH A (RECENCY ONLY) VS APPROACH B (FULL HISTORY)")
    print("=" * 70)

    p_df = pd.read_csv(PERSONNEL_CSV)
    u_df = pd.read_csv(UNITS_CSV)

    personnel_postings = {}
    for _, row in u_df.iterrows():
        p_id = int(row['personnel_id'])
        if p_id not in personnel_postings:
            personnel_postings[p_id] = []
        personnel_postings[p_id].append({
            'unit': row['unit'],
            'from_date': row['from_date'],
            'to_date': row['to_date'],
            'duty_performed': row['duty_performed']
        })

    y_coy = p_df['company'].apply(normalize_company_name)

    # 1. Approach A Dataset
    rows_a = [extract_features_approach_a(personnel_postings.get(int(p_row['id']), [])) for _, p_row in p_df.iterrows()]
    X_a = pd.DataFrame(rows_a)

    # 2. Approach B Dataset (Full Features from Preprocessing)
    X_b, y_b, _, _, _ = load_dataset_and_engineer_features()

    print(f"Approach A feature dimensions: {X_a.shape}")
    print(f"Approach B feature dimensions: {X_b.shape}")

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for approach_name, X_data in [("Approach A (Recency Only)", X_a), ("Approach B (Complete History & Densities)", X_b)]:
        accs = []
        macro_f1s = []
        for train_idx, val_idx in skf.split(X_data, y_coy):
            X_tr, X_val = X_data.iloc[train_idx], X_data.iloc[val_idx]
            y_tr, y_val = y_coy.iloc[train_idx], y_coy.iloc[val_idx]

            rf = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42)
            rf.fit(X_tr, y_tr)
            preds = rf.predict(X_val)

            accs.append(accuracy_score(y_val, preds))
            macro_f1s.append(f1_score(y_val, preds, average="macro"))

        print(f"\n--- {approach_name} 5-Fold Cross-Validation ---")
        print(f"Mean Accuracy: {np.mean(accs)*100:.2f}% (+/- {np.std(accs)*100:.2f}%)")
        print(f"Mean Macro F1: {np.mean(macro_f1s)*100:.2f}% (+/- {np.std(macro_f1s)*100:.2f}%)")

if __name__ == "__main__":
    run_experiment()
