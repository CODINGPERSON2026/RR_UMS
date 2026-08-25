from typing import Dict, Any, Tuple, Optional, List
import os
from datetime import date
import pandas as pd
import numpy as np

from db_config import get_db_connection
from .config import (
    CANONICAL_COMPANIES,
    SYNTHETIC_PERSONNEL_FILE,
    SYNTHETIC_UNITS_FILE
)
from .utils import get_logger, parse_date_safe, sanitize_text

logger = get_logger("data_loader")

def normalize_company(val: Any) -> Optional[str]:
    """
    Normalizes historical company strings to canonical target classes:
    'HQ Coy', 'Comn Coy', or '3 Coy'.
    """
    if val is None or pd.isna(val):
        return None
    
    s = str(val).strip().upper()
    
    # HQ Coy mappings
    if s in ["HQ COY", "HQ COMPANY", "HQ", "HQCOMPANY", "HQ_COY", "HEADQUARTER", "HEADQUARTERS"]:
        return "HQ Coy"
    
    # Comn Coy mappings (including historical 1 Coy and 2 Coy amalgamated into Comn)
    if s in [
        "COMN COY", "COMN COMPANY", "COMN", "COMN_COY",
        "1 COY", "1 COMPANY", "1COY", "1_COY",
        "2 COY", "2 COMPANY", "2COY", "2_COY"
    ]:
        return "Comn Coy"
    
    # 3 Coy mappings
    if s in ["3 COY", "3 COMPANY", "3COY", "3_COY", "3"]:
        return "3 Coy"
    
    # Fallback partial matching
    if "HQ" in s:
        return "HQ Coy"
    if "COMN" in s or "1 COY" in s or "2 COY" in s:
        return "Comn Coy"
    if "3" in s and ("COY" in s or "COMPANY" in s):
        return "3 Coy"
        
    return None

def clean_personnel_dataframe(df: pd.DataFrame, source_name: str = "raw") -> pd.DataFrame:
    """
    Cleans, standardizes and validates personnel records:
    - Standardizes text columns
    - Validates and parses dates (clamps future dates)
    - Normalizes company targets
    """
    if df.empty:
        return df

    cleaned = df.copy()

    # Text columns
    for col in ["name", "army_number", "rank", "trade", "prior_station", "detailed_course", "company"]:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].astype(str).str.strip()
            cleaned[col] = cleaned[col].replace(["nan", "None", "NAN", "NONE", "null", "NULL", "<NA>"], np.nan)

    # Date columns - sanitize and prevent invalid/future dates
    for d_col in ["date_of_enrollment", "date_of_birth", "date_of_tos", "date_of_tors"]:
        if d_col in cleaned.columns:
            cleaned[d_col] = cleaned[d_col].apply(lambda v: parse_date_safe(v, allow_future=False))

    # Normalize target company
    if "company" in cleaned.columns:
        cleaned["target_company"] = cleaned["company"].apply(normalize_company)
    else:
        cleaned["target_company"] = None

    logger.info(f"Cleaned {len(cleaned)} personnel records from {source_name}")
    return cleaned

def clean_units_dataframe(df: pd.DataFrame, source_name: str = "raw") -> pd.DataFrame:
    """
    Cleans, standardizes and validates units_served records:
    - Standardizes unit names and duties
    - Parses from_date and to_date
    - Ensures from_date <= to_date <= today
    """
    if df.empty:
        return df

    cleaned = df.copy()

    if "army_number" in cleaned.columns:
        cleaned["army_number"] = cleaned["army_number"].astype(str).str.strip()
        cleaned["army_number"] = cleaned["army_number"].replace(["nan", "None", "NAN", "NONE", "null", "NULL"], np.nan)

    if "unit" in cleaned.columns:
        cleaned["unit"] = cleaned["unit"].astype(str).str.strip()
        cleaned["unit"] = cleaned["unit"].replace(["nan", "None", "NAN", "NONE", "null", "NULL"], np.nan)

    if "duty_performed" in cleaned.columns:
        cleaned["duty_performed"] = cleaned["duty_performed"].astype(str).str.strip()
        cleaned["duty_performed"] = cleaned["duty_performed"].replace(["nan", "None", "NAN", "NONE", "null", "NULL"], np.nan)

    # Parse and validate dates
    today = date.today()
    if "from_date" in cleaned.columns:
        cleaned["from_date_parsed"] = cleaned["from_date"].apply(lambda v: parse_date_safe(v, allow_future=False))
    else:
        cleaned["from_date_parsed"] = None

    if "to_date" in cleaned.columns:
        cleaned["to_date_parsed"] = cleaned["to_date"].apply(lambda v: parse_date_safe(v, allow_future=False))
    else:
        cleaned["to_date_parsed"] = None

    # Fix reversed date ranges (swap if from_date > to_date)
    def sanitize_range(row):
        f = row.get("from_date_parsed")
        t = row.get("to_date_parsed")
        if f and t and f > t:
            # swap
            return t, f
        return f, t

    if "from_date_parsed" in cleaned.columns and "to_date_parsed" in cleaned.columns:
        swapped = cleaned.apply(sanitize_range, axis=1)
        cleaned["from_date"] = [s[0] for s in swapped]
        cleaned["to_date"] = [s[1] for s in swapped]
    
