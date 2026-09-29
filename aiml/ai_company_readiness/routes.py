"""
Flask Blueprint & REST API Routes for AI Company Readiness.
Enforces authentication via middleware.require_login and role-based access.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from functools import wraps
from typing import Dict, Any, Optional

from middleware import require_login
from .utils import SUPPORTED_COMPANIES, normalize_company_name, DISPLAY_NAMES
from .services import CompanyReadinessService

# Create Blueprint
ai_company_readiness_bp = Blueprint(
    "ai_company_readiness_bp",
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Initialize service
service = CompanyReadinessService()

# Authorized roles for executive readiness review
AUTHORIZED_READINESS_ROLES = [
    "CO", "2IC", "ADJUTANT", "OC", "ADMIN", "SUPER ADMIN",
    "COMMANDING OFFICER", "HEAD CLK", "CLERK", "JCO", "TRG", "PA"
]


def auth_required(f):
    """Decorator ensuring valid JWT session and passing user_payload."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        payload = require_login()
        if not payload:
            if request.path.startswith("/ai-company-readiness/api/"):
                return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
            return redirect("/admin_login")
        return f(payload, *args, **kwargs)
    return decorated_function


# ==========================================================
# UI HTML VIEWS
# ==========================================================

@ai_company_readiness_bp.route("/ai-company-readiness", methods=["GET"])
@auth_required
def dashboard_view(user_payload):
    """Main AI Company Readiness Dashboard showing 3 target companies."""
    data = service.get_dashboard_summary()
    return render_template(
        "ai_company_readiness/dashboard.html",
        dashboard=data,
        supported_companies=SUPPORTED_COMPANIES,
        display_names=DISPLAY_NAMES,
        role=user_payload.get("role", "CO"),
        username=user_payload.get("username", "Officer"),
        current_user_name=user_payload.get("username", "Officer"),
        company=user_payload.get("company", "")
    )


@ai_company_readiness_bp.route("/ai-company-readiness/company/<company>", methods=["GET"])
@auth_required
def company_details_view(user_payload, company):
    """Detailed view for a specific company's readiness dimensions and gaps."""
    canonical = normalize_company_name(company)
    if not canonical or canonical not in SUPPORTED_COMPANIES:
        return redirect("/ai-company-readiness")

    readiness = service.get_company_readiness(canonical)
    if not readiness:
        return redirect("/ai-company-readiness")

    # Get ML prediction
    conn = service.get_company_readiness  # predictor attached to service
    prediction = readiness.recommendations  # recommendations already attached

    return render_template(
        "ai_company_readiness/company_details.html",
        company=canonical,
        readiness=readiness,
        display_name=DISPLAY_NAMES.get(canonical, canonical),
        role=user_payload.get("role", "CO"),
        username=user_payload.get("username", "Officer"),
        current_user_name=user_payload.get("username", "Officer")
    )


@ai_company_readiness_bp.route("/ai-company-readiness/company/<company>/gaps", methods=["GET"])
@auth_required
def gap_details_view(user_payload, company):
    """Specific gap details and drill-down page."""
    canonical = normalize_company_name(company)
    if not canonical or canonical not in SUPPORTED_COMPANIES:
        return redirect("/ai-company-readiness")

    gap_type = request.args.get("type", "Strength")
    gap_name = request.args.get("name", gap_type)

    readiness = service.get_company_readiness(canonical)
    personnel_list = service.get_gap_drilldown(canonical, gap_type, gap_name)

    return render_template(
        "ai_company_readiness/gap_details.html",
        company=canonical,
        readiness=readiness,
        gap_type=gap_type,
        gap_name=gap_name,
        personnel_list=personnel_list,
        display_name=DISPLAY_NAMES.get(canonical, canonical),
        role=user_payload.get("role", "CO"),
        username=user_payload.get("username", "Officer"),
        current_user_name=user_payload.get("username", "Officer")
    )


@ai_company_readiness_bp.route("/ai-company-readiness/company/<company>/prediction", methods=["GET"])
@auth_required
def prediction_view(user_payload, company):
    """AI/ML Prediction details and contributing factors."""
    canonical = normalize_company_name(company)
    if not canonical or canonical not in SUPPORTED_COMPANIES:
        return redirect("/ai-company-readiness")

    readiness = service.get_company_readiness(canonical)
    # Re-evaluate prediction object
    conn_pred = service.predictor
    from .queries import fetch_company_personnel, fetch_personnel_weight_info
    from db_config import get_db_connection
    conn = get_db_connection()
    personnel = fetch_company_personnel(conn, canonical)
    army_numbers = [p["army_number"] for p in personnel if p.get("army_number")]
    weight_info = fetch_personnel_weight_info(conn, army_numbers)
    conn.close()

    prediction = conn_pred.get_prediction(readiness, personnel, weight_info)

    return render_template(
        "ai_company_readiness/prediction.html",
        company=canonical,
        readiness=readiness,
        prediction=prediction,
        display_name=DISPLAY_NAMES.get(canonical, canonical),
        role=user_payload.get("role", "CO"),
        username=user_payload.get("username", "Officer"),
        current_user_name=user_payload.get("username", "Officer")
    )


