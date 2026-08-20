import json
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
            "detailed_course": data.get("detailed_course", "")
        }
        units_list = data.get("units", [])
        
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
        force = request.args.get("force", "true").lower() == "true"
        res = execute_retraining(force=force)
        if res.get("success"):
            rec_service.reload_model()
        return jsonify(res), 200 if res.get("success") else 400
    except Exception as e:
        logger.error(f"API Error during retraining: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
