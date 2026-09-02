from imports import *
from db_config import get_db_connection

onco_leave_bp = Blueprint('onco_leave', __name__, url_prefix='/onco')


def require_onco():
    """Return the current user dict if role is ONCO, else return None."""
    user = require_login()
    if not user or user.get('role') != 'ONCO':
        return None
    return user

@onco_leave_bp.route('/manage_leave', methods=['GET'])
def manage_leave():
    user = require_onco()
    if not user:
        return "403 Forbidden – Only ONCO role can access this page.", 403
    return render_template('manage_leave.html')

@onco_leave_bp.route('/api/on_leave_persons', methods=['GET'])
def on_leave_persons():
    user = require_onco()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized. ONCO role required.'}), 403

    company = user.get('company')
    if not company:
        return jsonify({'status': 'error', 'message': 'Company not found in session.'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.army_number,
                p.name,
                p.rank,
                p.company,
                l.leave_type,
                l.from_date,
                l.to_date,
                l.suffix_days,
                l.prefix_days,
                l.suffix_date,
                l.prefix_date,
                l.leave_days,
                l.id AS leave_id
            FROM personnel p
            JOIN leave_status_info l ON p.army_number = l.army_number
            WHERE p.onleave_status = 1
              AND p.company = %s
              AND l.request_status = 'Approved'
            ORDER BY l.to_date
        """, (company,))

        rows = cursor.fetchall()

        for row in rows:
            if row.get('from_date'):
                row['from_date'] = str(row['from_date'])
            if row.get('to_date'):
                row['to_date'] = str(row['to_date'])



            if row['suffix_days']:
                row['to_date'] = str(row['suffix_date'])
                
            if row['prefix_days']:
                row['from_date'] = str(row['prefix_date'])

        return jsonify({'status': 'success', 'data': rows})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@onco_leave_bp.route('/remove_leave', methods=['POST'])
def remove_leave():
    user = require_onco()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized. ONCO role required.'}), 403

    data = request.get_json()
    army_number = data.get('army_number')
    leave_id = data.get('leave_id')

    if not army_number:
        return jsonify({'status': 'error', 'message': 'Army number is required.'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE personnel
            SET onleave_status = 0
            WHERE army_number = %s
        """, (army_number,))
        cursor.execute("""
        Update leave_status_info
                    set request_status  = 'Leave Closed' where id = %s""",(leave_id,)) 
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'status': 'error', 'message': 'Personnel not found.'}), 404

        return jsonify({'status': 'success', 'message': f'Personnel {army_number} removed from leave successfully.'})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@onco_leave_bp.route('/extend_leave', methods=['POST'])
