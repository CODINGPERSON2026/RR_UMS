"""
Multilingual PDF Report Generator for UMS Fitness Trend.
Orchestrates data translation, font binding, charts, logo headers,
ReportLab compilation, Urdu RTL shaping, and military watermark overlay.
"""

import io
import os
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from ..translation import (
    translate_report_data,
    translate_16section_report,
    get_report_labels,
    is_supported_language,
    is_rtl,
    get_language_name
)
from .font_manager import get_font_manager
from ..reports.fitness_report import (
    build_structured_fitness_report,
    get_certificate_logos,
    get_regiment_banner_uri,
    overlay_watermark_on_pdf
)

logger = logging.getLogger("fitness_trend.pdf.report_generator")


def generate_multilingual_fitness_pdf(
    soldier_features,
    prediction_result,
    recommendations,
    progression_data,
    client_ip="127.0.0.1",
    watermark_text="UMS RR",
    language="en"
):
    """
    Generates a production-ready, publication-quality fitness report PDF in the selected language.
    
    Args:
        soldier_features (dict): Standard soldier particulars (Army no, rank, weight, BMI, etc.)
        prediction_result (dict): ML classification score, category, confidence, strengths/improvements
        recommendations (dict): Diet strategy, caloric targets, macros, exercise drills
        progression_data (dict): 30/60/90 days trajectory projection
        client_ip (str): IP address for audit and watermark stamping
        watermark_text (str): Military unit identifier
        language (str): Supported ISO language code (e.g., 'en', 'hi', 'ur', 'ta', 'bn', etc.)
        
    Returns:
        io.BytesIO: Buffer containing the generated PDF bytes.
    """
    lang = (language or "en").lower().strip()
    if not is_supported_language(lang):
        logger.warning(f"Unsupported language '{lang}' requested. Falling back to English ('en').")
        lang = "en"

    # 1. Register fonts & determine font family
    font_mgr = get_font_manager()
    font_mgr.register_unicode_fonts()
    font_family = font_mgr.get_font_family_for_language(lang)

    # 2. Build 16-section structured report data
    structured_report = build_structured_fitness_report(
        soldier_features=soldier_features,
        prediction_result=prediction_result,
        recommendations=recommendations,
        progression_data=progression_data,
        client_ip=client_ip,
        language=lang
    )

    # 3. Translate human-readable content before PDF generation
    if lang != "en":
        t_report = translate_16section_report(structured_report, target_lang=lang, for_pdf=True)
        labels = get_report_labels(target_lang=lang, for_pdf=True)
    else:
        t_report = structured_report
        labels = get_report_labels(target_lang="en", for_pdf=False)

    # 4. Load official logos & regiment banner
    rt_logo_path, chinar_logo_path = get_certificate_logos()
    banner_image_path = get_regiment_banner_uri() if lang == "en" else ""

    # 5. Generate simplified 90-day physical line graph (Actual vs AI)
    from .chart_generator import generate_progression_line_chart_uri
    progression_chart_uri = generate_progression_line_chart_uri(
        progression_data=t_report.get('progression', progression_data),
        title="90-Day Physical Readiness & Weight Projection Curve",
        lang=lang
    )

    # 6. Render HTML template using Jinja2
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates"
    )
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("fitness_trend/pdf_template.html")

    rendered_html = template.render(
        report=t_report,
        soldier=t_report.get('soldier', soldier_features),
        prediction=t_report.get('prediction', prediction_result),
        recommendations=t_report.get('recommendations', recommendations),
        progression=t_report.get('progression', progression_data),
        labels=labels,
        font_family=font_family,
        lang=lang,
        direction="rtl" if is_rtl(lang) else "ltr",
        is_rtl=is_rtl(lang),
        client_ip=client_ip,
        chinar_logo_path=chinar_logo_path,
        rt_logo_path=rt_logo_path,
        banner_image_path=banner_image_path,
        progression_chart_uri=progression_chart_uri,
        generated_at=t_report.get('generated_at'),
        model_version=prediction_result.get('model_version', 'v1')
    )

    # 5. Compile HTML into PDF using xhtml2pdf / Pisa
    from xhtml2pdf import pisa
    raw_pdf_stream = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        io.StringIO(rendered_html),
        dest=raw_pdf_stream,
        encoding="utf-8"
    )

    if pisa_status.err:
        logger.error(f"Pisa PDF compilation error ({pisa_status.err}) for language '{lang}'.")
        raise RuntimeError(f"PDF generation failed with Pisa status error code: {pisa_status.err}")

    raw_pdf_stream.seek(0)

    # 6. Apply diagonal military watermark and audit metadata
    watermarked_pdf = overlay_watermark_on_pdf(
        raw_pdf_stream,
        client_ip=client_ip,
        watermark_text=watermark_text
    )

    return watermarked_pdf
