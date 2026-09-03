"""
Flask Blueprint & REST API Routes for AI/ML Individual Fitness Trend.
Isolates all fitness routes, UI views, PDF exports, and ML retraining endpoints.
"""

import os
import sys
import re
import logging
from datetime import datetime
from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    send_file,
    redirect,
    url_for,
    make_response
)

# Configure blueprint logger
logger = logging.getLogger("fitness_trend.routes")

# Import authentication helper from UMS root middleware
try:
    from middleware import require_login
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from middleware import require_login

from .api import (
    analyze_personnel_fitness,
    search_personnel_records,
    trigger_retraining
)
from .prediction.predictor import get_model_info
from .reports.fitness_report import generate_fitness_pdf_report, generate_fitness_html_report

# Initialize Blueprint with isolated templates and static assets
fitness_trend_bp = Blueprint(
    "fitness_trend_bp",
    __name__,
    url_prefix="/fitness",
    template_folder="templates",
    static_folder="static"
)


@fitness_trend_bp.route("/", methods=["GET"])
def fitness_dashboard_view():
    """
    Renders the main interactive AI/ML Individual Fitness Prediction interface.
    """
    user_payload = require_login()
    if not user_payload:
        return redirect("/admin_login")
        
    role = user_payload.get('role', 'User')
    current_user_name = user_payload.get('name') or user_payload.get('username') or 'Personnel'
    company = user_payload.get('company', 'Unit HQ')
    
    return render_template(
        "fitness_trend/index.html",
        role=role,
        current_user_name=current_user_name,
        company=company,
        header="15 CESR UMS"
    )


@fitness_trend_bp.route("/api/personnel-list", methods=["GET"])
def api_search_personnel():
    """
    API endpoint for personnel autocomplete and search.
    Query params: q (search text), limit (integer)
    """
    user_payload = require_login()
    if not user_payload:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 50))
    result = search_personnel_records(q, limit)
    return jsonify(result)


@fitness_trend_bp.route("/api/analyze", methods=["POST"])
def api_analyze_fitness():
    """
    Primary AI Fitness Prediction API endpoint.
    JSON payload: {"army_number": "15744604X", "goal": "Overall Fitness"}
    """
    user_payload = require_login()
    if not user_payload:
        return jsonify({'success': False, 'error': 'Unauthorized. Please login.'}), 401
        
    data = request.get_json(silent=True) or {}
    army_number = data.get("army_number", "").strip()
    goal = data.get("goal", "Overall Fitness").strip()
    
    if not army_number:
        return jsonify({'success': False, 'error': 'Missing required parameter "army_number".'}), 400
        
    try:
        result = analyze_personnel_fitness(army_number, goal=goal)
        if not result.get('success'):
            return jsonify(result), 404
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in analyze_fitness for {army_number}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An internal error occurred while analyzing soldier fitness. Please check logs.'
        }), 500


@fitness_trend_bp.route("/api/model-info", methods=["GET"])
def api_model_info():
    """
    Returns active ML model version, metrics, and dataset statistics.
    """
    user_payload = require_login()
    if not user_payload:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    info = get_model_info()
    return jsonify({'success': True, 'data': info})


@fitness_trend_bp.route("/api/retrain", methods=["POST"])
def api_retrain_model():
    """
    Triggers manual retraining of the fitness classification and regression models.
    """
    user_payload = require_login()
    if not user_payload:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    # Allow retrain only for administrative or officer roles
    role = (user_payload.get('role') or '').upper()
    allowed_roles = ['CO', '2IC', 'ADJUTANT', 'OC', 'NCO IT', 'ADMIN', 'DEVELOPER']
    if role not in allowed_roles:
        return jsonify({'success': False, 'error': 'Insufficient permissions to trigger model retraining.'}), 403
        
    data = request.get_json(silent=True) or {}
    version = data.get('version', 'v1')
    
    result = trigger_retraining(version=version)
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 500


@fitness_trend_bp.route("/report/preview/<army_number>", methods=["GET"])
def preview_fitness_report(army_number):
    """
    Renders the printable HTML view of the Personalized Fitness Report.
    """
    user_payload = require_login()
    if not user_payload:
        return redirect("/admin_login")
        
    goal = request.args.get("goal", "Overall Fitness")
    result = analyze_personnel_fitness(army_number, goal=goal)
    
    if not result.get('success'):
        return render_template(
            "fitness_trend/index.html",
            error_message=result.get('error', 'Soldier record not found.'),
            role=user_payload.get('role', 'User')
        ), 404
        
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
    client_ip = raw_ip.split(',')[0].strip() if raw_ip else '127.0.0.1'
    
    html = generate_fitness_html_report(
        soldier_features=result['soldier'],
        prediction_result=result['prediction'],
        recommendations=result['recommendations'],
        progression_data=result['progression'],
        client_ip=client_ip
    )
    
    response = make_response(html)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@fitness_trend_bp.route("/report/pdf/<army_number>", methods=["GET"])
def download_fitness_pdf(army_number):
    """
    Generates and streams the downloadable PDF Personalized Fitness Report with watermark and unique timestamp.
    """
    user_payload = require_login()
    if not user_payload:
        return redirect("/admin_login")
        
    goal = request.args.get("goal", "Overall Fitness")
    result = analyze_personnel_fitness(army_number, goal=goal)
    
    if not result.get('success'):
        return jsonify({'error': result.get('error', 'Soldier record not found.')}), 404
        
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
    client_ip = raw_ip.split(',')[0].strip() if raw_ip else '127.0.0.1'
    
    pdf_stream = generate_fitness_pdf_report(
        soldier_features=result['soldier'],
        prediction_result=result['prediction'],
        recommendations=result['recommendations'],
        progression_data=result['progression'],
        client_ip=client_ip,
        watermark_text="15 CESR REGM"
    )
    
    if not pdf_stream:
        return jsonify({'error': 'Failed to compile PDF report binary stream.'}), 500
        
    raw_name = result.get('soldier', {}).get('name') or ''
    clean_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', raw_name).strip().replace(' ', '_')
    safe_army_no = re.sub(r'[^a-zA-Z0-9_\-]', '_', army_number)
    if clean_name:
        filename = f"{clean_name}_{safe_army_no}_Fitness_Report.pdf"
    else:
        filename = f"Fitness_Report_{safe_army_no}.pdf"
    
    response = make_response(send_file(
        pdf_stream,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    ))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