_CACHED_RAW_DATA: Optional[Tuple[pd.DataFrame, pd.DataFrame]] = None

def load_raw_data(force_reload: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads and merges raw personnel and units_served tables directly from:
    1. MySQL Database (active troop records)
    2. CSV Datasets (synthetic_personnel_1000.csv and synthetic_units_served.csv)
    Performs deduplication and rigorous data cleaning.
    Caches in-memory for fast repeated inference.
    """
    global _CACHED_RAW_DATA
    if _CACHED_RAW_DATA is not None and not force_reload:
        return _CACHED_RAW_DATA[0].copy(), _CACHED_RAW_DATA[1].copy()

    db_personnel_df = pd.DataFrame()
    db_units_df = pd.DataFrame()


    # 1. Load from MySQL Database
    conn = get_db_connection()
    if conn:
        try:
            query_personnel = """
                SELECT 
                    id, name, army_number, `rank`, trade, 
                    date_of_enrollment, date_of_birth, date_of_tos, date_of_tors,
                    prior_station, detailed_course, company, created_at
                FROM personnel
            """
            db_personnel_df = pd.read_sql(query_personnel, conn)
            db_personnel_df["data_source"] = "database"

            query_units = """
                SELECT 
                    id, personnel_id, army_number, sr_no, unit, 
                    from_date, to_date, duty_performed
                FROM units_served
                ORDER BY personnel_id, from_date ASC, sr_no ASC
            """
            db_units_df = pd.read_sql(query_units, conn)
            db_units_df["data_source"] = "database"
            logger.info(f"Loaded {len(db_personnel_df)} personnel and {len(db_units_df)} units from MySQL DB.")
        except Exception as e:
            logger.error(f"Error loading raw data from MySQL: {e}", exc_info=True)
        finally:
            conn.close()
    else:
        logger.warning("Could not connect to MySQL DB. Will rely on CSV dataset files.")

    # 2. Load from CSV Datasets
    csv_personnel_df = pd.DataFrame()
    csv_units_df = pd.DataFrame()

    if SYNTHETIC_PERSONNEL_FILE.exists():
        try:
            csv_personnel_df = pd.read_csv(SYNTHETIC_PERSONNEL_FILE)
            csv_personnel_df["data_source"] = "synthetic_csv"
            # Assign synthetic negative IDs to avoid collisions with DB auto-increment IDs
            csv_personnel_df["id"] = [-10000 - i for i in range(len(csv_personnel_df))]
            logger.info(f"Loaded {len(csv_personnel_df)} personnel records from CSV ({SYNTHETIC_PERSONNEL_FILE.name}).")
        except Exception as e:
            logger.error(f"Error reading {SYNTHETIC_PERSONNEL_FILE}: {e}")

    if SYNTHETIC_UNITS_FILE.exists():
        try:
            csv_units_df = pd.read_csv(SYNTHETIC_UNITS_FILE)
            csv_units_df["data_source"] = "synthetic_csv"
            csv_units_df["id"] = [-10000 - i for i in range(len(csv_units_df))]
            logger.info(f"Loaded {len(csv_units_df)} units_served records from CSV ({SYNTHETIC_UNITS_FILE.name}).")
        except Exception as e:
            logger.error(f"Error reading {SYNTHETIC_UNITS_FILE}: {e}")

    # 3. Clean both sources
    db_p_clean = clean_personnel_dataframe(db_personnel_df, "MySQL DB")
    csv_p_clean = clean_personnel_dataframe(csv_personnel_df, "CSV Dataset")

    db_u_clean = clean_units_dataframe(db_units_df, "MySQL DB")
    csv_u_clean = clean_units_dataframe(csv_units_df, "CSV Dataset")

    # 4. Merge Personnel with Deduplication (Database records take priority if army_number duplicates)
    if not db_p_clean.empty and not csv_p_clean.empty:
        existing_army_nos = set(db_p_clean["army_number"].dropna().unique())
        # Filter CSV to keep non-duplicates
        csv_filtered = csv_p_clean[~csv_p_clean["army_number"].isin(existing_army_nos)]
        combined_personnel = pd.concat([db_p_clean, csv_filtered], ignore_index=True)
    elif not db_p_clean.empty:
        combined_personnel = db_p_clean
    else:
        combined_personnel = csv_p_clean

    # 5. Merge Units
    if not db_u_clean.empty and not csv_u_clean.empty:
        combined_units = pd.concat([db_u_clean, csv_u_clean], ignore_index=True)
    elif not db_u_clean.empty:
        combined_units = db_u_clean
    else:
        combined_units = csv_u_clean

    logger.info(
        f"Combined dataset ready: Total Personnel={len(combined_personnel)} (DB: {len(db_p_clean)}, CSV: {len(csv_p_clean)}), "
        f"Total Units Served={len(combined_units)} (DB: {len(db_u_clean)}, CSV: {len(csv_u_clean)})"
    )

    _CACHED_RAW_DATA = (combined_personnel.copy(), combined_units.copy())
    return combined_personnel, combined_units


def load_single_personnel(personnel_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[pd.DataFrame]]:
    """
    Loads a single personnel record and its unit serving history from MySQL.
    """
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to connect to MySQL database.")
        return None, None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                id, name, army_number, `rank`, trade, 
                date_of_enrollment, date_of_birth, date_of_tos, date_of_tors,
                prior_station, detailed_course, company, created_at
            FROM personnel
            WHERE id = %s
        """, (personnel_id,))
        personnel_row = cursor.fetchone()
        cursor.close()

        if not personnel_row:
            return None, None

        army_no = personnel_row.get("army_number")
        query_units = """
            SELECT 
                id, personnel_id, army_number, sr_no, unit, 
                from_date, to_date, duty_performed
            FROM units_served
            WHERE personnel_id = %s OR (army_number IS NOT NULL AND army_number != '' AND army_number = %s)
            ORDER BY from_date ASC, sr_no ASC
        """
        units_df = pd.read_sql(query_units, conn, params=(personnel_id, army_no))

        return personnel_row, units_df
    except Exception as e:
        logger.error(f"Error loading personnel ID {personnel_id}: {e}", exc_info=True)
        return None, None
    finally:
        conn.close()

