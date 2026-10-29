from imports import *

pending_cases_bp = Blueprint('pending_cases_bp', __name__, url_prefix='/pending_cases')

ALLOWED_ROLES = [
    'CO', 'COMMANDING OFFICER', 'COMMANDINGOFFICER', '2IC', 'ADJUTANT',
    'ACCOUNT OFFICER', 'ACCOUNTS OFFICER', 'ACCOUNT JCO', 'ACCOUNTS JCO',
    'ACCOUNT CLK', 'ACCOUNTS CLK', 'ADMIN', 'SUPERADMIN',
    'DOCJC', 'DOC JC', 'DOC_JC'
]

import datetime

def check_weekly_rollover(cursor, conn):
    try:
        now = datetime.datetime.now()
        iso = now.isocalendar()
        current_week_str = f"{iso[0]}-W{iso[1]:02d}"

        cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'last_part2_rollover_week'")
        row = cursor.fetchone()
        last_week_str = row['setting_value'] if row else None

        if not last_week_str or last_week_str == '0':
            cursor.execute("INSERT INTO system_settings (setting_key, setting_value) VALUES ('last_part2_rollover_week', %s) ON DUPLICATE KEY UPDATE setting_value = %s", (current_week_str, current_week_str))
            conn.commit()
            return

        if last_week_str != current_week_str:
            # Sunday 11:59 PM passed, Monday 12:00 AM arrived:
            # "once it is 12:00 AM MONDAY make 0 Under PROG add them to PEnding Last Week"
            cursor.execute("""
                UPDATE pending_cases
                SET pending_last_week = pending_last_week + under_prog,
                    under_prog = 0,
                    recd_current_week = 0,
                    pub_this_week = 0,
                    total_cases = pending_last_week + under_prog,
                    updated_at = NOW(),
                    updated_by = 'SYSTEM ROLLOVER'
            """)
            cursor.execute("""
                UPDATE doc_leave_details
                SET onco_status = 'active',
                    doc_status = ''
                WHERE doc_status = 'balance'
            """)
            cursor.execute("UPDATE system_settings SET setting_value = %s WHERE setting_key = 'last_part2_rollover_week'", (current_week_str,))
            conn.commit()
    except Exception as e:
        print("Weekly rollover check error:", e)

