import datetime
from flask import Blueprint, jsonify, request
from db_config import get_db_connection
from middleware import require_login

pending_cases_bp = Blueprint('pending_cases_bp', __name__, url_prefix='/pending_cases')

ALLOWED_ROLES = [
    'CO', 'COMMANDING OFFICER', 'COMMANDINGOFFICER', '2IC', 'ADJUTANT',
    'ACCOUNT OFFICER', 'ACCOUNTS OFFICER', 'ACCOUNT JCO', 'ACCOUNTS JCO',
    'ACCOUNT CLK', 'ACCOUNTS CLK', 'ADMIN', 'SUPERADMIN',
    'DOCJC', 'DOC JC', 'DOC_JC'
]

import datetime

DEFAULT_CASE_TYPES = [
    (1, 'Posting IN'),
    (2, 'Posting OUT'),
    (3, 'Pension Out'),
    (4, 'TPTL'),
    (5, 'Lve'),
    (6, 'TFRGTH'),
    (7, 'HRA'),
    (8, 'RUMCIG'),
    (9, 'PRPLVE/JRNYD'),
    (10, 'Medal'),
    (11, 'Med Cat'),
    (12, 'CEA'),
    (13, 'Marriage/Divorce'),
    (14, 'Change of Name'),
    (15, 'Birth'),
    (16, 'Demise'),
    (17, 'Civ Edn/MILEDN'),
    (18, 'ACCLVE'),
    (19, 'UID/PAN'),
    (20, 'Jt Acct'),
    (21, 'OPTFIX'),
    (22, 'PFWDL'),
    (23, 'Mobile No/Email'),
    (24, 'Change Address'),
    (25, 'Injury Report'),
    (26, 'Hosp Adm/Tfr/Disch'),
    (27, 'PROVFS'),
    (28, 'LTC'),
    (29, 'RISK'),
    (30, 'HAUCA')
]

def ensure_default_cases(cursor, conn):
    """
    Guarantees all 30 standard case types exist in pending_cases.
    If the table is truncated or has no data, re-populates all 30 rows with default 0s.
    If any individual case types are missing, inserts them with default 0s.
    """
    try:
        cursor.execute("SELECT COUNT(*) AS cnt FROM pending_cases")
        row = cursor.fetchone()
        cnt = (row['cnt'] if row else 0) or 0
        if cnt == 0:
            cursor.executemany("""
                INSERT INTO pending_cases (id, type_of_case, pending_last_week, recd_current_week, pub_this_week, total_cases, under_prog, sort_order, updated_at)
                VALUES (%s, %s, 0, 0, 0, 0, 0, %s, NOW())
            """, [(cid, cname, cid) for cid, cname in DEFAULT_CASE_TYPES])
            conn.commit()
        else:
            cursor.execute("SELECT id, LOWER(TRIM(type_of_case)) as norm_name FROM pending_cases")
            existing_rows = cursor.fetchall()
            existing_names = {r['norm_name'] for r in existing_rows if r.get('norm_name')}
            existing_ids = {r['id'] for r in existing_rows if r.get('id')}

            added = False
            for cid, cname in DEFAULT_CASE_TYPES:
                if cname.strip().lower() not in existing_names:
                    if cid not in existing_ids:
                        cursor.execute("""
                            INSERT INTO pending_cases (id, type_of_case, pending_last_week, recd_current_week, pub_this_week, total_cases, under_prog, sort_order, updated_at)
                            VALUES (%s, %s, 0, 0, 0, 0, 0, %s, NOW())
                        """, (cid, cname, cid))
                    else:
                        cursor.execute("""
                            INSERT INTO pending_cases (type_of_case, pending_last_week, recd_current_week, pub_this_week, total_cases, under_prog, sort_order, updated_at)
                            VALUES (%s, 0, 0, 0, 0, 0, %s, NOW())
                        """, (cname, cid))
                    added = True
            # Sync sort_order to ensure Lve is always at sno. 5th
            for s_idx, (cid, cname) in enumerate(DEFAULT_CASE_TYPES, start=1):
                cursor.execute(
                    "UPDATE pending_cases SET sort_order = %s WHERE LOWER(TRIM(type_of_case)) = %s",
                    (s_idx, cname.strip().lower())
                )
            conn.commit()
    except Exception as e:
        print("ensure_default_cases error:", e)


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
            # Monday 12:00 AM rollover:
            # Under PROG count gets added to Pending Last Week
            # Under PROG resets to 0
            # recd_current_week = 0, pub_this_week = 0
            # total_cases = new pending_last_week (since recd = 0)
            # under_prog = total_cases - pub = new_pending - 0 = new_pending
            # Monday 12:00 AM rollover:
            # reset Under PROG to 0 and if it contains any count add that count to pending Last week
            cursor.execute("""
                UPDATE pending_cases
                SET total_cases = pending_last_week + under_prog,
                    pending_last_week = pending_last_week + under_prog,
                    under_prog = 0,
                    recd_current_week = 0,
                    pub_this_week = 0,
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
        ensure_default_cases(cursor, conn)
        check_weekly_rollover(cursor, conn)

        # 5th Position for TOTAL CASES next to Current Week:
        # 1: id/sort, 2: type_of_case, 3: pending_last_week, 4: recd_current_week, 5: total_cases, 6: pub_this_week, 7: under_prog
        cursor.execute("""
            SELECT id, type_of_case, pending_last_week, recd_current_week,
                   (pending_last_week + recd_current_week) AS total_cases,
                   pub_this_week,
                   under_prog,
                   remarks, updated_by,
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
        ensure_default_cases(cursor, conn)
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
            # DOCJC can edit: recd_current_week, pub_this_week
            # total_cases = pending_last_week + recd_current_week  (auto)
            # under_prog  = total_cases - pub_this_week            (auto)
            if remark_text:
                cursor.execute("""
                    INSERT INTO pending_case_remarks (case_id, remark, remarked_by, remarked_by_role, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (row_id, remark_text, user_name, user_role_label))

            cursor.execute("SELECT pending_last_week FROM pending_cases WHERE id = %s", (row_id,))
            ex = cursor.fetchone()
            p_val = ex['pending_last_week'] if ex else 0
            r_val = int(data.get('recd_current_week') or 0)
            pub_val = int(data.get('pub_this_week') or 0)
            tot_val = p_val + r_val
            under_val = max(0, tot_val - pub_val)

            cursor.execute("""
                UPDATE pending_cases
                SET recd_current_week = %s,
                    pub_this_week = %s,
                    total_cases = %s,
                    under_prog = %s,
                    remarks = COALESCE(NULLIF(%s, ''), remarks),
                    updated_by = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                r_val,
                pub_val,
                tot_val,
                under_val,
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
            tot_val = p_val + r_val
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
                   (pending_last_week + recd_current_week) AS total_cases,
                   pub_this_week,
                   under_prog,
                   remarks, updated_by,
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
        ensure_default_cases(cursor, conn)
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
