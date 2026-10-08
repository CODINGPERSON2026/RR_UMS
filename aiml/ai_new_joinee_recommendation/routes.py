"""
Flask Blueprint & REST API Routes for AI NEW ARRIVAL RECOMMENDATION (Unit 15 CESR)
Enforces Hierarchical Placement, Role-Based Access Control (CO, Adjutant, 2IC),
and Trade-Free Supervised Recommendation Pipeline.
"""

import os
import sys
import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response

# Ensure workspace root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from db_config import get_db_connection
from middleware import require_login
from aiml.ai_new_joinee_recommendation.position_mapping import (
    VALID_COMPANIES,
    VALID_DB_COMPANIES,
    UNIT_15_CESR_STRUCTURE,
    normalize_company_name,
    to_db_company_name,
    to_display_company_name,
    get_all_companies,
    get_sections_for_company,
    get_positions_for_section,
    get_positions_for_company,
    get_section_for_position,
    is_position_valid_for_company,
    is_valid_hierarchy,
    get_full_hierarchy_dict
)
from aiml.ai_new_joinee_recommendation.recommendation import (
    recommend_placement,
    load_model_artifacts
)
from aiml.ai_new_joinee_recommendation.explainability import generate_domain_and_contrastive_explainability
from aiml.ai_new_joinee_recommendation.training import run_training_pipeline

