from flask import Blueprint, jsonify, request
from db_config import get_db_connection
from middleware import require_login
from datetime import date
import traceback

drone_wpn_bp = Blueprint('drone_wpn_bp', __name__, url_prefix='/drone_wpn')


def ensure_drone_wpn_table(conn=None):
    """
    Ensures the drone_wpn and drone_wpn_assignment tables exist with Option 1 architecture:
    - drone_wpn: id, name, auth_individuals, created_by, created_at, updated_at
    - drone_wpn_assignment: id, drone_wpn_id, army_number, assigned_on, assigned_by, created_at
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    if not conn:
        return False

    c = conn.cursor(buffered=True)
    try:
        # 1. Main equipment table
        c.execute("""
            CREATE TABLE IF NOT EXISTS `drone_wpn` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `name` VARCHAR(255) NOT NULL,
                `auth_individuals` VARCHAR(255) DEFAULT '0',
                `created_by` VARCHAR(100) DEFAULT NULL,
                `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                UNIQUE KEY `idx_drone_wpn_unique_name` (`name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)

        # 2. Assignment table for 1-to-Many relationships (1 equipment -> multiple army personnel)
        c.execute("""
            CREATE TABLE IF NOT EXISTS `drone_wpn_assignment` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `drone_wpn_id` INT NOT NULL,
                `army_number` VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
                `assigned_on` DATE DEFAULT NULL,
                `assigned_by` VARCHAR(100) DEFAULT NULL,
                `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                INDEX `idx_dwa_drone_id` (`drone_wpn_id`),
                INDEX `idx_dwa_army_no` (`army_number`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """)

        # Check and migrate any legacy assignments from drone_wpn.army_number if column exists
        c.execute("SHOW COLUMNS FROM `drone_wpn` LIKE 'army_number'")
        if c.fetchone():
            try:
                c.execute("""
                    INSERT INTO `drone_wpn_assignment` (drone_wpn_id, army_number, assigned_on, assigned_by)
                    SELECT d.id, d.army_number, COALESCE(d.assigned_on, CURDATE()), d.created_by
                    FROM `drone_wpn` d
                    WHERE d.army_number IS NOT NULL AND TRIM(d.army_number) != ''
                    AND NOT EXISTS (
                        SELECT 1 FROM `drone_wpn_assignment` a 
                        WHERE a.drone_wpn_id = d.id AND a.army_number = d.army_number
                    )
                """)
                conn.commit()
            except Exception as mig_err:
                print(f"[drone_wpn] Legacy data migration note: {mig_err}")

        # Drop old fields from drone_wpn if present
        cols_to_remove = ['held', 'present_in_unit', 'on_leave', 'company', 'updated_by']
        for col in cols_to_remove:
            c.execute(f"SHOW COLUMNS FROM `drone_wpn` LIKE '{col}'")
            if c.fetchone():
                try:
                    c.execute(f"ALTER TABLE `drone_wpn` DROP COLUMN `{col}`")
                except Exception as col_err:
                    print(f"[drone_wpn] Could not drop column {col}: {col_err}")

        # Ensure collations match personnel table (utf8mb4_0900_ai_ci)
        try:
            c.execute("ALTER TABLE `drone_wpn` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
            c.execute("ALTER TABLE `drone_wpn_assignment` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
        except Exception:
            pass

        conn.commit()
        return True
    except Exception as e:
        print(f"[drone_wpn] Error ensuring tables: {e}")
        traceback.print_exc()
        return False
    finally:
        try:
            c.close()
        except Exception:
            pass
        if should_close:
            try:
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


@drone_wpn_bp.route('/api/personnel/search', methods=['GET'])
def search_personnel_for_assign():
    """
    Search personnel by name, army number, or rank for assigning to equipment.
    Returns list of matching personnel.
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'success': True, 'data': []})

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        user_company = (user.get('company') or '').strip()
        user_role = (user.get('role') or '').upper().strip()
        search_pattern = f"%{q}%"

        # Check if user has global leadership view (e.g. Admin, Superadmin, CO, 2IC)
        is_global_view = user_role in ['ADMIN', 'SUPERADMIN', 'CO', '2IC'] and (not user_company or user_company.lower() in ['admin', 'center', 'all'])

        # Strictly restrict ONCO / company users to their own matching company
        if user_company and not is_global_view:
            coy_clean = user_company.lower().replace('company', '').replace('coy', '').strip()
            cursor.execute("""
                SELECT army_number, name, `rank`, company, COALESCE(onleave_status, 0) AS onleave_status
                FROM personnel
                WHERE (army_number LIKE %s OR name LIKE %s OR `rank` LIKE %s)
                  AND (
                      LOWER(TRIM(company)) = LOWER(TRIM(%s))
                      OR LOWER(TRIM(company)) LIKE %s
                  )
                ORDER BY name ASC
                LIMIT 25
            """, (search_pattern, search_pattern, search_pattern, user_company, f"%{coy_clean}%"))
        else:
            cursor.execute("""
                SELECT army_number, name, `rank`, company, COALESCE(onleave_status, 0) AS onleave_status
                FROM personnel
                WHERE army_number LIKE %s OR name LIKE %s OR `rank` LIKE %s
                ORDER BY name ASC
                LIMIT 25
            """, (search_pattern, search_pattern, search_pattern))

        rows = cursor.fetchall() or []
        return jsonify({'success': True, 'data': rows})
    except Exception as e:
        print(f"[drone_wpn] Search personnel error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Search failed: {str(e)}'}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


@drone_wpn_bp.route('/api/list', methods=['GET'])
def get_drone_wpn_list():
    """
    Returns list of all drone_wpn items with their multiple assigned personnel.
    Also returns distinct equipment names for the Add dropdown.
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    company_filter = request.args.get('company', '').strip()

    try:
        ensure_drone_wpn_table(conn)

        cursor = conn.cursor(dictionary=True, buffered=True)

        # 1. Fetch distinct companies for dropdown (with case-insensitive normalization)
        cursor.execute("SELECT DISTINCT company FROM personnel WHERE company IS NOT NULL AND TRIM(company) != '' ORDER BY company ASC")
        c_rows = cursor.fetchall() or []
        
        company_map = {}
        for r in c_rows:
            raw_c = (r.get('company') or '').strip()
            if raw_c:
                key = raw_c.lower()
                if key not in company_map:
                    if key == 'hq company':
                        company_map[key] = 'HQ Company'
                    elif key == 'comn company':
                        company_map[key] = 'COMN Company'
                    else:
                        company_map[key] = raw_c.title() if raw_c.islower() else raw_c

        # Ensure standard unit companies exist
        standard_defaults = ['COMN Company', '3 Company', 'HQ Company']
        for sdc in standard_defaults:
            if sdc.lower() not in company_map:
                company_map[sdc.lower()] = sdc

        distinct_companies = sorted(list(company_map.values()))

        # 2. Fetch all equipment items
        cursor.execute("""
            SELECT 
                d.id, 
                d.name, 
                COALESCE(d.auth_individuals, '0') AS auth_individuals,
                d.created_by,
                DATE_FORMAT(d.updated_at, '%d %b %Y %H:%i') AS formatted_updated_at
            FROM drone_wpn d
            ORDER BY d.name ASC, d.id ASC
        """)
        equipments = cursor.fetchall() or []

        # 3. Fetch all assignments joined with personnel
        cursor.execute("""
            SELECT 
                a.id AS assignment_id,
                a.drone_wpn_id,
                a.army_number,
                DATE_FORMAT(a.assigned_on, '%Y-%m-%d') AS assigned_on,
                DATE_FORMAT(a.assigned_on, '%d %b %Y') AS formatted_assigned_on,
                a.assigned_by,
                p.name AS personnel_name,
                p.`rank` AS personnel_rank,
                p.company AS personnel_company,
                COALESCE(p.onleave_status, 0) AS onleave_status
            FROM drone_wpn_assignment a
            LEFT JOIN personnel p ON a.army_number COLLATE utf8mb4_unicode_ci = p.army_number COLLATE utf8mb4_unicode_ci
            ORDER BY a.assigned_on DESC, a.id DESC
        """)
        assignments = cursor.fetchall() or []

        # Group assignments by drone_wpn_id
        assignments_by_item = {}
        for a in assignments:
            item_id = a['drone_wpn_id']
            if item_id not in assignments_by_item:
                assignments_by_item[item_id] = []
            assignments_by_item[item_id].append(a)

        # Combine equipments with their assignments
        rows = []
        total_assignments = 0
        total_present = 0
        total_leave = 0

        for eq in equipments:
            eq_id = eq['id']
            eq_assignments = assignments_by_item.get(eq_id, [])

            # Apply company filter if selected
            if company_filter and company_filter.upper() != 'ALL':
                eq_assignments = [
                    a for a in eq_assignments 
                    if (a.get('personnel_company') or '').strip().lower() == company_filter.strip().lower()
                ]

            total_assignments += len(eq_assignments)
            for a in eq_assignments:
                if a.get('onleave_status'):
                    total_leave += 1
                else:
                    total_present += 1

            row_data = dict(eq)
            row_data['assignments'] = eq_assignments
            row_data['assigned_count'] = len(eq_assignments)
            row_data['held'] = len(eq_assignments)
            row_data['present_in_unit'] = sum(1 for a in eq_assignments if not a.get('onleave_status'))
            row_data['on_leave'] = sum(1 for a in eq_assignments if a.get('onleave_status'))
            rows.append(row_data)

        # Equipment names for dropdown selection
        equipment_names = [e['name'] for e in equipments]

        # Calculate totals
        def safe_int(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        total_auth = sum(safe_int(r.get('auth_individuals')) for r in rows)

        can_edit = is_onco_authorized(user)

        return jsonify({
            'success': True,
            'data': rows,
            'equipment_names': equipment_names,
            'companies': distinct_companies,
            'selected_company': company_filter or 'ALL',
            'totals': {
                'count': len(rows),
                'assigned': total_assignments,
                'held': total_assignments,
                'present_in_unit': total_present,
                'on_leave': total_leave,
                'auth_individuals': total_auth
            },
            'can_edit': can_edit,
            'user_role': user.get('role'),
            'user_company': user.get('company')
        })
    except Exception as e:
        print(f"[drone_wpn] get_drone_wpn_list error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to fetch drone/wpn records: {str(e)}'}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


@drone_wpn_bp.route('/api/add', methods=['POST'])
def add_drone_wpn_or_assign():
    """
    Adds equipment or assigns personnel to equipment.
    Payload options:
    - name: string (chosen from dropdown or newly typed)
    - auth_individuals: string (optional)
    - army_numbers: array of army numbers (or single army_number)
    - assigned_on: date string (optional)
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    if not is_onco_authorized(user):
        return jsonify({'success': False, 'message': 'Forbidden: Only ONCO can modify Drone/Wpn entries.'}), 403

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    name = (payload.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Equipment name is required.'}), 400

    auth_individuals = str(payload.get('auth_individuals') or payload.get('authIndividuals') or '0').strip()
    assigned_on = (payload.get('assigned_on') or payload.get('assignedOn') or '').strip() or date.today().isoformat()
    user_name = user.get('name') or user.get('username') or user.get('role') or 'ONCO'

    # Extract army numbers (handles array or comma-separated or single)
    raw_army_nos = payload.get('army_numbers') or payload.get('army_number') or []
    if isinstance(raw_army_nos, str):
        army_numbers = [num.strip() for num in raw_army_nos.split(',') if num.strip()]
    elif isinstance(raw_army_nos, list):
        army_numbers = [str(num).strip() for num in raw_army_nos if str(num).strip()]
    else:
        army_numbers = []

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    try:
        ensure_drone_wpn_table(conn)

        cursor = conn.cursor(dictionary=True, buffered=True)

        # 1. Find or create the equipment entry in drone_wpn
        cursor.execute("SELECT id, auth_individuals FROM drone_wpn WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))", (name,))
        existing_eq = cursor.fetchone()

        if existing_eq:
            drone_wpn_id = existing_eq['id']
            # If user provided a custom auth_individuals that differs from '0', update it
            if auth_individuals and auth_individuals != '0' and auth_individuals != existing_eq.get('auth_individuals'):
                cursor.execute("UPDATE drone_wpn SET auth_individuals = %s WHERE id = %s", (auth_individuals, drone_wpn_id))
        else:
            cursor.execute("""
                INSERT INTO drone_wpn (name, auth_individuals, created_by)
                VALUES (%s, %s, %s)
            """, (name, auth_individuals, user_name))
            drone_wpn_id = cursor.lastrowid

        # 2. Insert any assigned personnel into drone_wpn_assignment
        assigned_count = 0
        for army_no in army_numbers:
            # Check if this soldier is already assigned to this equipment
            cursor.execute("""
                SELECT id FROM drone_wpn_assignment 
                WHERE drone_wpn_id = %s AND army_number = %s
            """, (drone_wpn_id, army_no))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO drone_wpn_assignment (drone_wpn_id, army_number, assigned_on, assigned_by)
                    VALUES (%s, %s, %s, %s)
                """, (drone_wpn_id, army_no, assigned_on, user_name))
                assigned_count += 1

        conn.commit()

        msg = f'"{name}" saved successfully.'
        if assigned_count > 0:
            msg += f' Assigned to {assigned_count} personnel.'

        return jsonify({
            'success': True,
            'message': msg,
            'id': drone_wpn_id,
            'assigned_count': assigned_count
        })
    except Exception as e:
        conn.rollback()
        print(f"[drone_wpn] add error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to save record: {str(e)}'}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


@drone_wpn_bp.route('/api/assign', methods=['POST'])
def assign_single_personnel():
    """
    Directly assigns one soldier to an equipment item.
    Payload: { drone_wpn_id, army_number, assigned_on }
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    if not is_onco_authorized(user):
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    drone_wpn_id = payload.get('drone_wpn_id')
    army_number = (payload.get('army_number') or '').strip()
    assigned_on = (payload.get('assigned_on') or '').strip() or date.today().isoformat()
    user_name = user.get('name') or user.get('username') or user.get('role') or 'ONCO'

    if not drone_wpn_id or not army_number:
        return jsonify({'success': False, 'message': 'Equipment and Army Number are required.'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    try:
        ensure_drone_wpn_table(conn)

        cursor = conn.cursor(dictionary=True, buffered=True)

        # Check existing assignment
        cursor.execute("""
            SELECT id FROM drone_wpn_assignment 
            WHERE drone_wpn_id = %s AND army_number = %s
        """, (drone_wpn_id, army_number))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'This personnel is already assigned to this equipment.'}), 400

        cursor.execute("""
            INSERT INTO drone_wpn_assignment (drone_wpn_id, army_number, assigned_on, assigned_by)
            VALUES (%s, %s, %s, %s)
        """, (drone_wpn_id, army_number, assigned_on, user_name))
        conn.commit()

        return jsonify({'success': True, 'message': 'Personnel assigned successfully.'})
    except Exception as e:
        conn.rollback()
        print(f"[drone_wpn] assign error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to assign: {str(e)}'}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


@drone_wpn_bp.route('/api/unassign/<int:assignment_id>', methods=['POST', 'DELETE'])
def unassign_personnel(assignment_id):
    """
    Removes a single soldier assignment from an equipment.
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    if not is_onco_authorized(user):
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    try:
        ensure_drone_wpn_table(conn)

        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("DELETE FROM drone_wpn_assignment WHERE id = %s", (assignment_id,))
        conn.commit()

        return jsonify({'success': True, 'message': 'Personnel unassigned successfully.'})
    except Exception as e:
        conn.rollback()
        print(f"[drone_wpn] unassign error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to unassign: {str(e)}'}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


@drone_wpn_bp.route('/api/update/<int:item_id>', methods=['POST', 'PUT'])
def update_equipment(item_id):
    """
    Updates equipment details (name, auth_individuals).
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    if not is_onco_authorized(user):
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    name = (payload.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Equipment Name is required.'}), 400

    auth_individuals = str(payload.get('auth_individuals') or payload.get('authIndividuals') or '0').strip()

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    try:
        ensure_drone_wpn_table(conn)

        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("""
            UPDATE drone_wpn
            SET name = %s, auth_individuals = %s
            WHERE id = %s
        """, (name, auth_individuals, item_id))
        conn.commit()

        return jsonify({'success': True, 'message': f'"{name}" updated successfully.'})
    except Exception as e:
        conn.rollback()
        print(f"[drone_wpn] update error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to update: {str(e)}'}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


@drone_wpn_bp.route('/api/delete/<int:item_id>', methods=['POST', 'DELETE'])
def delete_equipment(item_id):
    """
    Deletes an equipment and all its associated personnel assignments.
    """
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401

    if not is_onco_authorized(user):
        return jsonify({'success': False, 'message': 'Forbidden.'}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection unavailable.'}), 500

    try:
        ensure_drone_wpn_table(conn)

        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT name FROM drone_wpn WHERE id = %s", (item_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Record not found.'}), 404

        # Delete assignments first
        cursor.execute("DELETE FROM drone_wpn_assignment WHERE drone_wpn_id = %s", (item_id,))
        # Delete equipment
        cursor.execute("DELETE FROM drone_wpn WHERE id = %s", (item_id,))
        conn.commit()

        return jsonify({
            'success': True,
            'message': f'Equipment "{row.get("name")}" and its assignments deleted successfully.'
        })
    except Exception as e:
        conn.rollback()
        print(f"[drone_wpn] delete error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to delete: {str(e)}'}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