def extend_leave():
    user = require_onco()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized. ONCO role required.'}), 403

    data = request.get_json()
    army_number      = data.get('army_number')
    new_to_date_str  = data.get('new_to_date')
    leave_type       = data.get('leave_type')

    # ── Validate inputs ───────────────────────────────────────────
    if not army_number or not new_to_date_str:
        return jsonify({'status': 'error', 'message': 'army_number and new_to_date are required.'}), 400

    VALID_LEAVE_TYPES = {'AL', 'CL', 'AAL', 'PL'}
    if not leave_type or leave_type not in VALID_LEAVE_TYPES:
        return jsonify({'status': 'error', 'message': 'A valid leave_type (AL/CL/AAL/PL) is required.'}), 400

    conn   = None
    cursor = None
    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ── 1. Fetch current approved leave record ────────────────
        cursor.execute("""
            SELECT id, from_date, to_date, suffix_date, suffix_days, request_status
            FROM leave_status_info
            WHERE army_number = %s
              AND request_status = 'Approved'
            ORDER BY from_date DESC
            LIMIT 1
        """, (army_number,))
        leave = cursor.fetchone()

        if not leave:
            return jsonify({'status': 'error', 'message': 'No approved leave record found for this personnel.'}), 404

        from_date   = leave['from_date']
        old_to_date = leave['to_date']
        suffix_date = leave.get('suffix_date')
        suffix_days = leave.get('suffix_days') or 0
        new_to_date = datetime.strptime(new_to_date_str, '%Y-%m-%d').date()

        if new_to_date <= from_date:
            return jsonify({'status': 'error', 'message': 'New to_date must be after from_date.'}), 400

        if new_to_date <= old_to_date:
            return jsonify({'status': 'error', 'message': 'New to_date must be after the current end date.'}), 400

        # Check if existing suffix_date falls on or before new_to_date
        clear_suffix = False
        if suffix_date:
            if isinstance(suffix_date, str):
                try:
                    suffix_date_obj = datetime.strptime(suffix_date, '%Y-%m-%d').date()
                except ValueError:
                    suffix_date_obj = None
            elif hasattr(suffix_date, 'year'):
                suffix_date_obj = suffix_date
            else:
                suffix_date_obj = None

            if suffix_date_obj and suffix_date_obj <= new_to_date:
                clear_suffix = True

        # ── 2. Calculate extension details ───────────────────────
        ext_start_date   = old_to_date + timedelta(days=1)
        ext_end_date     = new_to_date
        total_leave_days = (new_to_date - from_date).days + 1
        extended_days    = (new_to_date - old_to_date).days

        download_url = (
            f"/onco/download_extension_certificate"
            f"?army_number={army_number}"
            f"&leave_id={leave['id']}"
            f"&ext_from={ext_start_date.strftime('%Y-%m-%d')}"
            f"&ext_to={new_to_date_str}"
            f"&ext_days={extended_days}"
            f"&leave_type={leave_type}"
            f"&old_from={from_date.strftime('%Y-%m-%d')}"
            f"&old_to={old_to_date.strftime('%Y-%m-%d')}"
        )

        # ── 3. Update leave_status_info ───────────────────────────
        if clear_suffix:
            cursor.execute("""
                UPDATE leave_status_info
                SET to_date     = %s,
                    leave_days  = %s,
                    suffix_date = NULL,
                    suffix_days = 0,
                    updated_at  = NOW()
                WHERE id = %s
            """, (new_to_date_str, total_leave_days, leave['id']))
        else:
            cursor.execute("""
                UPDATE leave_status_info
                SET to_date    = %s,
                    leave_days = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (new_to_date_str, total_leave_days, leave['id']))

        # ── 4. Update leave_details ───────────────────────────────
        current_year = str(new_to_date.year)

        cursor.execute(f"""
            UPDATE leave_details
            SET `{leave_type}`  = COALESCE(`{leave_type}`, 0) + %s,
                leave_end_date  = %s
            WHERE army_number = %s
              AND year = %s
        """, (extended_days, new_to_date_str, army_number, current_year))

        # If no row exists for this year, insert one
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO leave_details
                    (army_number, year, AL, CL, AAL, PL, leave_end_date, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'Created on leave extension')
            """, (
                army_number,
                current_year,
                extended_days if leave_type == 'AL'  else 0,
                extended_days if leave_type == 'CL'  else 0,
                extended_days if leave_type == 'AAL' else 0,
                extended_days if leave_type == 'PL'  else 0,
                new_to_date_str,
            ))

        conn.commit()

        return jsonify({
            'status':        'success',
            'message':       f'Leave extended by {extended_days} day(s) under {leave_type}. Total duration: {total_leave_days} days.',
            'new_to_date':   new_to_date_str,
            'leave_days':    total_leave_days,
            'extended_days': extended_days,
            'leave_type':    leave_type,
            'leave_id':      leave['id'],
            'download_url':  download_url
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        if cursor: cursor.close()
        if conn:   conn.close()


@onco_leave_bp.route('/download_extension_certificate', methods=['GET'])
def download_extension_certificate():
    army_number = request.args.get('army_number')
    leave_id    = request.args.get('leave_id')
    ext_from    = request.args.get('ext_from')
    ext_to      = request.args.get('ext_to')
    ext_days    = request.args.get('ext_days')
    leave_type  = request.args.get('leave_type', 'AL')
    old_from    = request.args.get('old_from')
    old_to      = request.args.get('old_to')

    if not army_number or not ext_from or not ext_to:
        return "Missing parameters for extension certificate", 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.army_number, p.name, p.`rank`, p.company AS company_name, p.trade, p.i_card_no,
                   p.home_village, p.home_po, p.home_ps, p.home_district, p.home_state,
                   m.number AS mobile_number
            FROM personnel p
            LEFT JOIN mobile_phones m ON m.army_number = p.army_number
            WHERE TRIM(p.army_number) = %s
            LIMIT 1
        """, (army_number.strip(),))
        applicant = cursor.fetchone() or {'army_number': army_number, 'name': 'Unknown', 'rank': 'N/A'}

        ext_start_date  = datetime.strptime(ext_from, '%Y-%m-%d').date()
        ext_end_date    = datetime.strptime(ext_to, '%Y-%m-%d').date()
        orig_start_date = datetime.strptime(old_from, '%Y-%m-%d').date() if old_from else ext_start_date
        orig_end_date   = datetime.strptime(old_to, '%Y-%m-%d').date() if old_to else ext_start_date - timedelta(days=1)
        reporting_date  = ext_end_date
        revised_total_days = (ext_end_date - orig_start_date).days + 1

        leave_info = {
            'leave_id': leave_id or '1',
            'leave_type': leave_type,
            'extended_days': ext_days or (ext_end_date - ext_start_date).days + 1,
            'ext_start_date': ext_start_date,
            'ext_end_date': ext_end_date,
            'orig_start_date': orig_start_date,
            'orig_end_date': orig_end_date,
            'reporting_date': reporting_date,
            'revised_total_days': revised_total_days
        }

        # Logos & Watermark setup
        from PIL import Image, ImageDraw
        from flask import current_app

        static_dir = os.path.join(current_app.root_path, 'static')
        chinar_logo_path = os.path.abspath(os.path.join(static_dir, 'image_for_login_page', 'chinar.jpg'))
        rt_logo_path     = os.path.abspath(os.path.join(static_dir, 'image_for_login_page', 'rt.jpg'))
        
        chinar_rounded_path = os.path.abspath(os.path.join(static_dir, 'image_for_login_page', 'chinar_rounded.jpg'))
        if not os.path.exists(chinar_rounded_path) and os.path.exists(chinar_logo_path):
            try:
                img = Image.open(chinar_logo_path).convert("RGBA")
                min_dim = min(img.size)
                left = (img.width - min_dim)/2
                top = (img.height - min_dim)/2
                right = (img.width + min_dim)/2
                bottom = (img.height + min_dim)/2
                img = img.crop((left, top, right, bottom))
                
                mask = Image.new("L", img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, min_dim, min_dim), fill=255)
                
                white_bg = Image.new("RGB", img.size, (255, 255, 255))
                white_bg.paste(img, mask=mask)
                white_bg.save(chinar_rounded_path, "JPEG")
            except Exception:
                chinar_rounded_path = chinar_logo_path
        elif not os.path.exists(chinar_logo_path):
            chinar_rounded_path = chinar_logo_path

        raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
        client_ip = raw_ip.split(',')[0].strip() if raw_ip else '127.0.0.1'

        html = render_template(
            "extension_certificate.html", 
            applicant=applicant, 
            leave=leave_info,
            issue_date=datetime.now(),
            chinar_logo_path=chinar_rounded_path,
            rt_logo_path=rt_logo_path,
            client_ip=client_ip
        )

        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
        if pisa_status.err:
            return "Error generating PDF", 500
        
        pdf_buffer.seek(0)

        # Overlay diagonal watermark on PDF using ReportLab + pypdf
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            try:
                from pypdf import PdfReader, PdfWriter
            except ImportError:
                from PyPDF2 import PdfReader, PdfWriter

            # Create 1-page watermark PDF in memory
            wm_buffer = BytesIO()
            c = canvas.Canvas(wm_buffer, pagesize=(595.27, 841.89))  # A4 size in points
            
            # Position origin slightly towards the top of the page and rotate 45 degrees
            cx, cy = 595.27 / 2.0, (841.89 / 2.0) + 60.0
            c.translate(cx, cy)
            c.rotate(45)
            
            # Set soft grey color and opacity
            c.setFillColor(colors.Color(0.72, 0.72, 0.72))
            try:
                c.setFillAlpha(0.35)
            except Exception:
                pass
            c.setFont("Helvetica-Bold", 56)
            
            lines = [
                "15 CORPS UMS",
                f"{client_ip}"
            ]
            
            line_height = 68
            total_h = (len(lines) - 1) * line_height
            start_y = total_h / 2.0
            
            for idx, line in enumerate(lines):
                y = start_y - (idx * line_height)
                c.drawCentredString(0, y, line)
                
            c.showPage()
            c.save()
            wm_buffer.seek(0)

            # Merge watermark page onto each page of base PDF
            base_reader = PdfReader(pdf_buffer)
            wm_reader = PdfReader(wm_buffer)
            wm_page = wm_reader.pages[0]

            writer = PdfWriter()
            for page in base_reader.pages:
                page.merge_page(wm_page)
                writer.add_page(page)

            final_pdf_buffer = BytesIO()
            writer.write(final_pdf_buffer)
            final_pdf_buffer.seek(0)
            download_buffer = final_pdf_buffer

        except Exception as wm_err:
            import traceback
            print("Watermark merge error, falling back to base PDF:", wm_err)
            traceback.print_exc()
            pdf_buffer.seek(0)
            download_buffer = pdf_buffer

        return send_file(
            download_buffer,
            as_attachment=True,
            download_name=f"Leave_Extension_Certificate_{army_number}_{ext_to}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return str(e), 500
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()