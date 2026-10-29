from imports import *

pending_cases_bp = Blueprint('pending_cases_bp', __name__, url_prefix='/pending_cases')

ALLOWED_ROLES = [
    'CO', 'COMMANDING OFFICER', 'COMMANDINGOFFICER', '2IC', 'ADJUTANT',
    'ACCOUNT OFFICER', 'ACCOUNTS OFFICER', 'ACCOUNT JCO', 'ACCOUNTS JCO',
    'ACCOUNT CLK', 'ACCOUNTS CLK', 'ADMIN', 'SUPERADMIN'
]

@pending_cases_bp.route('/get', methods=['GET'])
def get_pending_cases():
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, type_of_case, pending_last_week, recd_current_week,
                   pub_this_week, under_prog, remarks, updated_by,
                   DATE_FORMAT(updated_at, '%d %b %Y %h:%i %p') AS updated_at,
                   UNIX_TIMESTAMP(updated_at) AS updated_at_ts
            FROM pending_cases
            ORDER BY sort_order ASC
        """)
        rows = cursor.fetchall()
        return jsonify({'success': True, 'data': rows})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@pending_cases_bp.route('/update/<int:row_id>', methods=['POST'])
def update_pending_case(row_id):
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    role = (user.get('role') or '').upper().strip()
    r_clean = role.replace(' ', '').replace('_', '').replace('-', '')
    allowed_upper = [r.upper() for r in ALLOWED_ROLES]
    allowed_clean = [r.replace(' ', '').replace('_', '').replace('-', '') for r in allowed_upper]
    if role not in allowed_upper and r_clean not in allowed_clean:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    data = request.get_json() or {}
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            UPDATE pending_cases
            SET pending_last_week = %s,
                recd_current_week = %s,
                pub_this_week = %s,
                under_prog = %s,
                remarks = %s,
                updated_by = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (
            int(data.get('pending_last_week') or 0),
            int(data.get('recd_current_week') or 0),
            int(data.get('pub_this_week') or 0),
            int(data.get('under_prog') or 0),
            str(data.get('remarks') or '').strip(),
            user.get('name') or user.get('username') or 'Authority',
            row_id
        ))
        conn.commit()

        cursor.execute("""
            SELECT DATE_FORMAT(updated_at, '%d %b %Y %h:%i %p') AS updated_at,
                   UNIX_TIMESTAMP(updated_at) AS updated_at_ts
            FROM pending_cases WHERE id = %s
        """, (row_id,))
        updated_info = cursor.fetchone()

        return jsonify({
            'success': True,
            'updated_at': updated_info['updated_at'] if updated_info else None,
            'updated_at_ts': updated_info['updated_at_ts'] if updated_info else None
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