@pending_cases_bp.route('/get', methods=['GET'])
def get_pending_cases():
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        check_weekly_rollover(cursor, conn)

        # 5th Position for TOTAL CASES next to Current Week:
        # 1: id/sort, 2: type_of_case, 3: pending_last_week, 4: recd_current_week, 5: total_cases, 6: pub_this_week, 7: under_prog
        cursor.execute("""
            SELECT id, type_of_case, pending_last_week, recd_current_week,
                   GREATEST(0, (pending_last_week + recd_current_week) - pub_this_week) AS total_cases,
                   pub_this_week,
                   under_prog, remarks, updated_by,
                   DATE_FORMAT(updated_at, '%d %b %Y %h:%i %p') AS updated_at,
                   UNIX_TIMESTAMP(updated_at) AS updated_at_ts
            FROM pending_cases
            ORDER BY sort_order ASC
        """)
        rows = cursor.fetchall()

        cursor.execute("""
            SELECT id, case_id, remark, remarked_by,
                   COALESCE(remarked_by_role, remarked_by) AS remarked_by_role,
                   DATE_FORMAT(created_at, '%d %b %Y %h:%i %p') AS created_at
            FROM pending_case_remarks
            ORDER BY id DESC
        """)
        all_remarks = cursor.fetchall()

        remarks_by_case = {}
        for rem in all_remarks:
            cid = rem['case_id']
            if cid not in remarks_by_case:
                remarks_by_case[cid] = []
            remarks_by_case[cid].append(rem)

        for row in rows:
            rems = remarks_by_case.get(row['id'], [])
            row['remarks_list'] = rems
            row['remarks_count'] = len(rems)

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

    # for CO,2IC,ADJUTANT roles show PART-II STATUS can only update Remarks rest keep locked
    is_remark_only_role = role in ['CO', 'COMMANDING OFFICER', 'COMMANDINGOFFICER', '2IC', 'ADJUTANT'] or \
                          r_clean in ['CO', 'COMMANDINGOFFICER', '2IC', 'ADJUTANT']

    # "lock columns for DOCJC Pending Cas of Last Week, Recd Cas Current Week, Total Cases"
    is_docjc_role = ('DOC' in role or 'DOC' in r_clean) and r_clean not in ['ADMIN', 'SUPERADMIN']

    try:
        remark_text = str(data.get('remarks') or '').strip()
        user_role_label = user.get('role') or 'Authority'
        user_name = user.get('name') or user.get('username') or user_role_label

        if is_remark_only_role:
            if remark_text:
                cursor.execute("""
                    INSERT INTO pending_case_remarks (case_id, remark, remarked_by, remarked_by_role, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (row_id, remark_text, user_name, user_role_label))

                cursor.execute("""
                    UPDATE pending_cases
                    SET remarks = %s,
                        updated_by = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (remark_text, user_name, row_id))
        elif is_docjc_role:
            # For DOCJC: pending_last_week, recd_current_week, and total_cases are locked / auto-calculated
            if remark_text:
                cursor.execute("""
                    INSERT INTO pending_case_remarks (case_id, remark, remarked_by, remarked_by_role, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (row_id, remark_text, user_name, user_role_label))

            cursor.execute("SELECT pending_last_week, recd_current_week FROM pending_cases WHERE id = %s", (row_id,))
            ex = cursor.fetchone()
            p_val = ex['pending_last_week'] if ex else 0
            r_val = ex['recd_current_week'] if ex else 0
            pub_val = int(data.get('pub_this_week') or 0)
            tot_val = max(0, (p_val + r_val) - pub_val)
            under_val = int(data.get('under_prog') or 0)

            cursor.execute("""
                UPDATE pending_cases
                SET pub_this_week = %s,
                    under_prog = %s,
                    total_cases = %s,
                    remarks = COALESCE(NULLIF(%s, ''), remarks),
                    updated_by = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                pub_val,
                under_val,
                tot_val,
                remark_text,
                user_name,
                row_id
            ))
        else:
            if remark_text:
                cursor.execute("""
                    INSERT INTO pending_case_remarks (case_id, remark, remarked_by, remarked_by_role, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (row_id, remark_text, user_name, user_role_label))

            p_val = int(data.get('pending_last_week') or 0)
            r_val = int(data.get('recd_current_week') or 0)
            pub_val = int(data.get('pub_this_week') or 0)
            tot_val = max(0, (p_val + r_val) - pub_val)
            under_val = int(data.get('under_prog') or 0)

            cursor.execute("""
                UPDATE pending_cases
                SET pending_last_week = %s,
                    recd_current_week = %s,
                    total_cases = %s,
                    pub_this_week = %s,
                    under_prog = %s,
                    remarks = COALESCE(NULLIF(%s, ''), remarks),
                    updated_by = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                p_val,
                r_val,
                tot_val,
                pub_val,
                under_val,
                remark_text,
                user_name,
                row_id
            ))
        conn.commit()

        cursor.execute("""
            SELECT id, type_of_case, pending_last_week, recd_current_week,
                   GREATEST(0, (pending_last_week + recd_current_week) - pub_this_week) AS total_cases,
                   pub_this_week,
                   under_prog, remarks, updated_by,
                   DATE_FORMAT(updated_at, '%d %b %Y %h:%i %p') AS updated_at,
                   UNIX_TIMESTAMP(updated_at) AS updated_at_ts
            FROM pending_cases WHERE id = %s
        """, (row_id,))

        updated_info = cursor.fetchone()

        cursor.execute("""
            SELECT id, case_id, remark, remarked_by,
                   COALESCE(remarked_by_role, remarked_by) AS remarked_by_role,
                   DATE_FORMAT(created_at, '%d %b %Y %h:%i %p') AS created_at
            FROM pending_case_remarks
            WHERE case_id = %s
            ORDER BY id DESC
        """, (row_id,))
        row_remarks = cursor.fetchall()

        if updated_info:
            updated_info['remarks_list'] = row_remarks
            updated_info['remarks_count'] = len(row_remarks)

        return jsonify({
            'success': True,
            'row': updated_info,
            'remarks_list': row_remarks,
            'remarks_count': len(row_remarks),
            'updated_at': updated_info['updated_at'] if updated_info else None,
            'updated_at_ts': updated_info['updated_at_ts'] if updated_info else None
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@pending_cases_bp.route('/add_remark/<int:row_id>', methods=['POST'])
def add_pending_case_remark(row_id):
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
    remark_text = str(data.get('remark') or '').strip()
    if not remark_text:
        return jsonify({'success': False, 'message': 'Remark cannot be empty'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        user_role_label = user.get('role') or 'Authority'
        user_name = user.get('name') or user.get('username') or user_role_label

        cursor.execute("""
            INSERT INTO pending_case_remarks (case_id, remark, remarked_by, remarked_by_role, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (row_id, remark_text, user_name, user_role_label))

        cursor.execute("""
            UPDATE pending_cases
            SET remarks = %s,
                updated_by = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (remark_text, user_name, row_id))
        conn.commit()

        cursor.execute("""
            SELECT id, case_id, remark, remarked_by,
                   COALESCE(remarked_by_role, remarked_by) AS remarked_by_role,
                   DATE_FORMAT(created_at, '%d %b %Y %h:%i %p') AS created_at
            FROM pending_case_remarks
            WHERE case_id = %s
            ORDER BY id DESC
        """, (row_id,))
        row_remarks = cursor.fetchall()

        cursor.execute("""
            SELECT DATE_FORMAT(updated_at, '%d %b %Y %h:%i %p') AS updated_at,
                   UNIX_TIMESTAMP(updated_at) AS updated_at_ts
            FROM pending_cases WHERE id = %s
        """, (row_id,))
        ts_info = cursor.fetchone()

        return jsonify({
            'success': True,
            'remarks_list': row_remarks,
            'remarks_count': len(row_remarks),
            'latest_remark': remark_text,
            'updated_at': ts_info['updated_at'] if ts_info else None,
            'updated_at_ts': ts_info['updated_at_ts'] if ts_info else None
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