# ==========================================================
# REST API ENDPOINTS
# ==========================================================

@ai_company_readiness_bp.route("/ai-company-readiness/api/dashboard", methods=["GET"])
@auth_required
def api_dashboard(user_payload):
    """JSON API returning current readiness for all 3 companies."""
    try:
        data = service.get_dashboard_summary()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_company_readiness_bp.route("/ai-company-readiness/api/company/<company>", methods=["GET"])
@auth_required
def api_company_details(user_payload, company):
    """JSON API returning complete readiness for a specific company."""
    canonical = normalize_company_name(company)
    if not canonical or canonical not in SUPPORTED_COMPANIES:
        return jsonify({"success": False, "error": f"Company '{company}' not supported"}), 404

    try:
        readiness = service.get_company_readiness(canonical)
        if not readiness:
            return jsonify({"success": False, "error": "Company not found"}), 404
        return jsonify({"success": True, "data": readiness.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_company_readiness_bp.route("/ai-company-readiness/company/<company>/personnel", methods=["GET"])
@auth_required
def api_gap_personnel(user_payload, company):
    """JSON API returning personnel drill-down for a gap."""
    canonical = normalize_company_name(company)
    if not canonical or canonical not in SUPPORTED_COMPANIES:
        return jsonify({"success": False, "error": f"Company '{company}' not supported"}), 404

    gap_type = request.args.get("gap_type") or request.args.get("type", "Strength")
    gap_name = request.args.get("gap_name") or request.args.get("name", gap_type)

    try:
        personnel = service.get_gap_drilldown(canonical, gap_type, gap_name)
        return jsonify({
            "success": True,
            "company": canonical,
            "gap_type": gap_type,
            "gap_name": gap_name,
            "count": len(personnel),
            "personnel": [p.__dict__ for p in personnel]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_company_readiness_bp.route("/ai-company-readiness/api/snapshot", methods=["POST"])
@auth_required
def api_save_snapshot(user_payload):
    """Records current readiness calculations into historical tracking table."""
    try:
        ids = service.record_current_snapshots()
        return jsonify({
            "success": True,
            "message": f"Successfully captured readiness snapshot for {len(ids)} companies",
            "snapshot_ids": ids
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_company_readiness_bp.route("/ai-company-readiness/requirements", methods=["GET"])
@auth_required
def requirements_view(user_payload):
    """View and manage operational baseline requirements."""
    reqs = service.get_all_requirements()
    return render_template(
        "ai_company_readiness/requirements.html",
        requirements=reqs,
        supported_companies=SUPPORTED_COMPANIES,
        display_names=DISPLAY_NAMES,
        role=user_payload.get("role", "CO"),
        username=user_payload.get("username", "Officer"),
        current_user_name=user_payload.get("username", "Officer")
    )


@ai_company_readiness_bp.route("/ai-company-readiness/api/requirements", methods=["GET", "POST"])
@auth_required
def api_requirements(user_payload):
    """REST API for fetching and updating baseline requirements."""
    if request.method == "GET":
        reqs = service.get_all_requirements()
        return jsonify({"success": True, "data": reqs})

    # POST: create or update requirement
    data = request.get_json() or {}
    company = data.get("company")
    canonical = normalize_company_name(company)
    if not canonical or canonical not in SUPPORTED_COMPANIES:
        return jsonify({"success": False, "error": "Invalid company formation"}), 400

    req_type = data.get("requirement_type")
    if not req_type:
        return jsonify({"success": False, "error": "Requirement type is required"}), 400

    req_name = data.get("requirement_name")
    if not req_name:
        return jsonify({"success": False, "error": "Requirement name is required"}), 400

    try:
        req_count = int(data.get("required_count", 0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid required count"}), 400

    payload = {
        "id": data.get("id"),
        "company": canonical,
        "requirement_type": req_type,
        "requirement_name": req_name,
        "required_count": req_count,
        "priority": data.get("priority", "Medium"),
        "status": data.get("status", "Active")
    }

    try:
        saved_id = service.save_requirement(payload)
        return jsonify({
            "success": True,
            "message": "Requirement saved successfully",
            "id": saved_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_company_readiness_bp.route("/ai-company-readiness/api/requirements/<int:req_id>/delete", methods=["POST"])
@auth_required
def api_delete_requirement(user_payload, req_id):
    """Deletes or archives a baseline requirement."""
    try:
        deleted = service.remove_requirement(req_id)
        if deleted:
            return jsonify({"success": True, "message": "Requirement deleted successfully"})
        return jsonify({"success": False, "error": "Requirement not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
