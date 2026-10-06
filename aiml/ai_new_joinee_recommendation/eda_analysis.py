"""
Exploratory Data Analysis (EDA) Script for AI NEW ARRIVAL RECOMMENDATION
Analyzes historical database relationships across Company, Section, Trade, Rank, Postings, and Duties.
"""

import sys
import os
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from db_config import get_db_connection

conn = get_db_connection()
cur = conn.cursor(dictionary=True)

cur.execute("""
    SELECT id, army_number, name, `rank`, trade, company, section, 
           date_of_enrollment, prior_station, worked_it, computer_knowledge, 
           it_literature, civ_qualifications, med_cat 
    FROM personnel
""")
personnel_rows = cur.fetchall()

cur.execute("""
    SELECT personnel_id, army_number, unit, from_date, to_date, duty_performed 
    FROM units_served
    ORDER BY personnel_id, sr_no
""")
units_rows = cur.fetchall()

cur.close()
conn.close()

p_df = pd.DataFrame(personnel_rows)
u_df = pd.DataFrame(units_rows)

print("=" * 60)
print(f"TOTAL PERSONNEL RECORDS: {len(p_df)}")
print(f"TOTAL UNITS_SERVED POSTINGS: {len(u_df)}")
print(f"UNIQUE PERSONNEL WITH POSTING HISTORY: {u_df['personnel_id'].nunique()}")
print(f"PERSONNEL WITH 0 RECORDED POSTINGS (FRESH/DIRECT): {len(p_df) - u_df['personnel_id'].nunique()}")
print("=" * 60)

print("\n=== 1. COMPANY DISTRIBUTION ===")
print(p_df['company'].value_counts(dropna=False))

print("\n=== 2. SECTION DISTRIBUTION (RAW) ===")
print(p_df['section'].value_counts(dropna=False))

print("\n=== 3. TOP 25 TRADES / APPOINTMENTS (RAW) ===")
print(p_df['trade'].value_counts(dropna=False).head(25))

print("\n=== 4. RANK DISTRIBUTION ===")
print(p_df['rank'].value_counts(dropna=False))

print("\n=== 5. CROSS-TAB: RANK vs COMPANY ===")
print(pd.crosstab(p_df['rank'].fillna('MISSING'), p_df['company'].fillna('MISSING'), margins=True))

print("\n=== 6. CROSS-TAB: SECTION vs COMPANY ===")
print(pd.crosstab(p_df['section'].fillna('MISSING'), p_df['company'].fillna('MISSING'), margins=True))

# Merge postings with personnel company/section
u_merged = u_df.merge(p_df[['id', 'company', 'section', 'rank', 'trade']], left_on='personnel_id', right_on='id', how='inner')

print("\n=== 7. TOP 20 UNITS SERVED vs CURRENT COMPANY ===")
top_units = u_merged['unit'].value_counts().head(20).index
print(pd.crosstab(u_merged[u_merged['unit'].isin(top_units)]['unit'], u_merged['company'], margins=True))

print("\n=== 8. TOP 20 DUTIES PERFORMED vs CURRENT COMPANY ===")
top_duties = u_merged['duty_performed'].value_counts().head(20).index
print(pd.crosstab(u_merged[u_merged['duty_performed'].isin(top_duties)]['duty_performed'], u_merged['company'], margins=True))

print("\n=== 9. TOP 20 DUTIES PERFORMED vs CURRENT SECTION ===")
print(pd.crosstab(u_merged[u_merged['duty_performed'].isin(top_duties)]['duty_performed'], u_merged['section'].fillna('MISSING'), margins=True))

print("\n=== 10. MISSING VALUES SUMMARY ===")
print(p_df.isnull().sum())
