from flask import Blueprint, jsonify, request
from db_config import get_db_connection
from middleware import require_login

drone_wpn_bp = Blueprint('drone_wpn_bp', __name__, url_prefix='/drone_wpn')


def ensure_drone_wpn_table(cursor=None, conn=None):
    """
    Ensures the drone_wpn table exists and has all required columns.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    if not conn:
        return False

    c = cursor or conn.cursor()
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS `drone_wpn` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `name` VARCHAR(255) NOT NULL,
                `auth_individuals` VARCHAR(255) DEFAULT '0',
                `held` INT NOT NULL DEFAULT 0,
                `present_in_unit` INT NOT NULL DEFAULT 0,
                `on_leave` INT NOT NULL DEFAULT 0,
                `company` VARCHAR(100) DEFAULT NULL,
                `created_by` VARCHAR(100) DEFAULT NULL,
                `updated_by` VARCHAR(100) DEFAULT NULL,
                `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        # Check if auth_individuals column exists (for existing tables)
        c.execute("SHOW COLUMNS FROM `drone_wpn` LIKE 'auth_individuals'")
        if not c.fetchone():
            c.execute("ALTER TABLE `drone_wpn` ADD COLUMN `auth_individuals` VARCHAR(255) DEFAULT '0' AFTER `name`")

        conn.commit()
        return True
    except Exception as e:
        print(f"[drone_wpn] Error ensuring table: {e}")
        return False
    finally:
        if should_close:
            try:
                c.close()
                conn.close()
            except Exception:
                pass


def is_onco_authorized(user):
    """
    Checks if user is ONCO or admin.
    """
    if not user:
        return False
    role = (user.get('role') or '').upper().strip()
    r_clean = role.replace(' ', '').replace('_', '').replace('-', '')
    if 'ONCO' in role or 'ONCO' in r_clean or role in ['ADMIN', 'SUPERADMIN', 'CO', '2IC']:
        return True
    return False


@drone_wpn_bp.route('/api/list', methods=['GET'])
def get_drone_wpn_list():
    """
    Returns list of all drone_wpn records along with summary totals.
    Supports optional ?company= filter for leadership & company-specific views.
    Columns: name, auth_individuals, held, present_in_unit, on_leave
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    company_filter = request.args.get('company', '').strip()

    cursor = conn.cursor(dictionary=True)
    try:
        ensure_drone_wpn_table(cursor, conn)

        # Collect distinct companies for filter dropdown
        cursor.execute("SELECT DISTINCT company FROM drone_wpn WHERE company IS NOT NULL AND TRIM(company) != '' ORDER BY company ASC")
        c_rows = cursor.fetchall() or []
        distinct_companies = [r['company'] for r in c_rows if r.get('company')]

        default_companies = ['COMN Company', '3 Company', 'HQ Company']
        for dc in default_companies:
            if dc not in distinct_companies:
                distinct_companies.append(dc)

        query = """
            SELECT 
                id, 
                name, 
                COALESCE(auth_individuals, '0') AS auth_individuals,
                held, 
                present_in_unit, 
                on_leave, 
                company, 
                created_by, 
                updated_by, 
                DATE_FORMAT(updated_at, '%d %b %Y %H:%i') AS formatted_updated_at
            FROM drone_wpn
        """
        params = []
        if company_filter and company_filter.upper() != 'ALL':
            query += " WHERE LOWER(TRIM(company)) = LOWER(TRIM(%s))"
            params.append(company_filter)

        query += " ORDER BY id ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall() or []

        # Calculate totals
        def safe_int(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        total_auth = sum(safe_int(r.get('auth_individuals')) for r in rows)
        total_held = sum(safe_int(r.get('held')) for r in rows)
        total_present = sum(safe_int(r.get('present_in_unit')) for r in rows)
        total_leave = sum(safe_int(r.get('on_leave')) for r in rows)

        can_edit = is_onco_authorized(user)

        return jsonify({
            'success': True,
            'data': rows,
            'companies': distinct_companies,
            'selected_company': company_filter or 'ALL',
            'totals': {
                'auth_individuals': total_auth,
                'held': total_held,
                'present_in_unit': total_present,
                'on_leave': total_leave,
                'count': len(rows)
            },
            'can_edit': can_edit,
            'user_role': user.get('role'),
            'user_company': user.get('company')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to fetch drone/wpn records: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()


@drone_wpn_bp.route('/api/add', methods=['POST'])
def add_drone_wpn():
    """
    Adds a new drone/wpn record. Restricted to ONCO / Admin.
    Fields: name, auth_individuals, held, present_in_unit, on_leave
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    if not is_onco_authorized(user):
        return jsonify({'success': False, 'message': 'Forbidden: Only ONCO can add Drone/Wpn entries.'}), 403

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    name = (payload.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'}), 400

    auth_individuals = str(payload.get('auth_individuals') or payload.get('authIndividuals') or '0').strip()

    try:
        held = int(payload.get('held', 0) or 0)
        present_in_unit = int(payload.get('present_in_unit', 0) or payload.get('presentInUnit', 0) or 0)
        on_leave = int(payload.get('on_leave', 0) or payload.get('onLeave', 0) or 0)

        if held < 0 or present_in_unit < 0 or on_leave < 0:
            return jsonify({'success': False, 'message': 'Counts cannot be negative.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Held, Present in Unit, and On Leave must be numbers.'}), 400

    company = user.get('company') or payload.get('company') or ''
    user_name = user.get('name') or user.get('username') or user.get('role') or 'ONCO'

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        ensure_drone_wpn_table(cursor, conn)

        cursor.execute("""
            INSERT INTO drone_wpn (name, auth_individuals, held, present_in_unit, on_leave, company, created_by, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, auth_individuals, held, present_in_unit, on_leave, company, user_name, user_name))
        conn.commit()

        new_id = cursor.lastrowid
        return jsonify({
            'success': True,
            'message': f'"{name}" added successfully.',
            'id': new_id
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Failed to add record: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()


@drone_wpn_bp.route('/api/update/<int:item_id>', methods=['POST', 'PUT'])
def update_drone_wpn(item_id):
    """
    Updates an existing drone/wpn record. Restricted to ONCO / Admin.
    Fields: name, auth_individuals, held, present_in_unit, on_leave
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    if not is_onco_authorized(user):
        return jsonify({'success': False, 'message': 'Forbidden: Only ONCO can update Drone/Wpn entries.'}), 403

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    name = (payload.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'}), 400

    auth_individuals = str(payload.get('auth_individuals') or payload.get('authIndividuals') or '0').strip()

    try:
        held = int(payload.get('held', 0) or 0)
        present_in_unit = int(payload.get('present_in_unit', 0) or payload.get('presentInUnit', 0) or 0)
        on_leave = int(payload.get('on_leave', 0) or payload.get('onLeave', 0) or 0)

        if held < 0 or present_in_unit < 0 or on_leave < 0:
            return jsonify({'success': False, 'message': 'Counts cannot be negative.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Held, Present in Unit, and On Leave must be numbers.'}), 400

    user_name = user.get('name') or user.get('username') or user.get('role') or 'ONCO'

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        ensure_drone_wpn_table(cursor, conn)

        cursor.execute("""
            UPDATE drone_wpn
            SET name = %s, auth_individuals = %s, held = %s, present_in_unit = %s, on_leave = %s, updated_by = %s
            WHERE id = %s
        """, (name, auth_individuals, held, present_in_unit, on_leave, user_name, item_id))
        conn.commit()

        if cursor.rowcount == 0:
            cursor.execute("SELECT id FROM drone_wpn WHERE id = %s", (item_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': 'Record not found.'}), 404

        return jsonify({
            'success': True,
            'message': f'"{name}" updated successfully.'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Failed to update record: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()


@drone_wpn_bp.route('/api/delete/<int:item_id>', methods=['POST', 'DELETE'])
def delete_drone_wpn(item_id):
    """
    Deletes a drone/wpn record. Restricted to ONCO / Admin.
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    if not is_onco_authorized(user):
        return jsonify({'success': False, 'message': 'Forbidden: Only ONCO can delete Drone/Wpn entries.'}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        ensure_drone_wpn_table(cursor, conn)

        cursor.execute("SELECT name FROM drone_wpn WHERE id = %s", (item_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Record not found.'}), 404

        cursor.execute("DELETE FROM drone_wpn WHERE id = %s", (item_id,))
        conn.commit()

        return jsonify({
            'success': True,
            'message': f'Record "{row.get("name")}" deleted successfully.'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Failed to delete record: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()
