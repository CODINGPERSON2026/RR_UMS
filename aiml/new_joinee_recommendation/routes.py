import json
from typing import Optional
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from middleware import require_login
from db_config import get_db_connection

from .recommendation_service import CompanyRecommendationService
from .analytics import get_analytics_data
from .retrain import check_retrain_status, execute_retraining
from .utils import get_logger, CustomJSONEncoder

logger = get_logger("routes")
company_rec_bp = Blueprint("company_recommendation", __name__)

# Singleton recommendation service instance
rec_service = CompanyRecommendationService()

@company_rec_bp.route("/company-recommendation-test", methods=["GET"])
@company_rec_bp.route("/aiml/new-joinee/recommendation", methods=["GET"])
@company_rec_bp.route("/aiml/new-joinee", methods=["GET"])
@company_rec_bp.route("/ai_new_joinee", methods=["GET"])
@company_rec_bp.route("/ai-new-joinee", methods=["GET"])
@company_rec_bp.route("/aiml/new-joinee/recommendation/<int:personnel_id>", methods=["GET"])
def company_recommendation_test_page(personnel_id: int = None):
    """
    Testing dashboard for AI New Joinee Company Recommendation System.
    """
    user = require_login()
    if not user:
        return redirect(url_for("admin_login"))

    # If ID provided in URL path or query params
    selected_id = personnel_id or request.args.get("personnel_id")
    try:
        if selected_id:
            selected_id = int(selected_id)
    except ValueError:
        selected_id = None

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, name, army_number, `rank`, trade, company, date_of_enrollment
                FROM personnel
                ORDER BY id DESC
                LIMIT 150
            """)
            personnel_list = cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching personnel for test dropdown: {e}")
        finally:
            conn.close()

    # Load analytics & retrain status
    analytics = get_analytics_data()
    retrain_status = check_retrain_status()

    # If an ID is selected, get prediction for it
    sample_recommendation = None
    if selected_id:
        sample_recommendation = rec_service.get_recommendation_for_personnel_id(selected_id)

    return render_template(
        "testing/company_recommendation_test.html",
        personnel_list=personnel_list,
        selected_id=selected_id,
        sample_recommendation=sample_recommendation,
        analytics=analytics,
        retrain_status=retrain_status
    )

@company_rec_bp.route("/api/ai/company-recommendation/<int:personnel_id>", methods=["GET"])
def api_get_company_recommendation(personnel_id: int):
    """
    REST API endpoint returning company assignment probabilities & explainability for a given personnel ID.
    """
    try:
        res = rec_service.get_recommendation_for_personnel_id(personnel_id)
        status_code = 200 if res.get("success") else 404
        return jsonify(res), status_code
    except Exception as e:
        logger.error(f"API Error for personnel_id={personnel_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

from .validator import validate_recommendation_payload

@company_rec_bp.route("/api/ai/company-recommendation/predict", methods=["POST"])
def api_predict_custom_payload():
    """
    REST API endpoint returning company assignment probabilities for a custom/new joinee JSON payload.
    """
    try:
        data = request.get_json(silent=True) or {}
        personnel_dict = {
            "trade": data.get("trade", ""),
            "rank": data.get("rank", ""),
            "prior_station": data.get("prior_station", ""),
            "date_of_enrollment": data.get("date_of_enrollment"),
            "date_of_birth": data.get("date_of_birth"),
            "date_of_tos": data.get("date_of_tos"),
            "date_of_tors": data.get("date_of_tors"),
            "detailed_course": data.get("detailed_course", "")
        }
        units_list = data.get("units", [])

        # Server-side validation
        is_valid, errors = validate_recommendation_payload(personnel_dict, units_list)
        if not is_valid:
            return jsonify({
                "success": False,
                "errors": errors,
                "error": errors[0] if errors else "Validation failed."
            }), 400
        
        res = rec_service.get_recommendation_for_payload(personnel_dict, units_list)
        status_code = 200 if res.get("success") else 400
        return jsonify(res), status_code
    except Exception as e:
        logger.error(f"API Error for custom payload: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@company_rec_bp.route("/api/ai/company-recommendation/analytics", methods=["GET"])
def api_get_analytics():
    """
    REST API returning model comparison, confusion matrix, and feature importance data.
    """
    try:
        data = get_analytics_data()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"API Error fetching analytics: {e}")
        return jsonify({"error": str(e)}), 500

@company_rec_bp.route("/api/ai/company-recommendation/retrain-status", methods=["GET"])
def api_get_retrain_status():
    """
    REST API returning auto-retraining threshold progress.
    """
    try:
        status = check_retrain_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"API Error fetching retrain status: {e}")
        return jsonify({"error": str(e)}), 500

@company_rec_bp.route("/api/ai/company-recommendation/retrain", methods=["POST"])
def api_trigger_retrain():
    """
    Admin trigger for retraining models and updating production weights in memory.
    """
    user = require_login()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        force = request.args.get("force", "false").lower() == "true"
        res = execute_retraining(force=force)
        if res.get("success"):
            rec_service.reload_model()
        return jsonify(res), 200 if res.get("success") else 400
    except Exception as e:
        logger.error(f"API Error during retraining: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# =========================================================================
# AI NEW JOINEE RECOMMENDATION INSIGHTS FOR CO / ADJUTANT / 2IC
# =========================================================================

def _is_authorized_insights_user(user: Optional[dict]) -> bool:
    """
    Verifies that the logged-in user has role CO, 2IC, ADJUTANT, or ADMIN.
    """
    if not user:
        return False
    role = str(user.get("role", "")).strip().upper()
    company = str(user.get("company", "")).strip()
    allowed_roles = {"CO", "2IC", "ADJUTANT", "ADMIN"}
    if role in allowed_roles:
        return True
    if company in ("Admin", "Center") and ("CO" in role or "2IC" in role or "ADJUTANT" in role or "ADMIN" in role):
        return True
    return False


@company_rec_bp.route("/api/ai/company-recommendation/insights", methods=["GET"])
def api_get_recommendation_insights():
    """
    REST API endpoint for CO / Adjutant / 2IC Recommendation Insights.
    Supports server-side pagination, search by Army Number / Name,
    filters by Company, Rank, Decision, and multi-field sorting.
    """
    user = require_login()
    if not user:
        return jsonify({"success": False, "error": "Authentication required. Please log in."}), 401

    if not _is_authorized_insights_user(user):
        return jsonify({
            "success": False,
            "error": "Access Denied: Only CO, Adjutant, and 2IC can access AI Recommendation Insights."
        }), 403

    try:
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)
        search = request.args.get("search", "", type=str)
        company_filter = request.args.get("company", "ALL", type=str)
        rank_filter = request.args.get("rank", "ALL", type=str)
        decision_filter = request.args.get("decision", "ALL", type=str)
        sort_by = request.args.get("sort_by", "percentage", type=str)
        sort_order = request.args.get("sort_order", "desc", type=str)

        res = rec_service.get_insights_page(
            page=page,
            page_size=page_size,
            search=search,
            company_filter=company_filter,
            rank_filter=rank_filter,
            decision_filter=decision_filter,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return jsonify(res), 200 if res.get("success") else 500
    except Exception as e:
        logger.error(f"API Error fetching recommendation insights: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Unable to load AI recommendation insights. Please try again."}), 500


@company_rec_bp.route("/api/ai/company-recommendation/insights/<int:rec_id>", methods=["GET"])
def api_get_single_recommendation_insight(rec_id: int):
    """
    REST API endpoint returning complete deep-dive AI analysis for a single recommendation.
    Includes SHAP values, probability breakdowns, and complete previous unit postings.
    """
    user = require_login()
    if not user:
        return jsonify({"success": False, "error": "Authentication required."}), 401

    if not _is_authorized_insights_user(user):
        return jsonify({"success": False, "error": "Access Denied."}), 403

    try:
        res = rec_service.get_single_insight(rec_id)
        status_code = 200 if res.get("success") else 404
        return jsonify(res), status_code
    except Exception as e:
        logger.error(f"API Error fetching single insight #{rec_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Unable to load AI analysis."}), 500


@company_rec_bp.route("/api/ai/company-recommendation/decision", methods=["POST"])
def api_save_manual_decision():
    """
    REST API endpoint for CO / Adjutant / 2IC to record a final posting decision.
    Guarantees that recommended_company is preserved as the single source of AI truth.
    """
    user = require_login()
    if not user:
        return jsonify({"success": False, "error": "Authentication required."}), 401

    if not _is_authorized_insights_user(user):
        return jsonify({"success": False, "error": "Access Denied: Only CO, Adjutant, and 2IC can record posting decisions."}), 403

    try:
        data = request.get_json(silent=True) or {}
        rec_id = data.get("id")
        final_company = data.get("final_company")
        decision_type = data.get("decision_type", "Manual")
        decision_remarks = data.get("decision_remarks", "")
        decided_by = user.get("username", "Officer")

        if not rec_id or not final_company:
            return jsonify({"success": False, "error": "Missing recommendation ID or final company."}), 400

        res = rec_service.save_manual_decision(
            rec_id=int(rec_id),
            final_company=final_company,
            decision_type=decision_type,
            decision_remarks=decision_remarks,
            decided_by=decided_by
        )
        return jsonify(res), 200 if res.get("success") else 400
    except Exception as e:
        logger.error(f"API Error saving decision: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Failed to save posting decision."}), 500


@company_rec_bp.route("/api/ai/company-recommendation/insights-count", methods=["GET"])
def api_get_insights_count():
    """
    REST API endpoint returning total recommendation counts for dashboard stats badges.
    """
    user = require_login()
    if not user:
        return jsonify({"success": False, "error": "Authentication required."}), 401

    if not _is_authorized_insights_user(user):
        return jsonify({"success": False, "error": "Access Denied."}), 403

    try:
        res = rec_service.get_insights_counts()
        return jsonify(res), 200
    except Exception as e:
        logger.warning(f"Error fetching insights count: {e}")
        return jsonify({"success": False, "total_count": 0}), 500


@company_rec_bp.route("/api/ai/company-recommendation/save-history", methods=["POST"])
def api_save_recommendation_history():
    """
    REST API endpoint to persistently store calculated recommendations from the AI modal into MySQL.
    """
    user = require_login()
    if not user:
        return jsonify({"success": False, "error": "Authentication required."}), 401

    try:
        data = request.get_json(silent=True) or {}
        personnel_id = data.get("personnel_id")
        army_number = data.get("army_number")
        name = data.get("name")
        rank = data.get("rank") or "SOLDIER"
        trade = data.get("trade") or "GENERAL"
        units_list = data.get("units") or []

        rec_res = {
            "recommended_company": data.get("recommended_company", "HQ Coy"),
            "confidence": data.get("confidence", "Moderate Match Confidence"),
            "top_percentage": data.get("top_percentage", 50.0),
            "probabilities": data.get("probabilities", {}),
            "reasons": data.get("reasons", []),
            "shap_breakdown": data.get("shap_breakdown", [])
        }

        rec_id = rec_service.persist_recommendation(
            personnel_id=int(personnel_id) if personnel_id else None,
            army_number=army_number,
            name=name,
            rank=rank,
            trade=trade,
            rec_res=rec_res,
            units_list=units_list,
            final_company=data.get("final_company"),
            decision_type=data.get("decision_type", "AI Recommended"),
            decision_remarks=data.get("decision_remarks", "AI Recommended Assignment Accepted"),
            decided_by=user.get("username")
        )

        return jsonify({"success": True, "id": rec_id}), 200
    except Exception as e:
        logger.error(f"API Error saving recommendation history: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

