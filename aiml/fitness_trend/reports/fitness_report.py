"""
Professional Individual Fitness Report Generator.
Renders HTML and converts to PDF using xhtml2pdf / pisa with military styling,
and overlays an official diagonal watermark with '15 CESR REGM', IP address, and timestamp.
"""

import os
import io
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from ..config import TEMPLATES_DIR, DEFAULT_MODEL_VERSION

logger = logging.getLogger("fitness_trend.reports")


def get_jinja_env():
    """
    Returns configured Jinja2 environment pointing to the fitness templates folder.
    """
    return Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)


def generate_fitness_html_report(soldier_features, prediction_result, recommendations, progression_data, client_ip="127.0.0.1"):
    """
    Renders the standalone printable HTML report string using pdf_template.html.
    """
    env = get_jinja_env()
    template = env.get_template("fitness_trend/pdf_template.html")
    
    rendered_html = template.render(
        soldier=soldier_features,
        prediction=prediction_result,
        recommendations=recommendations,
        progression=progression_data,
        client_ip=client_ip,
        generated_at=datetime.now().strftime("%d %b %Y, %H:%M hrs"),
        model_version=prediction_result.get('model_version', DEFAULT_MODEL_VERSION)
    )
    return rendered_html


def overlay_watermark_on_pdf(base_pdf_stream, client_ip="127.0.0.1", watermark_text="15 CESR REGM"):
    """
    Overlays a subtle, military diagonal watermark on each page of the generated PDF using ReportLab and pypdf.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            from PyPDF2 import PdfReader, PdfWriter

        # Create 1-page watermark PDF in memory
        wm_buffer = io.BytesIO()
        # A4 size in points: 595.27 x 841.89
        c = canvas.Canvas(wm_buffer, pagesize=(595.27, 841.89))
        
        # Position origin at center of the page and rotate 38 degrees
        cx, cy = 595.27 / 2.0, 841.89 / 2.0
        c.translate(cx, cy)
        c.rotate(38)
        
        # Soft grey color with subtle transparency
        c.setFillColor(colors.Color(0.68, 0.70, 0.75))
        try:
            c.setFillAlpha(0.22)
        except Exception:
            pass
            
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(0, 40, watermark_text)
        
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(0, 5, f"IP: {client_ip}")
        
        c.setFont("Helvetica", 13)
        c.drawCentredString(0, -25, datetime.now().strftime('%d/%m/%Y %I:%M %p'))
        
        c.showPage()
        c.save()
        wm_buffer.seek(0)
        
        # Merge watermark onto each page
        base_pdf_stream.seek(0)
        base_reader = PdfReader(base_pdf_stream)
        wm_reader = PdfReader(wm_buffer)
        wm_page = wm_reader.pages[0]
        
        writer = PdfWriter()
        for page in base_reader.pages:
            new_page = writer.add_page(page)
            new_page.merge_page(wm_page)
            
        final_stream = io.BytesIO()
        writer.write(final_stream)
        final_stream.seek(0)
        return final_stream
    except Exception as wm_err:
        logger.warning(f"Watermark overlay failed, returning base PDF stream: {wm_err}")
        base_pdf_stream.seek(0)
        return base_pdf_stream


def generate_fitness_pdf_report(soldier_features, prediction_result, recommendations, progression_data, client_ip="127.0.0.1", watermark_text="15 CESR REGM"):
    """
    Generates a high-quality PDF binary stream with AI prediction, recommendations, progression,
    and an official '15 CESR REGM' with IP address watermark.
    
    Returns:
        io.BytesIO stream containing the generated PDF document, or None if error occurs.
    """
    try:
        html_content = generate_fitness_html_report(
            soldier_features, prediction_result, recommendations, progression_data, client_ip=client_ip
        )
        
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(
            src=io.StringIO(html_content),
            dest=pdf_buffer,
            encoding='utf-8'
        )
        
        if pisa_status.err:
            logger.error(f"pisa CreatePDF returned error: {pisa_status.err}")
            return None
            
        pdf_buffer.seek(0)
        
        # Apply diagonal watermark with IP address
        watermarked_pdf = overlay_watermark_on_pdf(
            pdf_buffer, client_ip=client_ip, watermark_text=watermark_text
        )
        return watermarked_pdf
    except Exception as e:
        logger.error(f"Failed to generate fitness PDF report: {e}")
        return None
