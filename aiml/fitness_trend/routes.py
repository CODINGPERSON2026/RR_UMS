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
    
    from .data.db_loader import fetch_total_weight_info_count
    total_count = fetch_total_weight_info_count()

    return render_template(
        "fitness_trend/index.html",
        role=role,
        current_user_name=current_user_name,
        company=company,
        header="15 CESR UMS",
        total_count=total_count
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
    JSON payload: {"army_number": "15744604X", "goal": "Overall Fitness", "lang": "hi"}
    """
    user_payload = require_login()
    if not user_payload:
        return jsonify({'success': False, 'error': 'Unauthorized. Please login.'}), 401
        
    data = request.get_json(silent=True) or {}
    army_number = data.get("army_number", "").strip()
    goal = data.get("goal", "Overall Fitness").strip()
    lang = (data.get("lang") or data.get("language") or "en").lower().strip()
    
    if not army_number:
        return jsonify({'success': False, 'error': 'Missing required parameter "army_number".'}), 400
        
    try:
        result = analyze_personnel_fitness(army_number, goal=goal)
        if not result.get('success'):
            return jsonify(result), 404

        from .translation import translate_report_data, get_report_labels, is_supported_language
        if not is_supported_language(lang):
            lang = 'en'

        if lang != 'en':
            t_soldier, t_prediction, t_recommendations, t_progression = translate_report_data(
                result['soldier'], result['prediction'], result['recommendations'], result['progression'],
                target_lang=lang, for_pdf=False
            )
            result['soldier'] = t_soldier
            result['prediction'] = t_prediction
            result['recommendations'] = t_recommendations
            result['progression'] = t_progression

        result['labels'] = get_report_labels(target_lang=lang, for_pdf=False)
        result['lang'] = lang
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
    lang = request.args.get("lang", "en").lower().strip()
    from .translation import is_supported_language
    if not is_supported_language(lang):
        lang = "en"

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
        client_ip=client_ip,
        lang=lang
    )
    
    response = make_response(html)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@fitness_trend_bp.route("/report/pdf", methods=["POST"])
@fitness_trend_bp.route("/api/export-pdf", methods=["POST"])
@fitness_trend_bp.route("/api/fitness-trend/export-pdf", methods=["POST"])
def export_fitness_pdf_api():
    """
    API endpoint for Multilingual PDF Report generation.
    Expected JSON:
    {
        "personnel_id": 123,
        "language": "hi",
        "goal": "Overall Fitness"
    }
    """
    logger.info("Fitness PDF generation started")
    user_payload = require_login()
    if not user_payload:
        return jsonify({"success": False, "error": "Unauthorized. Please login."}), 401

    data = request.get_json(silent=True) or {}
    personnel_id = data.get("personnel_id")
    army_number = data.get("army_number")
    language = (data.get("language") or data.get("lang") or "en").lower().strip()
    goal = data.get("goal", "Overall Fitness")

    logger.info(f"Language selected: {language}")

    # 1. Validate language code
    from .translation.language_config import is_supported_language
    if not is_supported_language(language):
        logger.warning(f"Unsupported language code requested: {language}. Falling back to English.")
        return jsonify({
            "success": False,
            "error": f"Unsupported language: '{language}'"
        }), 400

    # 2. Resolve army_number from personnel_id if needed
    target_army_no = None
    if army_number:
        target_army_no = str(army_number).strip()
    elif personnel_id is not None:
        p_str = str(personnel_id).strip()
        if p_str.isdigit():
            from .data.db_loader import get_db_connection
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT army_number FROM personnel WHERE id = %s", (int(p_str),))
                    row = cursor.fetchone()
                    if row and row.get("army_number"):
                        target_army_no = row["army_number"]
                finally:
                    cursor.close()
                    conn.close()
        if not target_army_no:
            target_army_no = p_str

    if not target_army_no:
        return jsonify({
            "success": False,
            "error": "Missing required parameter 'personnel_id' or 'army_number'."
        }), 400

    # 3. Analyze fitness
    result = analyze_personnel_fitness(target_army_no, goal=goal)
    if not result.get("success"):
        return jsonify({
            "success": False,
            "error": result.get("error", "Soldier record not found.")
        }), 404

    # 4. Generate PDF using multilingual generator
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
    client_ip = raw_ip.split(',')[0].strip() if raw_ip else '127.0.0.1'

    try:
        from .pdf.report_generator import generate_multilingual_fitness_pdf
        pdf_stream = generate_multilingual_fitness_pdf(
            soldier_features=result['soldier'],
            prediction_result=result['prediction'],
            recommendations=result['recommendations'],
            progression_data=result['progression'],
            client_ip=client_ip,
            watermark_text="UMS 15 CESR",
            language=language
        )
    except Exception as e:
        logger.error(f"Error generating multilingual PDF for {target_army_no} in '{language}': {e}", exc_info=True)
        return jsonify({"success": False, "error": "Failed to generate report PDF."}), 500

    if not pdf_stream:
        return jsonify({"success": False, "error": "Failed to compile report PDF stream."}), 500

    logger.info(f"PDF generated successfully for language: {language}")

    safe_army_no = re.sub(r'[^a-zA-Z0-9_\-]', '', target_army_no)
    lang_suffix = language.upper()
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"UMS_Fitness_Report_{safe_army_no}_{lang_suffix}_{date_str}.pdf"

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


@fitness_trend_bp.route("/report/pdf/<army_number>", methods=["GET"])
def download_fitness_pdf(army_number):
    """
    Generates and streams the downloadable PDF Personalized Fitness Report with watermark and unique timestamp.
    """
    user_payload = require_login()
    if not user_payload:
        return redirect("/admin_login")
        
    goal = request.args.get("goal", "Overall Fitness")
    lang = request.args.get("lang", "en").lower().strip()
    
    result = analyze_personnel_fitness(army_number, goal=goal)
    
    if not result.get('success'):
        return jsonify({'error': result.get('error', 'Soldier record not found.')}), 404
        
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
    client_ip = raw_ip.split(',')[0].strip() if raw_ip else '127.0.0.1'
    
    from .pdf.report_generator import generate_multilingual_fitness_pdf
    pdf_stream = generate_multilingual_fitness_pdf(
        soldier_features=result['soldier'],
        prediction_result=result['prediction'],
        recommendations=result['recommendations'],
        progression_data=result['progression'],
        client_ip=client_ip,
        watermark_text="UMS 15 CESR",
        language=lang
    )
    
    if not pdf_stream:
        return jsonify({'error': 'Failed to compile PDF report binary stream.'}), 500
        
    safe_army_no = re.sub(r'[^a-zA-Z0-9_\-]', '', army_number)
    lang_suffix = lang.upper()
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"UMS_Fitness_Report_{safe_army_no}_{lang_suffix}_{date_str}.pdf"
    
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