company_rec_bp = Blueprint(
    "company_rec_bp",
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Allowed executive roles for recommendations
AUTHORIZED_DECISION_ROLES = ["CO", "ADJUTANT", "2IC", "ADMIN", "COMMANDING OFFICER", "SUPER ADMIN"]
AUTHORIZED_VIEW_ROLES = ["CO", "ADJUTANT", "2IC", "ADMIN", "COMMANDING OFFICER", "SUPER ADMIN"]

# Rank synonym mapping for normalization & queries
RANK_SYNONYM_MAP = {
    "COL": ["COL", "COLONEL", "COL."],
    "COLONEL": ["COL", "COLONEL", "COL."],
    "LT COL": ["LT COL", "LT. COL", "LIEUTENANT COLONEL", "LT-COL"],
    "LIEUTENANT COLONEL": ["LT COL", "LT. COL", "LIEUTENANT COLONEL", "LT-COL"],
    "MAJ": ["MAJ", "MAJOR", "MAJ."],
    "MAJOR": ["MAJ", "MAJOR", "MAJ."],
    "CAPT": ["CAPT", "CAPTAIN", "CAPT."],
    "CAPTAIN": ["CAPT", "CAPTAIN", "CAPT."],
    "LT": ["LT", "LIEUTENANT", "LT."],
    "LIEUTENANT": ["LT", "LIEUTENANT", "LT."],
    "SUB MAJ": ["SUB MAJ", "SUB. MAJ", "SUBEDAR MAJOR", "SUB/MAJ", "SUB-MAJ"],
    "SUBEDAR MAJOR": ["SUB MAJ", "SUB. MAJ", "SUBEDAR MAJOR", "SUB/MAJ", "SUB-MAJ"],
    "SUB": ["SUB", "SUBEDAR", "SUB."],
    "SUBEDAR": ["SUB", "SUBEDAR", "SUB."],
    "NB SUB": ["NB SUB", "NB. SUB", "NAIB SUBEDAR", "NB/SUB", "NB-SUB", "NAIB-SUBEDAR"],
    "NAIB SUBEDAR": ["NB SUB", "NB. SUB", "NAIB SUBEDAR", "NB/SUB", "NB-SUB", "NAIB-SUBEDAR"],
    "RHM": ["RHM", "REGIMENTAL HAVILDAR MAJOR"],
    "BHM": ["BHM", "BATTERY HAVILDAR MAJOR", "BATTALION HAVILDAR MAJOR"],
    "CHM": ["CHM", "COMPANY HAVILDAR MAJOR"],
    "CQMH": ["CQMH", "COMPANY QUARTERMASTER HAVILDAR"],
    "HAV": ["HAV", "HAVILDAR", "HAV."],
    "HAVILDAR": ["HAV", "HAVILDAR", "HAV."],
    "L HAV": ["L HAV", "L/HAV", "LHAV", "LOC HAV", "L-HAV", "L/ HAV"],
    "LOC HAV": ["L HAV", "L/HAV", "LHAV", "LOC HAV", "L-HAV", "L/ HAV"],
    "LHAV": ["L HAV", "L/HAV", "LHAV", "LOC HAV", "L-HAV", "L/ HAV"],
    "NK": ["NK", "NAIK", "NK."],
    "NAIK": ["NK", "NAIK", "NK."],
    "L NK": ["L NK", "L/NK", "LNK", "LOC NK", "L-NK", "L/ NK"],
    "LOC NK": ["L NK", "L/NK", "LNK", "LOC NK", "L-NK", "L/ NK"],
    "LNK": ["L NK", "L/NK", "LNK", "LOC NK", "L-NK", "L/ NK"],
    "CFN": ["CFN", "CRAFTSMAN", "CFN."],
    "CRAFTSMAN": ["CFN", "CRAFTSMAN", "CFN."],
    "SIGNAL MAN": ["SIGNAL MAN", "SIGNALMAN", "SIGMN", "SIG MAN", "SIGMN."],
    "SIGMN": ["SIGNAL MAN", "SIGNALMAN", "SIGMN", "SIG MAN", "SIGMN."],
    "AGNIVEER": ["AGNIVEER", "AGV", "AGV."],
    "AGV": ["AGNIVEER", "AGV", "AGV."],
}

_TABLE_ENSURED = False

def ensure_recommendations_table(cursor, conn=None):
    """Auto-create ai_new_joinee_recommendations table and safely add missing columns if they don't exist (idempotent)."""
    global _TABLE_ENSURED
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_new_joinee_recommendations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                personnel_id INT DEFAULT NULL,
                army_number VARCHAR(50) DEFAULT NULL,
                name VARCHAR(200) DEFAULT NULL,
                `rank` VARCHAR(100) DEFAULT NULL,
                trade VARCHAR(200) DEFAULT NULL,
                recommended_company VARCHAR(100) DEFAULT NULL,
                confidence_score VARCHAR(50) DEFAULT NULL,
                recommendation_percentage FLOAT DEFAULT NULL,
                recommended_position VARCHAR(200) DEFAULT NULL,
                position_confidence VARCHAR(50) DEFAULT NULL,
                confidence_type VARCHAR(100) DEFAULT 'ml',
                model_version VARCHAR(100) DEFAULT NULL,
                probabilities_json LONGTEXT DEFAULT NULL,
                match_reasons_json LONGTEXT DEFAULT NULL,
                shap_json LONGTEXT DEFAULT NULL,
                units_history_json LONGTEXT DEFAULT NULL,
                final_company VARCHAR(100) DEFAULT NULL,
                final_position VARCHAR(200) DEFAULT NULL,
                decision_type VARCHAR(50) DEFAULT 'pending',
                decision_remarks TEXT DEFAULT NULL,
                decided_by VARCHAR(200) DEFAULT NULL,
                decided_at DATETIME DEFAULT NULL,
                updated_by VARCHAR(200) DEFAULT NULL,
                updated_by_role VARCHAR(100) DEFAULT NULL,
                updated_by_user_id VARCHAR(100) DEFAULT NULL,
                created_at DATETIME DEFAULT NOW(),
                updated_at DATETIME DEFAULT NOW()
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        if conn:
            conn.commit()

        # Idempotently ensure missing audit, feature, and metric columns exist in existing database tables
        cols_to_check = [
            ("personnel_id", "INT DEFAULT NULL"),
            ("army_number", "VARCHAR(50) DEFAULT NULL"),
            ("name", "VARCHAR(200) DEFAULT NULL"),
            ("`rank`", "VARCHAR(100) DEFAULT NULL"),
            ("trade", "VARCHAR(200) DEFAULT NULL"),
            ("recommended_company", "VARCHAR(100) DEFAULT NULL"),
            ("confidence_score", "VARCHAR(50) DEFAULT NULL"),
            ("recommendation_percentage", "FLOAT DEFAULT NULL"),
            ("recommended_position", "VARCHAR(200) DEFAULT NULL"),
            ("position_confidence", "VARCHAR(50) DEFAULT NULL"),
            ("confidence_type", "VARCHAR(100) DEFAULT 'ml'"),
            ("model_version", "VARCHAR(100) DEFAULT NULL"),
            ("probabilities_json", "LONGTEXT DEFAULT NULL"),
            ("match_reasons_json", "LONGTEXT DEFAULT NULL"),
            ("shap_json", "LONGTEXT DEFAULT NULL"),
            ("units_history_json", "LONGTEXT DEFAULT NULL"),
            ("final_company", "VARCHAR(100) DEFAULT NULL"),
            ("final_position", "VARCHAR(200) DEFAULT NULL"),
            ("decision_type", "VARCHAR(50) DEFAULT 'pending'"),
            ("decision_remarks", "TEXT DEFAULT NULL"),
            ("decided_by", "VARCHAR(200) DEFAULT NULL"),
            ("decided_at", "DATETIME DEFAULT NULL"),
            ("updated_by", "VARCHAR(200) DEFAULT NULL"),
            ("updated_by_role", "VARCHAR(100) DEFAULT NULL"),
            ("updated_by_user_id", "VARCHAR(100) DEFAULT NULL"),
            ("created_at", "DATETIME DEFAULT NOW()"),
            ("updated_at", "DATETIME DEFAULT NOW()"),
            ("adjutant_action", "VARCHAR(50) DEFAULT NULL"),
            ("adjutant_company", "VARCHAR(100) DEFAULT NULL"),
            ("adjutant_section", "VARCHAR(100) DEFAULT NULL"),
            ("adjutant_position", "VARCHAR(200) DEFAULT NULL"),
            ("adjutant_remarks", "TEXT DEFAULT NULL"),
            ("adjutant_by", "VARCHAR(200) DEFAULT NULL"),
            ("adjutant_at", "DATETIME DEFAULT NULL"),
            ("two_ic_updated", "INT DEFAULT 0"),
            ("two_ic_message", "TEXT DEFAULT NULL"),
            ("final_section", "VARCHAR(100) DEFAULT NULL"),
        ]
        for col_name, col_def in cols_to_check:
            try:
                cursor.execute(f"ALTER TABLE ai_new_joinee_recommendations ADD COLUMN {col_name} {col_def}")
                if conn:
                    conn.commit()
            except Exception:
                pass

        _TABLE_ENSURED = True
    except Exception as e:
        print(f"Notice: Could not ensure recommendations table: {e}")


def get_current_authenticated_user(user: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Get authenticated user with fallback to Flask session when JWT token cookie is omitted."""
    if user:
        return user
    try:
        u = require_login()
        if u:
            return u
    except Exception:
        pass

    try:
        from flask import session
        if session:
            role = session.get("role") or session.get("user_role")
            username = session.get("username") or session.get("user_id")
            user_id = str(session.get("user_id") or session.get("id") or "1")
            if role or username:
                return {
                    "role": role or "CO",
                    "username": username or "Officer",
                    "user_id": user_id
                }
    except Exception:
        pass
    return None


def check_executive_authorization(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if authenticated user has CO, Adjutant, or 2IC decision authority."""
    auth_user = get_current_authenticated_user(user)
    if not auth_user:
        return False
    role = str(auth_user.get("role", "")).strip().upper()

    if role in AUTHORIZED_DECISION_ROLES:
        return True

    import re
    if re.search(r'\b(CO|ADJUTANT|2IC)\b', role):
        if not re.search(r'\b(NCO|JCO|ONCO)\b', role):
            return True

    return False


def check_view_authorization(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if authenticated user can view insights tables and dashboards."""
    auth_user = get_current_authenticated_user(user)
    if not auth_user:
        return False
    role = str(auth_user.get("role", "")).strip().upper()
    if role in AUTHORIZED_VIEW_ROLES:
        return True
    return check_executive_authorization(auth_user)


def check_predict_authorization(user: Optional[Dict[str, Any]] = None) -> bool:
    """Check if authenticated user can run AI New Joinee prediction (1coyonco, 2coyonco)."""
    auth_user = get_current_authenticated_user(user)
    if not auth_user:
        return False
    role = str(auth_user.get("role", "")).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    return role in ["1coyonco", "2coyonco", "onco", "coyonco", "admin", "co", "2ic", "adjutant", "commandingofficer"]


def sync_dues_in_recommendations(cursor=None, conn=None) -> int:
    """
    Scans `dues_in` (incoming joinees) and automatically calculates & persists
    AI recommendations into `ai_new_joinee_recommendations` for any joinee not yet stored.
    """
    close_at_end = False
    if cursor is None:
        c_conn = get_db_connection()
        if not c_conn:
            return 0
        cursor = c_conn.cursor(dictionary=True)
        conn = c_conn
        close_at_end = True

    try:
        ensure_recommendations_table(cursor, conn)

        # Get all dues_in joinees
        cursor.execute("SELECT * FROM dues_in ORDER BY id DESC")
        dues_rows = cursor.fetchall() or []

        if not dues_rows:
            if close_at_end:
                cursor.close()
                conn.close()
            return 0

        # Get existing army_numbers and names in ai_new_joinee_recommendations
        cursor.execute("SELECT army_number, name FROM ai_new_joinee_recommendations")
        existing_recs = cursor.fetchall() or []
        existing_army_nos = {str(r["army_number"]).strip().upper() for r in existing_recs if r.get("army_number")}
        existing_names = {str(r["name"]).strip().upper() for r in existing_recs if r.get("name")}

        added_count = 0
        for d in dues_rows:
            army_no = str(d.get("army_number") or "").strip().upper()
            name = str(d.get("name") or "").strip()
            name_upper = name.upper()

            # Skip if already exists in recommendations table
            if (army_no and army_no in existing_army_nos) or (name_upper and name_upper in existing_names):
                continue

            rank = str(d.get("rank")).strip() if d.get("rank") is not None else None
            trade = str(d.get("trade")).strip() if d.get("trade") is not None else None
            unit = str(d.get("unit") or "").strip()
            date_of_move = d.get("date_of_move")
            move_str = ""
            if date_of_move:
                try:
                    move_str = date_of_move.strftime("%d/%m/%Y") if hasattr(date_of_move, "strftime") else str(date_of_move)
                except Exception:
                    move_str = str(date_of_move)

            units_history = []
            if unit:
                units_history.append({
                    "unit": unit,
                    "from_date": "",
                    "to_date": move_str,
                    "duty_performed": trade or ""
                })

            # Generate placement recommendation via recommendation engine
            rec = recommend_placement(
                units_history=units_history,
                is_fresh_joinee=(len(units_history) == 0),
                army_number=army_no,
                name=name,
                rank=rank or "",
                prior_station=unit
            )

            rec_coy = normalize_company_name(rec.get("recommended_company"))
            conf_score = str(rec["confidence_score"]) if rec.get("confidence_score") is not None else None
            rec_pct = float(rec["recommendation_percentage"]) if rec.get("recommendation_percentage") is not None else None
            rec_pos = rec.get("recommended_position") or ""
            pos_conf = str(rec["position_confidence"]) if rec.get("position_confidence") is not None else None
            conf_type = rec.get("confidence_type") or "ml"
            model_ver = rec.get("model_version") or ""

            prob_json = json.dumps(rec.get("probabilities") or {})
            reasons_json = json.dumps(rec.get("match_reasons") or [])
            shap_json = json.dumps(rec.get("shap_explanation") or {})
            units_json = json.dumps(units_history)

            insert_sql = """
                INSERT INTO ai_new_joinee_recommendations (
                    personnel_id, army_number, name, `rank`, trade,
                    recommended_company, confidence_score, recommendation_percentage,
                    recommended_position, position_confidence, confidence_type, model_version,
                    probabilities_json, match_reasons_json, shap_json, units_history_json,
                    decision_type, created_at, updated_at
                ) VALUES (
                    NULL, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    'pending', NOW(), NOW()
                )
            """
            cursor.execute(insert_sql, (
                army_no, name, rank, trade,
                rec_coy, conf_score, rec_pct,
                rec_pos, pos_conf, conf_type, model_ver,
                prob_json, reasons_json, shap_json, units_json
            ))
            if conn:
                conn.commit()

            if army_no:
                existing_army_nos.add(army_no)
            if name_upper:
                existing_names.add(name_upper)
            added_count += 1

        if close_at_end:
            cursor.close()
            conn.close()

        return added_count
    except Exception as e:
        print(f"Error in sync_dues_in_recommendations: {e}")
        if close_at_end and conn:
            try:
                conn.close()
            except Exception:
                pass
        return 0


# =============================================================================
# 1. HIERARCHY & LOOKUP ROUTES
# =============================================================================

@company_rec_bp.route("/api/ai/company-recommendation/hierarchy", methods=["GET"])
def api_get_hierarchy():
    """
    Return the centralized canonical company -> section -> position hierarchy.
    Used by frontend dropdowns to enforce dynamic dependent hierarchy without duplication.
    """
    # Flatten section -> trades mapping across all companies
    section_trades_map = {}
    for coy, sec_dict in UNIT_15_CESR_STRUCTURE.items():
        for sec, trades in sec_dict.items():
            section_trades_map[sec] = trades

    return jsonify({
        "success": True,
        "hierarchy": UNIT_15_CESR_STRUCTURE,
        "companies": get_all_companies(),
        "sections": list(section_trades_map.keys()),
        "section_trades_map": section_trades_map,
        "company_sections_map": {
            coy: get_sections_for_company(coy) for coy in get_all_companies()
        },
        "company_positions_map": {
            coy: get_positions_for_company(coy) for coy in get_all_companies()
        }
    })


def clean_soldier_name_for_search(raw_name: str) -> str:
    """Helper to strip common military rank prefixes if user types rank into name input."""
    if not raw_name:
        return ""
    import re
    cleaned = re.sub(r'^(SEP|HAV|NK|L/NK|L\s*NK|CHM|CQMH|RHM|NB\s*SUB|SUB|SUB\s*MAJ|CFN|RECT|SIGMAN|SIGMN|SM|LT|CAPT|MAJ)\.?\s+', '', raw_name.strip(), flags=re.IGNORECASE)
    return cleaned.strip()


@company_rec_bp.route("/api/ai/company-recommendation/lookup-personnel", methods=["GET"])
def api_lookup_personnel():
    """
    Lookup personnel details by Army Number or Name to auto-fill AI recommendation form.
    Searches both `personnel` (and its `units_served`) and `dues_in` (new joinees).
    """
    army_no = request.args.get("army_number", "").strip()
    name = request.args.get("name", "").strip()
    query = request.args.get("query", "").strip()
    search_term = army_no or name or query
    clean_name = clean_soldier_name_for_search(name or search_term)

    if not search_term:
        return jsonify({"success": False, "message": "Army number or Name required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        row = None
        matched_source = None

        # 1. Search in personnel table
        if army_no:
            cursor.execute("""
                SELECT id, army_number, name, `rank`, trade, 
                       date_of_enrollment, company, section, prior_station, worked_unit_tenure
                FROM personnel 
                WHERE UPPER(TRIM(army_number)) = UPPER(%s) 
                LIMIT 1
            """, (army_no,))
            row = cursor.fetchone()
        elif name:
            cursor.execute("""
                SELECT id, army_number, name, `rank`, trade, 
                       date_of_enrollment, company, section, prior_station, worked_unit_tenure
                FROM personnel 
                WHERE UPPER(TRIM(name)) = UPPER(%s) 
                   OR UPPER(TRIM(name)) = UPPER(%s)
                   OR UPPER(name) LIKE UPPER(%s)
                   OR UPPER(name) LIKE UPPER(%s)
                ORDER BY CASE 
                    WHEN UPPER(TRIM(name)) = UPPER(%s) THEN 1 
                    WHEN UPPER(TRIM(name)) = UPPER(%s) THEN 2 
                    WHEN UPPER(name) LIKE UPPER(%s) THEN 3
                    ELSE 4 END, id ASC
                LIMIT 1
            """, (name, clean_name, f"%{name}%", f"%{clean_name}%", name, clean_name, f"{clean_name}%"))
            row = cursor.fetchone()
        else:
            cursor.execute("""
                SELECT id, army_number, name, `rank`, trade, 
                       date_of_enrollment, company, section, prior_station, worked_unit_tenure
                FROM personnel 
                WHERE UPPER(TRIM(army_number)) = UPPER(%s) 
                   OR UPPER(TRIM(name)) = UPPER(%s) 
                   OR UPPER(TRIM(name)) = UPPER(%s)
                   OR UPPER(name) LIKE UPPER(%s)
                   OR UPPER(name) LIKE UPPER(%s)
                ORDER BY CASE 
                    WHEN UPPER(TRIM(army_number)) = UPPER(%s) THEN 1 
                    WHEN UPPER(TRIM(name)) = UPPER(%s) THEN 2 
                    WHEN UPPER(TRIM(name)) = UPPER(%s) THEN 3 
                    ELSE 4 END, id ASC
                LIMIT 1
            """, (search_term, search_term, clean_name, f"%{search_term}%", f"%{clean_name}%", search_term, search_term, clean_name))
            row = cursor.fetchone()

        units_list = []
        if row:
            matched_source = "personnel"
            # Query units_served
            cursor.execute("""
                SELECT id, unit, from_date, to_date, duty_performed
                FROM units_served
                WHERE personnel_id = %s OR UPPER(TRIM(army_number)) = UPPER(%s)
                ORDER BY sr_no ASC, id ASC
            """, (row["id"], row["army_number"]))
            unit_rows = cursor.fetchall() or []
            for u in unit_rows:
                f_date = ""
                if u.get("from_date"):
                    try:
                        f_date = u["from_date"].strftime("%d/%m/%Y") if hasattr(u["from_date"], "strftime") else str(u["from_date"])
                    except Exception:
                        f_date = str(u["from_date"])
                t_date = ""
                if u.get("to_date"):
                    try:
                        t_date = u["to_date"].strftime("%d/%m/%Y") if hasattr(u["to_date"], "strftime") else str(u["to_date"])
                    except Exception:
                        t_date = str(u["to_date"])
                units_list.append({
                    "unit": (u.get("unit") or "").strip(),
                    "from_date": f_date,
                    "to_date": t_date,
                    "duty_performed": (u.get("duty_performed") or "").strip()
                })

            # If units_served has no records, check dues_in for this soldier
            if not units_list:
                cursor.execute("""
                    SELECT unit, date_of_move, trade FROM dues_in
                    WHERE UPPER(TRIM(army_number)) = UPPER(%s) 
                       OR UPPER(TRIM(name)) = UPPER(%s)
                       OR UPPER(TRIM(name)) = UPPER(%s)
                    LIMIT 1
                """, (row["army_number"], row["name"], clean_soldier_name_for_search(row["name"])))
                d = cursor.fetchone()
                if d and d.get("unit"):
                    m_date = ""
                    if d.get("date_of_move"):
                        try:
                            m_date = d["date_of_move"].strftime("%d/%m/%Y") if hasattr(d["date_of_move"], "strftime") else str(d["date_of_move"])
                        except Exception:
                            m_date = str(d["date_of_move"])
                    units_list.append({
                        "unit": d["unit"].strip(),
                        "from_date": "",
                        "to_date": m_date,
                        "duty_performed": (row.get("trade") or d.get("trade") or "GENERAL").strip()
                    })

            # If still empty, check worked_unit_tenure
            if not units_list and row.get("worked_unit_tenure"):
                wut = str(row["worked_unit_tenure"]).strip()
                if wut and wut.upper() not in ["-", "NONE", "NULL", ""]:
                    import re
                    parts = [p.strip() for p in re.split(r'[,;]+', wut) if p.strip()]
                    for p in parts:
                        units_list.append({
                            "unit": p,
                            "from_date": "",
                            "to_date": "",
                            "duty_performed": (row.get("trade") or "GENERAL").strip()
                        })

            # If still empty, check prior_station
            if not units_list and row.get("prior_station"):
                ps = str(row["prior_station"]).strip()
                if ps.upper() not in ["NO", "NONE", "NULL", "YES", ""]:
                    units_list.append({
                        "unit": ps,
                        "from_date": "",
                        "to_date": "",
                        "duty_performed": (row.get("trade") or "GENERAL").strip()
                    })

        # 2. If not found in personnel, search in dues_in (new joinees entering unit)
        if not row:
            if army_no:
                cursor.execute("""
                    SELECT army_number, name, `rank`, trade, unit, date_of_move
                    FROM dues_in
                    WHERE UPPER(TRIM(army_number)) = UPPER(%s)
                    LIMIT 1
                """, (army_no,))
                d_row = cursor.fetchone()
            elif name:
                cursor.execute("""
                    SELECT army_number, name, `rank`, trade, unit, date_of_move
                    FROM dues_in
                    WHERE UPPER(TRIM(name)) = UPPER(%s) 
                       OR UPPER(TRIM(name)) = UPPER(%s)
                       OR UPPER(name) LIKE UPPER(%s)
                       OR UPPER(name) LIKE UPPER(%s)
                    ORDER BY CASE 
                        WHEN UPPER(TRIM(name)) = UPPER(%s) THEN 1 
                        WHEN UPPER(TRIM(name)) = UPPER(%s) THEN 2 
                        ELSE 3 END, id ASC
                    LIMIT 1
                """, (name, clean_name, f"%{name}%", f"%{clean_name}%", name, clean_name))
                d_row = cursor.fetchone()
            else:
                cursor.execute("""
                    SELECT army_number, name, `rank`, trade, unit, date_of_move
                    FROM dues_in
                    WHERE UPPER(TRIM(army_number)) = UPPER(%s)
                       OR UPPER(TRIM(name)) = UPPER(%s)
                       OR UPPER(TRIM(name)) = UPPER(%s)
                       OR UPPER(name) LIKE UPPER(%s)
                       OR UPPER(name) LIKE UPPER(%s)
                    ORDER BY CASE 
                        WHEN UPPER(TRIM(army_number)) = UPPER(%s) THEN 1 
                        WHEN UPPER(TRIM(name)) = UPPER(%s) THEN 2 
                        WHEN UPPER(TRIM(name)) = UPPER(%s) THEN 3 
                        ELSE 4 END, id ASC
                    LIMIT 1
                """, (search_term, search_term, clean_name, f"%{search_term}%", f"%{clean_name}%", search_term, search_term, clean_name))
                d_row = cursor.fetchone()

            if d_row:
                matched_source = "dues_in"
                m_date = ""
                if d_row.get("date_of_move"):
                    try:
                        m_date = d_row["date_of_move"].strftime("%d/%m/%Y") if hasattr(d_row["date_of_move"], "strftime") else str(d_row["date_of_move"])
                    except Exception:
                        m_date = str(d_row["date_of_move"])

                if d_row.get("unit"):
                    units_list.append({
                        "unit": d_row["unit"].strip(),
                        "from_date": "",
                        "to_date": m_date,
                        "duty_performed": (d_row.get("trade") or "GENERAL").strip()
                    })

                row = {
                    "id": None,
                    "army_number": d_row["army_number"],
                    "name": d_row["name"],
                    "rank": d_row["rank"],
                    "trade": d_row.get("trade") or "",
                    "date_of_enrollment": "",
                    "company": "",
                    "section": "",
                    "prior_station": d_row.get("unit") or ""
                }

        cursor.close()
        conn.close()

        if row:
            enroll_str = ""
            if row.get("date_of_enrollment"):
                try:
                    enroll_str = row["date_of_enrollment"].strftime("%d/%m/%Y") if hasattr(row["date_of_enrollment"], "strftime") else str(row["date_of_enrollment"])
                except Exception:
                    enroll_str = str(row["date_of_enrollment"])

            return jsonify({
                "success": True,
                "found": True,
                "source": matched_source,
                "data": {
                    "id": row.get("id"),
                    "army_number": row.get("army_number") or "",
                    "name": row.get("name") or "",
                    "rank": row.get("rank") or "",
                    "trade": row.get("trade") or "",
                    "date_of_enrollment": enroll_str,
                    "company": row.get("company") or "",
                    "section": row.get("section") or "",
                    "prior_station": row.get("prior_station") or "",
                    "worked_unit_tenure": row.get("worked_unit_tenure") or "",
                    "units_served": units_list,
                    "is_fresh": len(units_list) == 0
                }
            })
        else:
            return jsonify({
                "success": True,
                "found": False,
                "message": "Personnel not found in database"
            })
    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return jsonify({"success": False, "error": str(e)}), 500


@company_rec_bp.route("/api/ai/company-recommendation/search-personnel", methods=["GET"])
def api_search_personnel():
    """
    Search personnel from both `personnel` and `dues_in` for live dropdown suggestions.
    Query params: q (search text, e.g. "amr" or "amit"), limit (default 20)
    """
    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 20))

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        results = []
        seen_army_nos = set()
        clean_q = clean_soldier_name_for_search(q)

        # 1. Search in personnel table
        if q:
            cursor.execute("""
                SELECT id, army_number, name, `rank`, trade, company, section, 
                       date_of_enrollment, prior_station, worked_unit_tenure
                FROM personnel
                WHERE UPPER(name) LIKE UPPER(%s) 
                   OR UPPER(name) LIKE UPPER(%s)
                   OR UPPER(army_number) LIKE UPPER(%s)
                ORDER BY CASE 
                    WHEN UPPER(name) = UPPER(%s) THEN 1
                    WHEN UPPER(name) LIKE UPPER(%s) THEN 2
                    WHEN UPPER(army_number) = UPPER(%s) THEN 3
                    ELSE 4 END, name ASC
                LIMIT %s
            """, (f"%{q}%", f"%{clean_q}%", f"%{q}%", q, f"{clean_q}%", q, limit))
        else:
            cursor.execute("""
                SELECT id, army_number, name, `rank`, trade, company, section, 
                       date_of_enrollment, prior_station, worked_unit_tenure
                FROM personnel
                ORDER BY id DESC
                LIMIT %s
            """, (limit,))
        p_rows = cursor.fetchall() or []

        for r in p_rows:
            ano = (r.get("army_number") or "").strip().upper()
            if ano:
                seen_army_nos.add(ano)

            # Query units_served for this soldier
            cursor.execute("""
                SELECT unit, from_date, to_date, duty_performed
                FROM units_served
                WHERE personnel_id = %s OR UPPER(TRIM(army_number)) = UPPER(%s)
                ORDER BY sr_no ASC, id ASC
            """, (r["id"], ano))
            u_rows = cursor.fetchall() or []
            units = []
            for u in u_rows:
                f_d = u["from_date"].strftime("%d/%m/%Y") if u.get("from_date") and hasattr(u["from_date"], "strftime") else str(u.get("from_date") or "")
                t_d = u["to_date"].strftime("%d/%m/%Y") if u.get("to_date") and hasattr(u["to_date"], "strftime") else str(u.get("to_date") or "")
                units.append({
                    "unit": (u.get("unit") or "").strip(),
                    "from_date": f_d,
                    "to_date": t_d,
                    "duty_performed": (u.get("duty_performed") or r.get("trade") or "GENERAL").strip()
                })

            if not units and r.get("worked_unit_tenure"):
                wut = str(r["worked_unit_tenure"]).strip()
                if wut and wut.upper() not in ["-", "NONE", "NULL", ""]:
                    import re
                    parts = [p.strip() for p in re.split(r'[,;]+', wut) if p.strip()]
                    for p in parts:
                        units.append({
                            "unit": p,
                            "from_date": "",
                            "to_date": "",
                            "duty_performed": (r.get("trade") or "GENERAL").strip()
                        })

            enroll_str = ""
            if r.get("date_of_enrollment"):
                try:
                    enroll_str = r["date_of_enrollment"].strftime("%d/%m/%Y") if hasattr(r["date_of_enrollment"], "strftime") else str(r["date_of_enrollment"])
                except Exception:
                    enroll_str = str(r["date_of_enrollment"])

            prev_u = units[0]["unit"] if units else (r.get("prior_station") if r.get("prior_station") not in ["No", "Yes", "None", None] else "")

            results.append({
                "id": r["id"],
                "army_number": r["army_number"] or "",
                "name": r["name"] or "",
                "rank": r["rank"] or "",
                "trade": r.get("trade") or "",
                "company": r.get("company") or "",
                "section": r.get("section") or "",
                "date_of_enrollment": enroll_str,
                "prior_station": r.get("prior_station") or "",
                "source": "personnel",
                "previous_unit": prev_u,
                "units_served": units,
                "is_fresh": len(units) == 0
            })

        # 2. Search dues_in table
        remaining_limit = max(5, limit - len(results))
        if q:
            cursor.execute("""
                SELECT id, army_number, name, `rank`, trade, unit, date_of_move
                FROM dues_in
                WHERE UPPER(name) LIKE UPPER(%s) 
                   OR UPPER(name) LIKE UPPER(%s)
                   OR UPPER(army_number) LIKE UPPER(%s)
                ORDER BY CASE 
                    WHEN UPPER(name) = UPPER(%s) THEN 1
                    WHEN UPPER(name) LIKE UPPER(%s) THEN 2
                    WHEN UPPER(army_number) = UPPER(%s) THEN 3
                    ELSE 4 END, name ASC
                LIMIT %s
            """, (f"%{q}%", f"%{clean_q}%", f"%{q}%", q, f"{clean_q}%", q, remaining_limit))
        else:
            cursor.execute("""
                SELECT id, army_number, name, `rank`, trade, unit, date_of_move
                FROM dues_in
                ORDER BY id DESC
                LIMIT %s
            """, (remaining_limit,))
        d_rows = cursor.fetchall() or []

        for d in d_rows:
            ano = (d.get("army_number") or "").strip().upper()
            if ano and ano in seen_army_nos:
                continue
            seen_army_nos.add(ano)

            m_d = d["date_of_move"].strftime("%d/%m/%Y") if d.get("date_of_move") and hasattr(d["date_of_move"], "strftime") else str(d.get("date_of_move") or "")
            d_units = []
            if d.get("unit"):
                d_units.append({
                    "unit": d["unit"].strip(),
                    "from_date": "",
                    "to_date": m_d,
                    "duty_performed": (d.get("trade") or "GENERAL").strip()
                })

            results.append({
                "id": None,
                "army_number": d["army_number"] or "",
                "name": d["name"] or "",
                "rank": d["rank"] or "",
                "trade": d.get("trade") or "",
                "company": "",
                "section": "",
                "date_of_enrollment": "",
                "prior_station": d.get("unit") or "",
                "source": "dues_in",
                "previous_unit": d.get("unit") or "",
                "units_served": d_units,
                "is_fresh": len(d_units) == 0
            })

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "count": len(results),
            "data": results
        })
    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return jsonify({"success": False, "error": str(e)}), 500


def validate_date_field(val: Any, field_name: str, allow_future: bool = False, min_year: int = 1950) -> tuple:
    """
    Validates calendar date string format (DD-MM-YYYY, YYYY-MM-DD), days per month,
    leap years, year bounds, and future date limits.
    """
    if not val:
        return True, None, ""
    val_str = str(val).strip()
    if not val_str:
        return True, None, ""

    parsed_dt = None
    # Try standard formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            parsed_dt = datetime.strptime(val_str, fmt).date()
            break
        except ValueError:
            pass

    if not parsed_dt:
        return False, None, f"Invalid date format for {field_name} ('{val_str}'). Proper format is DD/MM/YYYY or YYYY-MM-DD."

    if parsed_dt.year < min_year:
        return False, None, f"{field_name} year ({parsed_dt.year}) must be {min_year} or later."

    today = date.today()
    if not allow_future and parsed_dt > today:
        return False, None, f"{field_name} ({parsed_dt.strftime('%d/%m/%Y')}) exceeds current date ({today.strftime('%d/%m/%Y')}). Future dates are not allowed."

    return True, parsed_dt, ""


# =============================================================================
# 2. LIVE PREDICTION & SAVE ROUTES (TRADE-FREE)
# =============================================================================

@company_rec_bp.route("/api/ai/company-recommendation/predict", methods=["POST"])
def api_predict_recommendation():
    """
    Generate real-time hierarchical AI recommendation (Company -> Section -> Position).
    STRICTLY TRADE-FREE: Trade is not accepted or used as a prediction feature.
    """
    try:
        auth_user = get_current_authenticated_user()
        if not check_predict_authorization(auth_user):
            return jsonify({"success": False, "error": "Access Denied: Prediction functionality is restricted to authorized roles (1coyonco / 2coyonco)."}), 403

        data = request.get_json() or {}
        rank = data.get("rank") or ""
        date_of_enrollment = data.get("date_of_enrollment") or data.get("enrollment_date")
        prior_station = data.get("prior_station", "")
        units_history = data.get("units_history") or data.get("units") or []
        is_fresh_joinee = bool(data.get("is_fresh_joinee", False) or data.get("is_fresh", False) or len(units_history) == 0)
        army_number = data.get("army_number", "")
        name = data.get("name", "")

        # Strict Date Validation & Future Date Protection
        today = date.today()
        parsed_enroll_dt = None

        if date_of_enrollment:
            valid_dt, parsed_enroll_dt, err_msg = validate_date_field(date_of_enrollment, "Date of Enrollment", allow_future=False)
            if not valid_dt:
                return jsonify({"success": False, "error": err_msg}), 400

        # Validate Date of Birth (if provided)
        date_of_birth = data.get("date_of_birth") or data.get("dob")
        if date_of_birth:
            valid_dt, parsed_birth_dt, err_msg = validate_date_field(date_of_birth, "Date of Birth", allow_future=False)
            if not valid_dt:
                return jsonify({"success": False, "error": err_msg}), 400
            if parsed_enroll_dt and parsed_birth_dt and (parsed_enroll_dt - parsed_birth_dt).days < (16 * 365):
                return jsonify({
                    "success": False,
                    "error": f"Date of Enrollment ({parsed_enroll_dt.strftime('%d/%m/%Y')}) must be at least 16 years after Date of Birth ({parsed_birth_dt.strftime('%d/%m/%Y')})."
                }), 400

        # Validate Date of TOS (if provided)
        date_of_tos = data.get("date_of_tos") or data.get("tos")
        if date_of_tos:
            valid_dt, parsed_tos_dt, err_msg = validate_date_field(date_of_tos, "Date of TOS", allow_future=False)
            if not valid_dt:
                return jsonify({"success": False, "error": err_msg}), 400
            if parsed_enroll_dt and parsed_tos_dt and parsed_tos_dt < parsed_enroll_dt:
                return jsonify({
                    "success": False,
                    "error": f"Date of TOS ({parsed_tos_dt.strftime('%d/%m/%Y')}) cannot precede Date of Enrollment ({parsed_enroll_dt.strftime('%d/%m/%Y')})."
                }), 400

        # Validate Date of TORS (if provided)
        date_of_tors = data.get("date_of_tors") or data.get("tors")
        if date_of_tors:
            valid_dt, parsed_tors_dt, err_msg = validate_date_field(date_of_tors, "Date of TORS", allow_future=False)
            if not valid_dt:
                return jsonify({"success": False, "error": err_msg}), 400

        # Validate units history dates
        if not is_fresh_joinee and units_history:
            for idx, u in enumerate(units_history, start=1):
                u_name = u.get("unit") or f"Unit #{idx}"
                raw_from = u.get("from_date")
                raw_to = u.get("to_date")
                dt_from = None
                dt_to = None

                if raw_from:
                    valid_dt, dt_from, err_msg = validate_date_field(raw_from, f"Posting From Date for {u_name}", allow_future=False)
                    if not valid_dt:
                        return jsonify({"success": False, "error": err_msg}), 400
                    if parsed_enroll_dt and dt_from < parsed_enroll_dt:
                        return jsonify({
                            "success": False,
                            "error": f"Posting From Date for {u_name} ({dt_from.strftime('%d/%m/%Y')}) cannot precede Date of Enrollment ({parsed_enroll_dt.strftime('%d/%m/%Y')})."
                        }), 400

                if raw_to:
                    valid_dt, dt_to, err_msg = validate_date_field(raw_to, f"Posting To Date for {u_name}", allow_future=False)
                    if not valid_dt:
                        return jsonify({"success": False, "error": err_msg}), 400

                if dt_from and dt_to and dt_from > dt_to:
                    return jsonify({
                        "success": False,
                        "error": f"Posting From Date ({dt_from.strftime('%d/%m/%Y')}) cannot be later than To Date ({dt_to.strftime('%d/%m/%Y')}) for {u_name}."
                    }), 400

        selected_domains = data.get("selected_domains") or data.get("domains") or []
        selected_section = data.get("selected_section")
        target_sections = data.get("target_sections") or data.get("sections") or []
        target_trades = data.get("target_trades") or data.get("trades") or []
        section_trades_map = data.get("section_trades_map") or {}

        # If selected_section is not explicitly set but target_sections has exactly 1 section, use it
        if not selected_section:
            if isinstance(target_sections, list) and len(target_sections) == 1:
                selected_section = target_sections[0]
            elif isinstance(data.get("section"), str) and data.get("section").strip() and len(target_sections) <= 1:
                selected_section = data.get("section").strip()

        company = data.get("company") or data.get("served_company")

        rec = recommend_placement(
            units_history=units_history,
            is_fresh_joinee=is_fresh_joinee,
            army_number=army_number,
            name=name,
            selected_domains=selected_domains,
            rank=rank,
            date_of_enrollment=date_of_enrollment,
            prior_station=prior_station,
            selected_section=selected_section,
            target_sections=target_sections,
            target_trades=target_trades,
            section_trades_map=section_trades_map,
            company=company
        )

        return jsonify({
            "success": True,
            "data": rec
        })
    except Exception as e:
        print(f"Error generating recommendation: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to generate recommendation: {str(e)}"
        }), 500


@company_rec_bp.route("/api/ai/company-recommendation/save-history", methods=["POST"])
def api_save_recommendation():
    """
    Persist generated recommendation into ai_new_joinee_recommendations table.
    """
    try:
        user = get_current_authenticated_user()
        data = request.get_json() or {}

        army_number = data.get("army_number") or ""
        name = data.get("name") or ""
        rank = data.get("rank") or ""
        trade = data.get("trade") or ""  # Stored for record display only
        personnel_id = data.get("personnel_id")

        rec_coy = normalize_company_name(data.get("recommended_company"))
        conf_score = str(data["confidence_score"]) if data.get("confidence_score") is not None else None
        rec_pct = float(data["recommendation_percentage"]) if data.get("recommendation_percentage") is not None else None
        rec_pos = data.get("recommended_position") or ""
        pos_conf = str(data["position_confidence"]) if data.get("position_confidence") is not None else None
        conf_type = data.get("confidence_type") or "ml"
        model_ver = data.get("model_version") or ""

        prob_json = json.dumps(data.get("probabilities") or {})
        reasons_json = json.dumps(data.get("match_reasons") or [])
        shap_json = json.dumps(data.get("shap_explanation") or {})
        # Accept either 'units_history' or 'units' key from frontend
        units_data = data.get("units_history") or data.get("units") or []
        units_json = json.dumps(units_data)

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        # Auto-create / migrate table if it doesn't exist (prevents silent failures)
        ensure_recommendations_table(cursor, conn)

        if not personnel_id and army_number:
            cursor.execute("SELECT id FROM personnel WHERE army_number = %s LIMIT 1", (army_number,))
            row = cursor.fetchone()
            if row:
                personnel_id = row["id"]

        # Check if record with same army_number or name already exists to override
        existing_id = None
        if army_number:
            cursor.execute("SELECT id FROM ai_new_joinee_recommendations WHERE army_number = %s ORDER BY id DESC LIMIT 1", (army_number,))
            existing_row = cursor.fetchone()
            if existing_row:
                existing_id = existing_row["id"]
        elif name:
            cursor.execute("SELECT id FROM ai_new_joinee_recommendations WHERE name = %s ORDER BY id DESC LIMIT 1", (name,))
            existing_row = cursor.fetchone()
            if existing_row:
                existing_id = existing_row["id"]

        if existing_id:
            # OVERRIDE existing record with new recommendation and update timestamp
            update_sql = """
                UPDATE ai_new_joinee_recommendations SET
                    personnel_id = %s, army_number = %s, name = %s, `rank` = %s, trade = %s,
                    recommended_company = %s, confidence_score = %s, recommendation_percentage = %s,
                    recommended_position = %s, position_confidence = %s, confidence_type = %s, model_version = %s,
                    probabilities_json = %s, match_reasons_json = %s, shap_json = %s, units_history_json = %s,
                    decision_type = 'pending', updated_at = NOW()
                WHERE id = %s
            """
            cursor.execute(update_sql, (
                personnel_id, army_number, name, rank, trade,
                rec_coy, conf_score, rec_pct,
                rec_pos, pos_conf, conf_type, model_ver,
                prob_json, reasons_json, shap_json, units_json,
                existing_id
            ))
            conn.commit()
            saved_id = existing_id
            status_msg = "Recommendation updated successfully"
            is_updated = True
        else:
            # INSERT new recommendation record
            insert_sql = """
                INSERT INTO ai_new_joinee_recommendations (
                    personnel_id, army_number, name, `rank`, trade,
                    recommended_company, confidence_score, recommendation_percentage,
                    recommended_position, position_confidence, confidence_type, model_version,
                    probabilities_json, match_reasons_json, shap_json, units_history_json,
                    decision_type, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    'pending', NOW(), NOW()
                )
            """
            cursor.execute(insert_sql, (
                personnel_id, army_number, name, rank, trade,
                rec_coy, conf_score, rec_pct,
                rec_pos, pos_conf, conf_type, model_ver,
                prob_json, reasons_json, shap_json, units_json
            ))
            conn.commit()
            saved_id = cursor.lastrowid
            status_msg = "Recommendation saved successfully"
            is_updated = False

        cursor.close()
        conn.close()

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return jsonify({
            "success": True,
            "id": saved_id,
            "is_updated": is_updated,
            "status": "Updated" if is_updated else "Saved",
            "updated_at": now_str,
            "message": status_msg
        })
    except Exception as e:
        print(f"Error saving recommendation: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# 3. INSIGHTS LIST, SEARCH & DETAIL ROUTES (CO / ADJUTANT / 2IC)
# =============================================================================

@company_rec_bp.route("/api/ai/company-recommendation/insights", methods=["GET"])
def api_get_insights_list():
    """
    Paginated, searchable recommendation list for executive review.
    Enforces RBAC: Accessible to authorized management roles.
    """
    user = get_current_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not check_view_authorization(user):
        return jsonify({"success": False, "error": "Forbidden: Executive access required"}), 403

    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
        search = request.args.get("search", "").strip()
        coy_filter = request.args.get("company", "ALL").strip()
        rank_filter = request.args.get("rank", "ALL").strip()
        decision_filter = request.args.get("decision", "ALL").strip()
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc").lower()

        offset = max(0, (page - 1) * page_size)

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "Database unavailable"}), 500

        cursor = conn.cursor(dictionary=True)
        ensure_recommendations_table(cursor, conn)

        where_clauses = ["1=1"]
        params = []

        if search:
            where_clauses.append("(army_number LIKE %s OR name LIKE %s)")
            s_param = f"%{search}%"
            params.extend([s_param, s_param])

        if coy_filter and coy_filter != "ALL":
            canon = normalize_company_name(coy_filter)
            where_clauses.append("(recommended_company = %s OR recommended_company = %s)")
            params.extend([canon, to_db_company_name(canon)])

        if rank_filter and rank_filter != "ALL":
            clean_rf = rank_filter.strip().upper()
            synonyms = RANK_SYNONYM_MAP.get(clean_rf, [clean_rf])
            syn_set = set(synonyms)
            syn_set.add(clean_rf)
            unique_synonyms = list(syn_set)
            placeholders = ", ".join(["%s"] * len(unique_synonyms))
            where_clauses.append(f"TRIM(UPPER(`rank`)) IN ({placeholders})")
            params.extend(unique_synonyms)

        if decision_filter and decision_filter != "ALL":
            where_clauses.append("decision_type = %s")
            params.append(decision_filter)

        where_str = " AND ".join(where_clauses)

        # Count total
        count_sql = f"SELECT COUNT(*) as total FROM ai_new_joinee_recommendations WHERE {where_str}"
        cursor.execute(count_sql, tuple(params))
        total_count = cursor.fetchone()["total"]

        # Fetch comprehensive ranks for filter dropdown
        STANDARD_RANKS = [
            "Col",
            "Lt Col",
            "Maj",
            "Capt",
            "Lt",
            "Subedar Major",
            "Sub Maj",
            "Subedar",
            "Sub",
            "Naib Subedar",
            "Nb Sub",
            "RHM",
            "BHM",
            "CHM",
            "CQMH",
            "HAV",
            "L HAV",
            "LOC HAV",
            "NK",
            "L NK",
            "LOC NK",
            "CFN",
            "Signal Man",
            "Sigmn",
            "Agniveer"
        ]

        db_ranks = set()
        for tbl in ["ai_new_joinee_recommendations", "dues_in", "personnel"]:
            try:
                cursor.execute(f"SELECT DISTINCT `{tbl}`.`rank` FROM `{tbl}` WHERE `{tbl}`.`rank` IS NOT NULL AND TRIM(`{tbl}`.`rank`) != ''")
                for row in cursor.fetchall():
                    val = (row.get("rank") or "").strip()
                    if val:
                        db_ranks.add(val)
            except Exception:
                pass

        available_ranks = []
        seen = set()
        for rk in STANDARD_RANKS:
            key = rk.upper().strip()
            if key not in seen:
                available_ranks.append(rk)
                seen.add(key)
        for rk in sorted(db_ranks):
            key = rk.upper().strip()
            if key not in seen:
                available_ranks.append(rk)
                seen.add(key)

        ALLOWED_SORT_COLS = {
            "percentage": "recommendation_percentage",
            "created_at": "created_at",
            "updated_at": "updated_at",
            "id": "id",
            "name": "name",
            "army_number": "army_number"
        }
        order_col = ALLOWED_SORT_COLS.get(sort_by, "created_at")
        order_dir = "DESC" if sort_order == "desc" else "ASC"

        query_sql = f"""
            SELECT * FROM ai_new_joinee_recommendations
            WHERE {where_str}
            ORDER BY {order_col} {order_dir}
            LIMIT %s OFFSET %s
        """
        query_params = list(params) + [page_size, offset]
        cursor.execute(query_sql, tuple(query_params))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        formatted_rows = []
        for idx, r in enumerate(rows):
            s_no = offset + idx + 1
            units_json = r.get("units_history_json")
            prev_units_str = "No Previous Unit"
            units_list = []
            if r.get("units_history_json"):
                try:
                    units_list = json.loads(r["units_history_json"])
                except Exception:
                    pass

            prev_units_str = format_units_served_short(units_list) if 'format_units_served_short' in globals() else "No Previous Unit"
            try:
                if not prev_units_str or prev_units_str == "No Previous Unit":
                    if units_list and isinstance(units_list, list):
                        unit_names = [u.get("unit") or u.get("unit_name") for u in units_list if (u.get("unit") or u.get("unit_name"))]
                        prev_units_str = ", ".join(unit_names) if unit_names else f"{len(units_list)} Unit(s)"
            except Exception:
                pass

            match_reasons = []
            try:
                if r.get("match_reasons_json"):
                    match_reasons = json.loads(r["match_reasons_json"])
            except Exception:
                pass

            canonical_coy = normalize_company_name(r.get("recommended_company"))
            rec_pos = r.get("recommended_position") or "GD"
            rec_sec = get_section_for_position(canonical_coy, rec_pos)

            created_at_dt = r.get("created_at")
            updated_at_dt = r.get("updated_at")
            created_at_str = created_at_dt.strftime("%d/%m/%Y %H:%M") if created_at_dt else ""
            updated_at_str = updated_at_dt.strftime("%d/%m/%Y %H:%M") if updated_at_dt else ""

            is_re_calculated = False
            if created_at_dt and updated_at_dt:
                diff_seconds = (updated_at_dt - created_at_dt).total_seconds()
                is_re_calculated = diff_seconds > 30

            two_ic_was_updated = bool(r.get("two_ic_updated") or r.get("updated_by_role") == "2IC")
            final_coy_val = normalize_company_name(r.get("final_company") or canonical_coy)
            two_ic_msg = r.get("two_ic_message") or (f"2IC ({r.get('updated_by') or r.get('decided_by')}) updated & finalized allocation to {final_coy_val} on {updated_at_str}" if two_ic_was_updated else "")

            formatted_rows.append({
                "id": r["id"],
                "s_no": s_no,
                "personnel_id": r.get("personnel_id"),
                "army_number": r.get("army_number") or "N/A",
                "name": r.get("name") or "N/A",
                "rank": r.get("rank") or "N/A",
                "trade": r.get("trade") or "N/A",
                "previous_units_formatted": prev_units_str,
                "recommended_company": canonical_coy,
                "recommended_section": rec_sec,
                "confidence_score": r.get("confidence_score") or "",
                "recommendation_percentage": float(r["recommendation_percentage"]) if r.get("recommendation_percentage") is not None else 0.0,
                "recommended_position": rec_pos,
                "position_confidence": r.get("position_confidence") or "",
                "final_company": final_coy_val,
                "final_position": r.get("final_position") or rec_pos,
                "decision_type": r.get("decision_type") or "pending",
                "decision_remarks": r.get("decision_remarks") or "",
                "decided_by": r.get("decided_by") or "",
                "decided_at": r.get("decided_at").strftime("%d/%m/%Y %H:%M") if r.get("decided_at") else "",
                "updated_by": r.get("updated_by") or "",
                "updated_by_role": r.get("updated_by_role") or "",
                "created_at": created_at_str,
                "updated_at": updated_at_str,
                "is_re_calculated": is_re_calculated,
                "match_reasons": match_reasons,
                "adjutant_action": r.get("adjutant_action") or "",
                "adjutant_company": r.get("adjutant_company") or "",
                "adjutant_section": r.get("adjutant_section") or (get_section_for_position(r.get("adjutant_company"), r.get("adjutant_position")) if r.get("adjutant_company") and r.get("adjutant_position") else ""),
                "adjutant_position": r.get("adjutant_position") or "",
                "adjutant_remarks": r.get("adjutant_remarks") or "",
                "adjutant_by": r.get("adjutant_by") or "",
                "adjutant_at": r.get("adjutant_at").strftime("%d/%m/%Y %H:%M") if r.get("adjutant_at") else "",
                "two_ic_updated": two_ic_was_updated,
                "two_ic_message": two_ic_msg
            })

        total_pages = max(1, (total_count + page_size - 1) // page_size)
        user_role = str(user.get("role", "")).strip().upper()
        is_co = user_role in ["CO", "COMMANDING OFFICER"]
        is_adjutant = (user_role == "ADJUTANT")
        is_2ic = user_role in ["2IC", "ADMIN", "SUPER ADMIN"]

        can_assign = is_2ic
        can_add_remarks = (is_adjutant or is_2ic) and not is_co
        is_read_only = is_co or (not can_assign and not is_adjutant)

        return jsonify({
            "success": True,
            "data": formatted_rows,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "available_ranks": available_ranks,
            "user_role": user_role,
            "can_add_remarks": can_add_remarks,
            "can_assign_company": can_assign,
            "is_read_only": is_read_only
        })

    except Exception as e:
        print(f"Error in api_get_insights_list: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@company_rec_bp.route("/api/ai/company-recommendation/insights/<int:rec_id>", methods=["GET"])
def api_get_insight_detail(rec_id: int):
    """
    Fetch full detail of a single recommendation for the action dialog.
    """
    user = get_current_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not check_view_authorization(user):
        return jsonify({"success": False, "error": "Forbidden: Executive access required"}), 403

    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "Database unavailable"}), 500

        cursor = conn.cursor(dictionary=True)
        ensure_recommendations_table(cursor, conn)
        cursor.execute("SELECT * FROM ai_new_joinee_recommendations WHERE id = %s", (rec_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Recommendation not found"}), 404

        cursor.close()
        conn.close()

        # Parse JSON fields safely
        probs = json.loads(row["probabilities_json"]) if row.get("probabilities_json") else {}
        reasons = json.loads(row["match_reasons_json"]) if row.get("match_reasons_json") else []
        shap_data = json.loads(row["shap_json"]) if row.get("shap_json") else {}
        units_history = json.loads(row["units_history_json"]) if row.get("units_history_json") else []

        canonical_coy = normalize_company_name(row.get("recommended_company"))
        rec_pos = row.get("recommended_position") or "GD"
        rec_sec = get_section_for_position(canonical_coy, rec_pos)

        final_coy = normalize_company_name(row.get("final_company") or canonical_coy)
        final_pos = row.get("final_position") or rec_pos
        final_sec = get_section_for_position(final_coy, final_pos)

        user_role = str(user.get("role", "")).strip().upper()
        is_co = user_role in ["CO", "COMMANDING OFFICER"]
        is_adjutant = (user_role == "ADJUTANT")
        is_2ic = user_role in ["2IC", "ADMIN", "SUPER ADMIN"]

        domain_xai = generate_domain_and_contrastive_explainability(
            units_history=units_history,
            selected_domains=[],
            predicted_company=canonical_coy,
            section=rec_sec,
            position=rec_pos,
            company_probabilities=probs,
            rank=row.get("rank") or ""
        )

        two_ic_was_updated = bool(row.get("two_ic_updated") or row.get("updated_by_role") == "2IC" or row.get("decision_type") in ["accepted", "rejected"])
        two_ic_msg = row.get("two_ic_message") or (f"Notice to Adjutant: 2IC ({row.get('updated_by') or row.get('decided_by') or '2IC'}) updated & finalized allocation to {final_coy} - {final_sec} ({final_pos}) on {row.get('updated_at').strftime('%d/%m/%Y %H:%M') if row.get('updated_at') else 'N/A'}." if two_ic_was_updated else "")

        return jsonify({
            "success": True,
            "data": {
                "id": row["id"],
                "personnel_id": row.get("personnel_id"),
                "army_number": row.get("army_number"),
                "name": row.get("name"),
                "rank": row.get("rank"),
                "trade": row.get("trade") or "N/A",
                "recommended_company": canonical_coy,
                "confidence_score": row.get("confidence_score") or "",
                "recommendation_percentage": float(row["recommendation_percentage"]) if row.get("recommendation_percentage") is not None else 0.0,
                "recommended_section": rec_sec,
                "recommended_position": rec_pos,
                "position_confidence": row.get("position_confidence") or "",
                "confidence_type": row.get("confidence_type") or "ml",
                "probabilities": probs,
                "match_reasons": reasons or domain_xai.get("why_recommended", []),
                "shap_explanation": shap_data,
                "domain_explainability": domain_xai.get("duty_domain_breakdown", []),
                "why_recommended": domain_xai.get("why_recommended", []),
                "why_not_others": domain_xai.get("why_not_others", []),
                "units_history": units_history,
                "final_company": final_coy,
                "final_position": final_pos,
                "final_section": final_sec,
                "decision_type": row.get("decision_type") or "pending",
                "decision_remarks": row.get("decision_remarks") or "",
                "decided_by": row.get("decided_by") or "",
                "decided_at": row.get("decided_at").strftime("%d/%m/%Y %H:%M") if row.get("decided_at") else "",
                "updated_by": row.get("updated_by") or "",
                "updated_by_role": row.get("updated_by_role") or "",
                "updated_at": row.get("updated_at").strftime("%d/%m/%Y %H:%M") if row.get("updated_at") else "",
                "adjutant_action": row.get("adjutant_action") or "",
                "adjutant_company": row.get("adjutant_company") or "",
                "adjutant_section": row.get("adjutant_section") or (get_section_for_position(row.get("adjutant_company"), row.get("adjutant_position")) if row.get("adjutant_company") and row.get("adjutant_position") else ""),
                "adjutant_position": row.get("adjutant_position") or "",
                "adjutant_remarks": row.get("adjutant_remarks") or "",
                "adjutant_by": row.get("adjutant_by") or "",
                "adjutant_at": row.get("adjutant_at").strftime("%d/%m/%Y %H:%M") if row.get("adjutant_at") else "",
                "two_ic_updated": two_ic_was_updated,
                "two_ic_message": two_ic_msg,
                "hierarchy": UNIT_15_CESR_STRUCTURE,
                "available_companies": get_all_companies(),
                "company_sections_map": {coy: get_sections_for_company(coy) for coy in get_all_companies()},
                "company_positions_map": {coy: get_positions_for_company(coy) for coy in get_all_companies()},
                "user_role": user_role,
                "can_add_remarks": (is_adjutant or is_2ic) and not is_co,
                "can_assign_company": is_2ic and not is_co,
                "is_read_only": is_co,
            }
        })
    except Exception as e:
        print(f"Error in api_get_insight_detail: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# 4. EXECUTIVE DECISION WORKFLOW (ROLE-BASED: CO / ADJUTANT / 2IC)
# =============================================================================

@company_rec_bp.route("/api/ai/company-recommendation/decision", methods=["POST"])
def api_save_recommendation_decision():
    """
    Save or update recommendation decision.
    - ADJUTANT: Can Accept Recommendation or Update Recommendation with reason.
    - 2IC / ADMIN: Authorized to update company, section, position, and execute final allocation into personnel.
    - CO: View only, cannot submit updates or assignments.
    """
    user = get_current_authenticated_user()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    user_role = str(user.get("role", "")).strip().upper()
    if user_role in ["CO", "COMMANDING OFFICER"]:
        return jsonify({
            "success": False,
            "error": "Access Denied: Commanding Officer (CO) has view-only access and cannot submit decisions or updates."
        }), 403

    allowed_assignment_roles = ["2IC", "ADMIN", "SUPER ADMIN", "ADJUTANT"]

    if user_role not in allowed_assignment_roles:
        return jsonify({
            "success": False,
            "error": "Access Denied: You do not have executive assignment authority."
        }), 403

    if not check_executive_authorization(user):
        return jsonify({"success": False, "error": "Forbidden: Executive access required"}), 403

    try:
        data = request.get_json() or {}
        rec_id = data.get("id") or data.get("recommendation_id")
        action = str(data.get("action") or data.get("decision_type") or "accepted").strip().lower()
        remarks = str(data.get("decision_remarks") or data.get("remarks") or "").strip()
        final_company = data.get("final_company")
        final_position = data.get("final_position")

        if not rec_id:
            return jsonify({"success": False, "error": "Recommendation ID is required"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "Database unavailable"}), 500

        cursor = conn.cursor(dictionary=True)
        ensure_recommendations_table(cursor, conn)
        cursor.execute("SELECT * FROM ai_new_joinee_recommendations WHERE id = %s", (rec_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Record not found"}), 404

        user_id = str(user.get("user_id", user.get("id", "1")))
        user_name = user.get("username") or user.get("name") or f"User {user_id}"
        decided_by_str = f"2IC ({user_name})" if user_role in ["2IC", "ADMIN", "SUPER ADMIN"] else f"{user_role} ({user_name})"

        # =========================================================================
        # ADJUTANT WORKFLOW: Propose / Recommend (Never assigns an individual)
        # =========================================================================
        if user_role == "ADJUTANT" or action.startswith("adjutant_"):
            if action in ["adjutant_update", "update"] and not remarks:
                cursor.close()
                conn.close()
                return jsonify({
                    "success": False,
                    "error": "Reason is required when Adjutant updates a recommendation."
                }), 400

            if action in ["adjutant_reject", "reject", "rejected"]:
                if not remarks:
                    remarks = "Adjutant rejected AI recommendation."
                adj_action_type = "rejected"
                dec_type = "rejected"
            elif action in ["adjutant_update", "update"]:
                adj_action_type = "updated"
                dec_type = existing.get("decision_type", "pending")
            else:
                adj_action_type = "accepted"
                dec_type = existing.get("decision_type", "pending")

            adj_coy = normalize_company_name(final_company or data.get("recommended_company") or existing.get("recommended_company"))
            adj_pos = final_position or data.get("recommended_position") or existing.get("recommended_position")
            adj_sec = data.get("final_section") or data.get("recommended_section") or get_section_for_position(adj_coy, adj_pos)

            cursor.execute("""
                UPDATE ai_new_joinee_recommendations
                SET adjutant_action = %s,
                    adjutant_company = %s,
                    adjutant_section = %s,
                    adjutant_position = %s,
                    adjutant_remarks = %s,
                    adjutant_by = %s,
                    adjutant_at = NOW(),
                    decision_type = %s,
                    decision_remarks = %s,
                    updated_by = %s,
                    updated_by_role = %s,
                    updated_by_user_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                adj_action_type,
                adj_coy,
                adj_sec,
                adj_pos,
                remarks,
                user_name,
                dec_type,
                remarks,
                user_name,
                user_role,
                user_id,
                rec_id
            ))
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "message": f"Adjutant recommendation successfully {adj_action_type}.",
                "decision_type": dec_type,
                "adjutant_action": adj_action_type,
                "adjutant_company": adj_coy,
                "adjutant_section": adj_sec,
                "adjutant_position": adj_pos,
                "adjutant_remarks": remarks,
                "adjutant_by": user_name
            })

        # =========================================================================
        # 2IC / ADMIN WORKFLOW: Final Allocation & Company/Section/Position Assignment
        # =========================================================================
        allowed_allocation_roles = ["2IC", "ADMIN", "SUPER ADMIN"]
        if user_role not in allowed_allocation_roles:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "Access Denied: Only 2IC is authorized to perform final allocation and update company placement."
            }), 403

        if action in ["accept", "accepted"]:
            decision_type = "accepted"
        elif action in ["reject", "rejected"]:
            decision_type = "rejected"
        elif action in ["update", "updated"]:
            decision_type = "accepted"
        else:
            decision_type = "pending"

        # Validate hierarchy
        final_coy_val = normalize_company_name(final_company or existing.get("recommended_company"))
        final_pos_val = final_position or existing.get("recommended_position")

        if not is_position_valid_for_company(final_coy_val, final_pos_val):
            final_pos_val = get_positions_for_company(final_coy_val)[0]

        final_sec_val = data.get("final_section") or get_section_for_position(final_coy_val, final_pos_val)

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        two_ic_msg = f"Notice to Adjutant: 2IC ({user_name}) updated & finalized allocation to {final_coy_val} - {final_sec_val} ({final_pos_val}) on {now_str}."

        update_sql = """
            UPDATE ai_new_joinee_recommendations
            SET decision_type = %s,
                decision_remarks = %s,
                final_company = %s,
                final_section = %s,
                final_position = %s,
                decided_by = %s,
                decided_at = NOW(),
                updated_by = %s,
                updated_by_role = %s,
                updated_by_user_id = %s,
                updated_at = NOW(),
                two_ic_updated = 1,
                two_ic_message = %s
            WHERE id = %s
        """
        cursor.execute(update_sql, (
            decision_type,
            remarks,
            final_coy_val,
            final_sec_val,
            final_pos_val,
            decided_by_str,
            user_name,
            user_role,
            user_id,
            two_ic_msg,
            rec_id
        ))
        conn.commit()

        # If accepted/updated, sync company & section to personnel record and dues_in
        if decision_type == "accepted":
            db_coy_val = to_db_company_name(final_coy_val)
            if existing.get("personnel_id"):
                cursor.execute(
                    "UPDATE personnel SET company = %s, section = %s WHERE id = %s",
                    (db_coy_val, final_sec_val, existing["personnel_id"])
                )
            elif existing.get("army_number"):
                cursor.execute(
                    "UPDATE personnel SET company = %s, section = %s WHERE army_number = %s",
                    (db_coy_val, final_sec_val, existing["army_number"])
                )
            if existing.get("army_number"):
                try:
                    cursor.execute(
                        "UPDATE dues_in SET company = %s WHERE army_number = %s",
                        (db_coy_val, existing["army_number"])
                    )
                except Exception:
                    pass
            conn.commit()

        cursor.close()
        conn.close()

        action_msg = "updated and assigned" if action in ["update", "updated"] else "assigned"
        return jsonify({
            "success": True,
            "message": f"Recommendation successfully {action_msg} to {final_coy_val} ({final_pos_val}) by {user_role}",
            "decision_type": decision_type,
            "decided_by": decided_by_str,
            "final_company": final_coy_val,
            "final_position": final_pos_val
        })

    except Exception as e:
        print(f"Error in api_record_decision: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# 5. RETRAINING & ANALYTICS ROUTES (50-NEW-RECORD THRESHOLD)
# =============================================================================

@company_rec_bp.route("/api/ai/company-recommendation/retrain-status", methods=["GET"])
def api_retrain_status():
    """
    Check retraining status and dataset threshold counts (50 new records).
    """
    try:
        conn = get_db_connection()
        total_personnel = 0
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as c FROM personnel WHERE company IS NOT NULL")
            total_personnel = cursor.fetchone()["c"]
            cursor.close()
            conn.close()

        meta_path = os.path.join(os.path.dirname(__file__), "model", "model_metadata.json")
        metadata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                metadata = json.load(f)

        trained_records = metadata.get("total_records", total_personnel)
        new_records = max(0, total_personnel - trained_records)
        threshold = 50

        return jsonify({
            "success": True,
            "status": {
                "trained": bool(metadata),
                "model_version": metadata.get("model_version", "company_position_model_v2"),
                "selected_model": metadata.get("selected_model", "Random Forest"),
                "last_trained_at": metadata.get("trained_at", "N/A"),
                "total_records_in_db": total_personnel,
                "trained_records_count": trained_records,
                "new_records_since_last_training": new_records,
                "retrain_threshold": threshold,
                "ready_for_retrain": (new_records >= threshold),
                "trade_excluded": metadata.get("trade_excluded", True),
                "champion_metrics": metadata.get("champion_metrics", {})
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@company_rec_bp.route("/api/ai/company-recommendation/retrain", methods=["POST"])
def api_trigger_retrain():
    """
    Trigger complete retraining pipeline (Hierarchical RF vs XGBoost + SMOTE + Evaluation).
    """
    try:
        user = get_current_authenticated_user()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"}), 401

        meta = run_training_pipeline()
        load_model_artifacts()

        return jsonify({
            "success": True,
            "message": f"Retraining pipeline completed successfully. Champion Model: {meta.get('selected_model')}",
            "metadata": meta
        })
    except Exception as e:
        print(f"Error during retrain: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@company_rec_bp.route("/api/ai/company-recommendation/insights-count", methods=["GET"])
def api_insights_count():
    """
    Return summary counts of recommendations for UI badges.
    """
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": True, "count": 0, "pending_count": 0})

        cursor = conn.cursor(dictionary=True)
        ensure_recommendations_table(cursor, conn)

        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN decision_type = 'pending' THEN 1 ELSE 0 END) as pending FROM ai_new_joinee_recommendations")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        total = int(row["total"] or 0) if row else 0
        pending = int(row["pending"] or 0) if row else 0

        return jsonify({
            "success": True,
            "count": total,
            "total_count": total,
            "pending_count": pending,
            "accepted_count": max(0, total - pending)
        })
    except Exception as e:
        return jsonify({"success": True, "count": 0, "total_count": 0, "pending_count": 0})


# =============================================================================
# 6. TESTING & EVALUATION DASHBOARD ROUTE
# =============================================================================

@company_rec_bp.route("/testing/company-recommendation", methods=["GET"])
def testing_company_recommendation_view():
    """
    Render testing and evaluation dashboard.
    """
    try:
        meta_path = os.path.join(os.path.dirname(__file__), "model", "model_metadata.json")
        eval_path = os.path.join(os.path.dirname(__file__), "model", "evaluation_report.json")
        feat_path = os.path.join(os.path.dirname(__file__), "model", "feature_importance.json")

        metadata = {}
        eval_report = {}
        features = []

        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                metadata = json.load(f)
        if os.path.exists(eval_path):
            with open(eval_path, "r") as f:
                eval_report = json.load(f)
        if os.path.exists(feat_path):
            with open(feat_path, "r") as f:
                features = json.load(f)

        analytics = {
            "metadata": metadata,
            "evaluation": eval_report,
            "top_features": features[:10],
            "hierarchy": UNIT_15_CESR_STRUCTURE
        }

        template_name = "testing/company_recommendation_test.html"
        return render_template(template_name, analytics=analytics, retrain_status={
            "new_records_since_last_training": 0,
            "trained_at": metadata.get("trained_at", "N/A"),
            "selected_model": metadata.get("selected_model", "Random Forest")
        })
    except Exception as e:
        return f"Error loading testing view: {str(e)}", 500


@company_rec_bp.route("/api/ai/company-recommendation/visualization/<int:rec_id>", methods=["GET"])
def api_recommendation_visualization(rec_id: int):
    """
    Render probability comparison and SHAP explanation visualization page in a new tab.
    """
    return render_template("visualization.html", rec_id=rec_id)

