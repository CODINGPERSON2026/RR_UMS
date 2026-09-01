"""
Flask Blueprint & REST API Routes for AI New Joinee Recommendation (Unit 15 CESR)
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
AUTHORIZED_VIEW_ROLES = ["CO", "ADJUTANT", "2IC", "ADMIN", "COMMANDING OFFICER", "SUPER ADMIN", "OC", "SUBEDAR MAJOR", "S/JCO", "PROJECT OFFICER", "PROJECT JCO"]


def check_executive_authorization(user: Optional[Dict[str, Any]]) -> bool:
    """Check if authenticated user has CO, Adjutant, or 2IC decision authority."""
    if not user:
        return False
    role = str(user.get("role", "")).strip().upper()

    if role in AUTHORIZED_DECISION_ROLES:
        return True

    import re
    if re.search(r'\b(CO|ADJUTANT|2IC)\b', role):
        if not re.search(r'\b(NCO|JCO|ONCO)\b', role):
            return True

    return False


def check_view_authorization(user: Optional[Dict[str, Any]]) -> bool:
    """Check if authenticated user can view insights tables and dashboards."""
    if not user:
        return False
    role = str(user.get("role", "")).strip().upper()
    if role in AUTHORIZED_VIEW_ROLES:
        return True
    return check_executive_authorization(user)


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


@company_rec_bp.route("/api/ai/company-recommendation/lookup-personnel", methods=["GET"])
def api_lookup_personnel():
    """
    Lookup personnel details by Army Number to auto-fill AI recommendation form.
    """
    army_no = request.args.get("army_number", "").strip()
    if not army_no:
        return jsonify({"success": False, "message": "Army number required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, army_number, name, `rank`, trade, 
                   date_of_enrollment, company, section, prior_station
            FROM personnel 
            WHERE army_number = %s 
            LIMIT 1
        """, (army_no,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            enroll_str = ""
            if row.get("date_of_enrollment"):
                try:
                    enroll_str = row["date_of_enrollment"].strftime("%d-%m-%Y") if hasattr(row["date_of_enrollment"], "strftime") else str(row["date_of_enrollment"])
                except Exception:
                    enroll_str = str(row["date_of_enrollment"])

            return jsonify({
                "success": True,
                "found": True,
                "data": {
                    "id": row["id"],
                    "army_number": row["army_number"],
                    "name": row["name"],
                    "rank": row["rank"],
                    "trade": row.get("trade") or "",  # Returned for display only
                    "date_of_enrollment": enroll_str,
                    "company": row["company"],
                    "section": row["section"],
                    "prior_station": row.get("prior_station") or ""
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
            conn.close()
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
        return False, None, f"Invalid date format for {field_name} ('{val_str}'). Proper format is DD-MM-YYYY or YYYY-MM-DD."

    if parsed_dt.year < min_year:
        return False, None, f"{field_name} year ({parsed_dt.year}) must be {min_year} or later."

    today = date.today()
    if not allow_future and parsed_dt > today:
        return False, None, f"{field_name} ({parsed_dt.strftime('%d-%m-%Y')}) exceeds current date ({today.strftime('%d-%m-%Y')}). Future dates are not allowed."

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
        data = request.get_json() or {}
        rank = data.get("rank", "Signal Man")
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
                    "error": f"Date of Enrollment ({parsed_enroll_dt.strftime('%d-%m-%Y')}) must be at least 16 years after Date of Birth ({parsed_birth_dt.strftime('%d-%m-%Y')})."
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
                    "error": f"Date of TOS ({parsed_tos_dt.strftime('%d-%m-%Y')}) cannot precede Date of Enrollment ({parsed_enroll_dt.strftime('%d-%m-%Y')})."
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
                            "error": f"Posting From Date for {u_name} ({dt_from.strftime('%d-%m-%Y')}) cannot precede Date of Enrollment ({parsed_enroll_dt.strftime('%d-%m-%Y')})."
                        }), 400

                if raw_to:
                    valid_dt, dt_to, err_msg = validate_date_field(raw_to, f"Posting To Date for {u_name}", allow_future=False)
                    if not valid_dt:
                        return jsonify({"success": False, "error": err_msg}), 400

                if dt_from and dt_to and dt_from > dt_to:
                    return jsonify({
                        "success": False,
                        "error": f"Posting From Date ({dt_from.strftime('%d-%m-%Y')}) cannot be later than To Date ({dt_to.strftime('%d-%m-%Y')}) for {u_name}."
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
            section_trades_map=section_trades_map
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
        user = require_login()
        data = request.get_json() or {}

        army_number = data.get("army_number") or ""
        name = data.get("name") or ""
        rank = data.get("rank") or ""
        trade = data.get("trade") or ""  # Stored for record display only
        personnel_id = data.get("personnel_id")

        rec_coy = normalize_company_name(data.get("recommended_company"))
        conf_score = str(data.get("confidence_score") or "85.0%")
        rec_pct = float(data.get("recommendation_percentage") or 85.0)
        rec_pos = data.get("recommended_position") or ""
        pos_conf = str(data.get("position_confidence") or "80.0%")
        conf_type = data.get("confidence_type") or "ml"
        model_ver = data.get("model_version") or "company_position_model_v2"

        prob_json = json.dumps(data.get("probabilities") or {})
        reasons_json = json.dumps(data.get("match_reasons") or [])
        shap_json = json.dumps(data.get("shap_explanation") or {})
        units_json = json.dumps(data.get("units_history") or [])

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

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

        now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
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
    user = require_login()
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
            where_clauses.append("`rank` = %s")
            params.append(rank_filter)

        if decision_filter and decision_filter != "ALL":
            where_clauses.append("decision_type = %s")
            params.append(decision_filter)

        where_str = " AND ".join(where_clauses)

        # Count total
        count_sql = f"SELECT COUNT(*) as total FROM ai_new_joinee_recommendations WHERE {where_str}"
        cursor.execute(count_sql, tuple(params))
        total_count = cursor.fetchone()["total"]

        # Fetch ranks for filter dropdown
        cursor.execute("SELECT DISTINCT `rank` FROM ai_new_joinee_recommendations WHERE `rank` IS NOT NULL ORDER BY `rank`")
        rank_rows = cursor.fetchall()
        available_ranks = [r["rank"] for r in rank_rows if r.get("rank")]

        order_col = "recommendation_percentage" if sort_by == "percentage" else "id"
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
            try:
                if units_json:
                    u_list = json.loads(units_json)
                    if isinstance(u_list, list) and len(u_list) > 0:
                        unit_names = [u.get("unit") or u.get("unit_name") for u in u_list if (u.get("unit") or u.get("unit_name"))]
                        prev_units_str = ", ".join(unit_names) if unit_names else f"{len(u_list)} Unit(s)"
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
            created_at_str = created_at_dt.strftime("%d-%m-%Y %H:%M") if created_at_dt else ""
            updated_at_str = updated_at_dt.strftime("%d-%m-%Y %H:%M") if updated_at_dt else ""

            # Mark as re-calculated if updated_at is more than 30 seconds after created_at
            is_re_calculated = False
            if created_at_dt and updated_at_dt:
                diff_seconds = (updated_at_dt - created_at_dt).total_seconds()
                is_re_calculated = diff_seconds > 30

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
                "confidence_score": r.get("confidence_score") or "85.0%",
                "recommendation_percentage": float(r.get("recommendation_percentage") or 85.0),
                "recommended_position": rec_pos,
                "position_confidence": r.get("position_confidence") or "80.0%",
                "final_company": r.get("final_company"),
                "final_position": r.get("final_position"),
                "decision_type": r.get("decision_type") or "pending",
                "decision_remarks": r.get("decision_remarks") or "",
                "decided_by": r.get("decided_by") or "",
                "decided_at": r.get("decided_at").strftime("%d-%m-%Y %H:%M") if r.get("decided_at") else "",
                "created_at": created_at_str,
                "updated_at": updated_at_str,
                "is_re_calculated": is_re_calculated,
                "match_reasons": match_reasons
            })

        total_pages = max(1, (total_count + page_size - 1) // page_size)
        user_role = str(user.get("role", "")).strip().upper()
        is_co = user_role in ["CO", "COMMANDING OFFICER"]
        is_adjutant = (user_role == "ADJUTANT")
        is_2ic = user_role in ["2IC", "ADMIN", "SUPER ADMIN"]

        return jsonify({
            "success": True,
            "data": formatted_rows,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "available_ranks": available_ranks,
            "user_role": user_role,
            "can_add_remarks": (is_adjutant or is_2ic),
            "can_assign_company": is_2ic,
            "is_read_only": is_co
        })

    except Exception as e:
        print(f"Error in api_get_insights_list: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@company_rec_bp.route("/api/ai/company-recommendation/insights/<int:rec_id>", methods=["GET"])
def api_get_insight_detail(rec_id: int):
    """
    Fetch full detail of a single recommendation for the action dialog.
    """
    user = require_login()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not check_view_authorization(user):
        return jsonify({"success": False, "error": "Forbidden: Executive access required"}), 403

    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "Database unavailable"}), 500

        cursor = conn.cursor(dictionary=True)
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
                "confidence_score": row.get("confidence_score") or "85.0%",
                "recommendation_percentage": float(row.get("recommendation_percentage") or 85.0),
                "recommended_section": rec_sec,
                "recommended_position": rec_pos,
                "position_confidence": row.get("position_confidence") or "80.0%",
                "confidence_type": row.get("confidence_type") or "ml",
                "probabilities": probs,
                "match_reasons": reasons or domain_xai.get("why_recommended", []),
                "shap_explanation": shap_data,
                "domain_explainability": domain_xai.get("duty_domain_breakdown", []),
                "why_recommended": domain_xai.get("why_recommended", []),
                "why_not_others": domain_xai.get("why_not_others", []),
                "units_history": units_history,
                "final_company": row.get("final_company") or canonical_coy,
                "final_position": row.get("final_position") or rec_pos,
                "decision_type": row.get("decision_type") or "pending",
                "decision_remarks": row.get("decision_remarks") or "",
                "decided_by": row.get("decided_by") or "",
                "decided_at": row.get("decided_at").strftime("%d-%m-%Y %H:%M") if row.get("decided_at") else "",
                "hierarchy": UNIT_15_CESR_STRUCTURE,
                "available_companies": get_all_companies(),
                "company_sections_map": {coy: get_sections_for_company(coy) for coy in get_all_companies()},
                "company_positions_map": {coy: get_positions_for_company(coy) for coy in get_all_companies()},
                "user_role": user_role,
                "can_add_remarks": (is_adjutant or is_2ic),
                "can_assign_company": is_2ic,
                "is_read_only": is_co
            }
        })
    except Exception as e:
        print(f"Error in api_get_insight_detail: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# 4. EXECUTIVE DECISION WORKFLOW (ROLE-BASED: CO / ADJUTANT / 2IC)
# =============================================================================

@company_rec_bp.route("/api/ai/company-recommendation/decision", methods=["POST"])
def api_record_decision():
    """
    Record executive decision or remarks on a recommendation.
    Rules:
    - CO: Strictly READ-ONLY.
    - ADJUTANT: Can add / update remarks only.
    - 2IC / ADMIN: Authorized to assign company, modify placement, and execute final assignment into personnel.
    """
    user = require_login()
    if not user:
        return jsonify({"success": False, "error": "Authentication required"}), 401

    user_role = str(user.get("role", "")).strip().upper()

    if user_role in ["CO", "COMMANDING OFFICER"]:
        return jsonify({
            "success": False,
            "error": "Access Denied: Role CO has read-only access. You cannot modify recommendation records."
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
        cursor.execute("SELECT * FROM ai_new_joinee_recommendations WHERE id = %s", (rec_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Record not found"}), 404

        user_id = str(user.get("user_id", user.get("id", "1")))
        decided_by_str = f"{user_role} - {user_id}"

        # ADJUTANT: remarks only
        if user_role == "ADJUTANT" or action == "remarks":
            cursor.execute("""
                UPDATE ai_new_joinee_recommendations
                SET decision_remarks = %s,
                    updated_by = %s,
                    updated_by_role = %s,
                    updated_by_user_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                remarks,
                user.get("username", "Adjutant"),
                user_role,
                user_id,
                rec_id
            ))
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Adjutant remarks updated successfully",
                "decision_type": existing.get("decision_type", "pending"),
                "decision_remarks": remarks,
                "decided_by": decided_by_str
            })

        # 2IC / ADMIN: full assignment
        if user_role not in ["2IC", "ADMIN", "SUPER ADMIN"]:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "error": "Access Denied: Only 2IC is authorized to assign companies and finalize postings."
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

        update_sql = """
            UPDATE ai_new_joinee_recommendations
            SET decision_type = %s,
                decision_remarks = %s,
                final_company = %s,
                final_position = %s,
                decided_by = %s,
                decided_at = NOW(),
                updated_by = %s,
                updated_by_role = %s,
                updated_by_user_id = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(update_sql, (
            decision_type,
            remarks,
            final_coy_val,
            final_pos_val,
            decided_by_str,
            user.get("username", "Officer"),
            user_role,
            user_id,
            rec_id
        ))
        conn.commit()

        # If accepted, sync company & section to personnel record
        if decision_type == "accepted" and existing.get("personnel_id"):
            db_coy_val = to_db_company_name(final_coy_val)
            pos_sec = get_section_for_position(final_coy_val, final_pos_val)
            cursor.execute(
                "UPDATE personnel SET company = %s, section = %s WHERE id = %s",
                (db_coy_val, pos_sec, existing["personnel_id"])
            )
            conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Recommendation successfully {decision_type} by 2IC",
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
        user = require_login()
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
        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN decision_type = 'pending' THEN 1 ELSE 0 END) as pending FROM ai_new_joinee_recommendations")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        total = int(row["total"] or 0)
        pending = int(row["pending"] or 0)

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

