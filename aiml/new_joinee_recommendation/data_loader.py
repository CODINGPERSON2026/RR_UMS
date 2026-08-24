from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
from db_config import get_db_connection
from .config import CANONICAL_COMPANIES
from .utils import get_logger

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

def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads raw personnel and units_served tables directly from UMS MySQL database.
    """
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to connect to MySQL database.")
        return pd.DataFrame(), pd.DataFrame()

    try:
        query_personnel = """
            SELECT 
                id, name, army_number, `rank`, trade, 
                date_of_enrollment, date_of_birth, date_of_tos, date_of_tors,
                prior_station, detailed_course, company, created_at
            FROM personnel
        """
        personnel_df = pd.read_sql(query_personnel, conn)

        query_units = """
            SELECT 
                id, personnel_id, army_number, sr_no, unit, 
                from_date, to_date, duty_performed
            FROM units_served
            ORDER BY personnel_id, from_date ASC, sr_no ASC
        """
        units_df = pd.read_sql(query_units, conn)

        return personnel_df, units_df
    except Exception as e:
        logger.error(f"Error loading raw data from MySQL: {e}", exc_info=True)
        return pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()

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
            WHERE personnel_id = %s OR army_number = %s
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
    df["target_company"] = df["company"].apply(normalize_company)
    eligible = df[df["target_company"].isin(CANONICAL_COMPANIES)]

    p_ids_with_units = set(units_df["personnel_id"].dropna().unique())
    if "army_number" in units_df:
        p_ids_with_units.update(units_df["army_number"].dropna().unique())

    with_history = eligible[eligible["id"].isin(p_ids_with_units) | eligible["army_number"].isin(p_ids_with_units)]

    coy_dist = eligible["target_company"].value_counts().to_dict()
    trade_dist = eligible["trade"].dropna().astype(str).str.strip().str.upper().value_counts().head(10).to_dict()

    return {
        "total_personnel": len(personnel_df),
        "total_eligible": len(eligible),
        "records_with_trade": int(eligible["trade"].notna().sum()),
        "personnel_with_unit_history": len(with_history),
        "personnel_without_unit_history": len(eligible) - len(with_history),
        "total_unit_records": len(units_df),
        "company_distribution": {c: int(coy_dist.get(c, 0)) for c in CANONICAL_COMPANIES},
        "top_trades": trade_dist,
        "canonical_classes": CANONICAL_COMPANIES
    }
