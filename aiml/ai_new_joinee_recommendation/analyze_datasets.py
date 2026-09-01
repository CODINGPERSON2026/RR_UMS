"""
Comprehensive Statistical & Exploratory Data Analysis for AI New Joinee Recommendation
Analyzes both the real MySQL database tables (personnel, units_served) and the historical CSV datasets.
Calculates empirical transition distributions and pattern combinations.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Ensure workspace root is in path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from db_config import get_db_connection

def run_comprehensive_eda():
    print("=" * 80)
    print("AI NEW JOINEE RECOMMENDATION: COMPREHENSIVE DATA & PATTERN ANALYSIS")
    print("=" * 80)

    # -------------------------------------------------------------
    # 1. DATABASE INSPECTION
    # -------------------------------------------------------------
    print("\n" + "=" * 40)
    print("1. LIVE DATABASE ANALYSIS (`personnel` & `units_served`)")
    print("=" * 40)

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT id, army_number, name, `rank`, trade, company, section,
               date_of_enrollment, prior_station, worked_it, computer_knowledge, it_literature
        FROM personnel
    """)
    db_p_rows = cur.fetchall()
    db_p_df = pd.DataFrame(db_p_rows)

    cur.execute("""
        SELECT id as unit_entry_id, personnel_id, army_number, unit, from_date, to_date, duty_performed
        FROM units_served
    """)
    db_u_rows = cur.fetchall()
    db_u_df = pd.DataFrame(db_u_rows)

    cur.close()
    conn.close()

    print(f"Total Personnel in Database: {len(db_p_df)}")
    print(f"Total Units Served Records in Database: {len(db_u_df)}")
    print(f"Unique Personnel IDs with Postings in DB: {db_u_df['personnel_id'].nunique()}")
    print(f"Unique Units in DB: {db_u_df['unit'].nunique()}")
    print(f"Unique Duties in DB: {db_u_df['duty_performed'].nunique()}")
    print(f"DB Company Distribution:\n{db_p_df['company'].value_counts(dropna=False)}")

    # -------------------------------------------------------------
    # 2. CSV DATASET INSPECTION
    # -------------------------------------------------------------
    print("\n" + "=" * 40)
    print("2. CSV HISTORICAL DATASET ANALYSIS")
    print("=" * 40)

    csv_dir = os.path.join(os.path.dirname(__file__), "datasets")
    p_csv_path = os.path.join(csv_dir, "personnel_test_2000.csv")
    u_csv_path = os.path.join(csv_dir, "units_served_test_2000.csv")

    csv_p_df = pd.read_csv(p_csv_path)
    csv_u_df = pd.read_csv(u_csv_path)

    print(f"Dataset 1: {os.path.basename(p_csv_path)} -> {len(csv_p_df)} rows, {len(csv_p_df.columns)} columns")
    print(f"Dataset 2: {os.path.basename(u_csv_path)} -> {len(csv_u_df)} rows, {len(csv_u_df.columns)} columns")
    print(f"Unique Army Numbers in CSV: {csv_p_df['army_number'].nunique()}")
    print(f"Unique personnel_id in units_served CSV: {csv_u_df['personnel_id'].nunique()}")
    print(f"Unique Units in CSV: {csv_u_df['unit'].nunique()}")
    print(f"Unique Duties in CSV: {csv_u_df['duty_performed'].nunique()}")
    print(f"CSV Company Distribution:\n{csv_p_df['company'].value_counts(dropna=False)}")

    # -------------------------------------------------------------
    # 3. DB vs CSV CONSISTENCY AUDIT
    # -------------------------------------------------------------
    print("\n" + "=" * 40)
    print("3. DATABASE VS CSV CONSISTENCY AUDIT")
    print("=" * 40)
    print(f"Database Personnel count: {len(db_p_df)} vs CSV Personnel count: {len(csv_p_df)}")
    print(f"Database Units Served count: {len(db_u_df)} vs CSV Units Served count: {len(csv_u_df)}")
    
    # Check matching army numbers
    db_army_nos = set(db_p_df['army_number'].astype(str).str.strip().str.upper())
    csv_army_nos = set(csv_p_df['army_number'].astype(str).str.strip().str.upper())
    overlap = db_army_nos.intersection(csv_army_nos)
    print(f"Army Numbers in DB: {len(db_army_nos)}, in CSV: {len(csv_army_nos)}, Overlapping: {len(overlap)}")

    # -------------------------------------------------------------
    # 4. JOIN & STATISTICAL TRANSITION MATRICES (HISTORICAL LEARNING)
    # -------------------------------------------------------------
    print("\n" + "=" * 40)
    print("4. HISTORICAL TRANSITION PATTERNS")
    print("=" * 40)

    merged = csv_u_df.merge(csv_p_df, left_on='personnel_id', right_on='id', suffixes=('_unit', '_pers'))
    print(f"Total Merged Historical Records for Learning: {len(merged)}")

    # Pattern A: Previous Unit -> Company
    print("\n--- Pattern A: Previous Unit -> Company Conditional Distribution (%) ---")
    unit_coy_ct = pd.crosstab(merged['unit'], merged['company'])
    unit_coy_pct = pd.crosstab(merged['unit'], merged['company'], normalize='index') * 100
    print(unit_coy_pct.round(1).head(15))

    # Pattern B: Previous Duty -> Company
    print("\n--- Pattern B: Previous Duty -> Company Conditional Distribution (%) ---")
    duty_coy_pct = pd.crosstab(merged['duty_performed'], merged['company'], normalize='index') * 100
    print(duty_coy_pct.round(1).head(15))

    # Pattern C: Previous Unit + Previous Duty -> Company
    print("\n--- Pattern C: Previous Unit + Previous Duty -> Company Combinations (Sample Top 20) ---")
    unit_duty_coy = merged.groupby(['unit', 'duty_performed', 'company']).size().reset_index(name='count')
    unit_duty_total = merged.groupby(['unit', 'duty_performed']).size().reset_index(name='total')
    unit_duty_comb = unit_duty_coy.merge(unit_duty_total, on=['unit', 'duty_performed'])
    unit_duty_comb['prob_pct'] = (unit_duty_comb['count'] / unit_duty_comb['total'] * 100).round(1)
    print(unit_duty_comb.sort_values(by='count', ascending=False).head(20).to_string(index=False))

    # Pattern D: Previous Duty -> Section
    print("\n--- Pattern D: Previous Duty -> Section Conditional Distribution (%) (Top 12 Duties) ---")
    top_duties = merged['duty_performed'].value_counts().head(12).index
    duty_sec_pct = pd.crosstab(merged[merged['duty_performed'].isin(top_duties)]['duty_performed'], merged['section'], normalize='index') * 100
    print(duty_sec_pct.round(1).to_string())

    # Pattern E: Previous Duty -> Trade / Appointment
    print("\n--- Pattern E: Previous Duty -> Personnel Trade (Sample Top 20) ---")
    duty_trade = merged.groupby(['duty_performed', 'trade']).size().reset_index(name='count')
    print(duty_trade.sort_values(by='count', ascending=False).head(20).to_string(index=False))

    # Pattern F: Previous Unit + Rank -> Company
    if 'rank' in merged.columns:
        print("\n--- Pattern F: Previous Unit + Rank -> Company (Sample Top 15) ---")
        unit_rank_coy = merged.groupby(['unit', 'rank', 'company']).size().reset_index(name='count')
        print(unit_rank_coy.sort_values(by='count', ascending=False).head(15).to_string(index=False))

    print("\n" + "=" * 80)
    print("EXPLORATORY DATA ANALYSIS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_comprehensive_eda()