def profile_dataset(personnel_df: pd.DataFrame, units_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generates summary dataset profile metrics for analytics.
    """
    if len(personnel_df) == 0:
        return {}

    df = personnel_df.copy()
    if "target_company" not in df.columns:
        df["target_company"] = df["company"].apply(normalize_company)
    eligible = df[df["target_company"].isin(CANONICAL_COMPANIES)]

    p_ids_with_units = set(units_df["personnel_id"].dropna().unique())
    if "army_number" in units_df:
        p_ids_with_units.update(units_df["army_number"].dropna().unique())

    with_history = eligible[eligible["id"].isin(p_ids_with_units) | eligible["army_number"].isin(p_ids_with_units)]

    coy_dist = eligible["target_company"].value_counts().to_dict()
    trade_dist = eligible["trade"].dropna().astype(str).str.strip().str.upper().value_counts().head(10).to_dict()

    db_count = int((eligible.get("data_source") == "database").sum()) if "data_source" in eligible.columns else 0
    csv_count = int((eligible.get("data_source") == "synthetic_csv").sum()) if "data_source" in eligible.columns else 0

    return {
        "total_personnel": len(personnel_df),
        "total_eligible": len(eligible),
        "database_records": db_count,
        "synthetic_csv_records": csv_count,
        "records_with_trade": int(eligible["trade"].notna().sum()),
        "personnel_with_unit_history": len(with_history),
        "personnel_without_unit_history": len(eligible) - len(with_history),
        "total_unit_records": len(units_df),
        "company_distribution": {c: int(coy_dist.get(c, 0)) for c in CANONICAL_COMPANIES},
        "top_trades": trade_dist,
        "canonical_classes": CANONICAL_COMPANIES
    }

