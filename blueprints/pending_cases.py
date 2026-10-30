import datetime
from flask import Blueprint, jsonify, request
from db_config import get_db_connection
from middleware import require_login

pending_cases_bp = Blueprint('pending_cases_bp', __name__, url_prefix='/pending_cases')

ALLOWED_ROLES = [
    'CO', 'COMMANDING OFFICER', 'COMMANDINGOFFICER', '2IC', 'ADJUTANT',
    'ACCOUNT OFFICER', 'ACCOUNTS OFFICER', 'ACCOUNT JCO', 'ACCOUNTS JCO',
    'ACCOUNT CLK', 'ACCOUNTS CLK', 'ADMIN', 'SUPERADMIN',
    'DOCJC', 'DOC JC', 'DOC_JC',
    'ONCO', 'ONCO ACCESS'
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


def get_lve_docjc_published_count(cursor, week_start=None):
    """
    Counts only those LVE cases published by DOCJC during the current week.
    Publications made by other users are excluded.
    """
    if week_start is None:
        now = datetime.datetime.now()
        week_start = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    cursor.execute("""
        SELECT COUNT(*) AS c 
        FROM doc_leave_details 
        WHERE LOWER(TRIM(doc_status)) = 'done'
          AND (
              (published_at >= %s AND (
                  LOWER(TRIM(COALESCE(published_role, ''))) = 'docjc' 
                  OR LOWER(TRIM(COALESCE(published_role, ''))) LIKE '%doc%'
                  OR LOWER(TRIM(COALESCE(published_by, ''))) = 'docjc'
                  OR LOWER(TRIM(COALESCE(published_by, ''))) LIKE '%doc%'
              ))
              OR 
              (published_at IS NULL AND created_at >= %s AND (
                  LOWER(TRIM(COALESCE(created_by, ''))) = 'docjc'
                  OR LOWER(TRIM(COALESCE(created_by, ''))) LIKE '%doc%'
              ))
          )
    """, (week_start, week_start))
    row = cursor.fetchone()
    return (row['c'] if row else 0) or 0


def sync_lve_case_status(cursor, conn):
    """
    Applies authoritative calculation rules strictly for the LVE case:
    1. Total Cases = Pending Cases (Last Week) + Received Cases (Current Week)
    2. Published This Week = only those LVE cases published by DOCJC during current week
    3. Under Progress = Total Cases - Published This Week
    """
    try:
        cursor.execute("""
            SELECT id, pending_last_week, recd_current_week, pub_this_week, total_cases, under_prog 
            FROM pending_cases 
            WHERE type_of_case = 'Lve' 
            LIMIT 1
        """)
        lve = cursor.fetchone()
        if not lve:
            return None

        pub_this_week = get_lve_docjc_published_count(cursor)
        pend = int(lve.get('pending_last_week') or 0)
        recd = int(lve.get('recd_current_week') or 0)
        total_cases = pend + recd
        under_prog = max(0, total_cases - pub_this_week)

        if (lve.get('pub_this_week') != pub_this_week or
            lve.get('total_cases') != total_cases or
            lve.get('under_prog') != under_prog):
            cursor.execute("""
                UPDATE pending_cases
                SET pub_this_week = %s,
                    total_cases = %s,
                    under_prog = %s,
                    updated_at = NOW()
                WHERE type_of_case = 'Lve'
            """, (pub_this_week, total_cases, under_prog))
            conn.commit()

        return {
            'pending_last_week': pend,
            'recd_current_week': recd,
            'total_cases': total_cases,
            'pub_this_week': pub_this_week,
            'under_prog': under_prog
        }
    except Exception as e:
        print("[sync_lve_case_status Warning]:", e)
        return None


def check_weekly_rollover(cursor, conn):
    """
    Automatic weekly rollover every Monday at 12:00 AM (00:00).
    Applies to ALL type of cases:
    1. Carries forward previous week's Under Progress into Pending Cases (Last Week).
    2. Resets Received Cases (Current Week) to 0.
    3. Resets Published This Week to 0.
    4. Sets Total Cases = New Pending Cases + 0 = under_prog.
    5. Sets Under Progress = Total Cases - 0 = under_prog.
    6. Archives historical weekly snapshot of all cases to `pending_cases_weekly_history`.
    7. Resets company received counts in `pending_cases_company_recd` to 0.
    8. Persistently records current rollover week in `system_settings` to prevent duplicates.
    """
    try:
        now = datetime.datetime.now()
        iso = now.isocalendar()
        current_week_str = f"{iso[0]}-W{iso[1]:02d}"

        cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'last_part2_rollover_week'")
        row = cursor.fetchone()
        last_week_str = row['setting_value'] if row else None

        if not last_week_str or last_week_str == '0':
            cursor.execute("""
                INSERT INTO system_settings (setting_key, setting_value)
                VALUES ('last_part2_rollover_week', %s)
                ON DUPLICATE KEY UPDATE setting_value = %s
            """, (current_week_str, current_week_str))
            conn.commit()
            return

        if last_week_str != current_week_str:
            # Calculate dates for previous week snapshot
            monday_this_week = (now - datetime.timedelta(days=now.weekday())).date()
            sunday_last_week = monday_this_week - datetime.timedelta(days=1)
            monday_last_week = monday_this_week - datetime.timedelta(days=7)

            # Ensure history table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `pending_cases_weekly_history` (
                  `id` int NOT NULL AUTO_INCREMENT,
                  `case_id` int DEFAULT NULL,
                  `type_of_case` varchar(100) NOT NULL,
                  `week_identifier` varchar(30) NOT NULL,
                  `week_start_date` date NOT NULL,
                  `week_end_date` date NOT NULL,
                  `pending_last_week` int DEFAULT '0',
                  `recd_current_week` int DEFAULT '0',
                  `total_cases` int DEFAULT '0',
                  `pub_this_week` int DEFAULT '0',
                  `under_prog` int DEFAULT '0',
                  `remarks` text,
                  `rollover_at` datetime DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  UNIQUE KEY `uk_case_week` (`type_of_case`,`week_identifier`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 1. Archive current values of ALL cases to historical table before rollover
            cursor.execute("""
                INSERT IGNORE INTO pending_cases_weekly_history
                (case_id, type_of_case, week_identifier, week_start_date, week_end_date,
                 pending_last_week, recd_current_week, total_cases, pub_this_week, under_prog, remarks, rollover_at)
                SELECT id, type_of_case, %s, %s, %s,
                       pending_last_week, recd_current_week, total_cases, pub_this_week, under_prog, remarks, NOW()
                FROM pending_cases
            """, (last_week_str, monday_last_week, sunday_last_week))

            # 2. Apply Weekly Rollover to ALL type of cases:
            # - Carry forward previous week's Under Progress count into Pending Cases (Last Week)
            # - Reset Received Cases (Current Week) to 0
            # - Reset Published This Week to 0
            # - Total Cases = New Pending Cases + 0 = under_prog
            # - Under Progress = Total Cases - 0 = under_prog
            cursor.execute("""
                UPDATE pending_cases
                SET pending_last_week = under_prog,
                    recd_current_week = 0,
                    pub_this_week = 0,
                    total_cases = under_prog,
                    updated_at = NOW(),
                    updated_by = 'SYSTEM ROLLOVER'
            """)

            # 4. On Monday rollover, delete all completed (DONE) leaves from doc_leave_details table
            cursor.execute("""
                DELETE FROM doc_leave_details
                WHERE LOWER(TRIM(doc_status)) = 'done'
            """)

            # 4b. Ensure remaining uncompleted pending leaves carry forward into the new week as active
            cursor.execute("""
                UPDATE doc_leave_details
                SET onco_status = 'active',
                    doc_status = ''
                WHERE LOWER(TRIM(doc_status)) != 'done'
            """)

            # 4b. Reset company recd counts to 0 for the new week
            cursor.execute("UPDATE pending_cases_company_recd SET recd_count = 0;")

            # 5. Persistently record current week to prevent duplicate runs
            cursor.execute("""
                UPDATE system_settings 
                SET setting_value = %s, updated_at = NOW() 
                WHERE setting_key = 'last_part2_rollover_week'
            """, (current_week_str,))

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
        sync_lve_case_status(cursor, conn)

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

        user_role = (user.get('role') or '').upper().strip()
        r_clean = user_role.replace(' ', '').replace('_', '').replace('-', '')
        is_onco = ('ONCO' in user_role or 'ONCO' in r_clean)
        user_comp = (user.get('company') or '').strip()

        # Fetch company-wise recd counts
        cursor.execute("SELECT case_id, company, recd_count FROM pending_cases_company_recd")
        all_comp_recd = cursor.fetchall()
        comp_recd_by_case = {}
        for cr in all_comp_recd:
            cid = cr['case_id']
            if cid not in comp_recd_by_case:
                comp_recd_by_case[cid] = {}
            comp_recd_by_case[cid][cr['company']] = cr['recd_count']

        # Also fetch company-wise active leave counts for LVE
        cursor.execute("""
            SELECT company, COUNT(*) AS active_count
            FROM doc_leave_details
            WHERE LOWER(TRIM(COALESCE(onco_status, ''))) = 'active'
            GROUP BY company
        """)
        lve_comp_rows = cursor.fetchall()
        lve_by_comp = {str(r['company']).strip().lower(): r['active_count'] for r in lve_comp_rows if r.get('company')}

        user_comp_norm = (user_comp or '').strip().lower()
        for row in rows:
            rems = remarks_by_case.get(row['id'], [])
            row['remarks_list'] = rems
            row['remarks_count'] = len(rems)

            is_lve = (row.get('type_of_case') or '').strip().lower() == 'lve'
            if is_lve:
                row['company_recd_map'] = lve_by_comp
                row['my_company_recd'] = lve_by_comp.get(user_comp_norm, 0) if is_onco else row['recd_current_week']
            else:
                c_dict = comp_recd_by_case.get(row['id'], {})
                row['company_recd_map'] = c_dict
                row['my_company_recd'] = c_dict.get(user_comp, 0)

        return jsonify({
            'success': True,
            'data': rows,
            'is_onco': is_onco,
            'user_company': user_comp,
            'current_role': user_role
        })
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


@pending_cases_bp.route('/onco_update/<int:row_id>', methods=['POST'])
def onco_update_pending_case(row_id):
    user = require_login()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    role = (user.get('role') or '').upper().strip()
    r_clean = role.replace(' ', '').replace('_', '').replace('-', '')
    is_onco = ('ONCO' in role or 'ONCO' in r_clean)
    if not is_onco:
        return jsonify({'success': False, 'message': 'Only ONCO role can perform company case update'}), 403

    user_company = (user.get('company') or '').strip()
    if not user_company:
        return jsonify({'success': False, 'message': 'User has no assigned company'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_default_cases(cursor, conn)

        # "in action they can edit all Tpe of cases except LVE"
        cursor.execute("SELECT id, type_of_case, pending_last_week, pub_this_week FROM pending_cases WHERE id = %s", (row_id,))
        case_row = cursor.fetchone()
        if not case_row:
            return jsonify({'success': False, 'message': 'Case not found'}), 404

        case_type = (case_row.get('type_of_case') or '').strip().lower()
        if case_type == 'lve':
            return jsonify({'success': False, 'message': 'LVE case cannot be edited manually by ONCO. It is managed via Leave Details.'}), 400

        data = request.get_json() or {}
        mode = str(data.get('mode') or 'add').strip().lower()
        input_val = int(data.get('recd_count') or 0)
        remark_text = str(data.get('remarks') or '').strip()
        user_name = user.get('name') or user.get('username') or f"ONCO ({user_company})"

        # Fetch current count for this company to support cumulative addition (update by 5, then update 10 -> total 15)
        cursor.execute("SELECT recd_count FROM pending_cases_company_recd WHERE case_id = %s AND company = %s", (row_id, user_company))
        cur_row = cursor.fetchone()
        cur_recd = int(cur_row['recd_count'] or 0) if cur_row else 0

        if mode == 'set':
            new_company_recd = max(0, input_val)
        else:
            new_company_recd = max(0, cur_recd + input_val)

        # 1. Upsert company recd count for this case
        cursor.execute("""
            INSERT INTO pending_cases_company_recd (case_id, company, recd_count, updated_by, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE recd_count = VALUES(recd_count), updated_by = VALUES(updated_by), updated_at = NOW()
        """, (row_id, user_company, new_company_recd, user_name))

        # 2. Sum up values RECD THIS WEEK provided by all ONCOs
        cursor.execute("SELECT COALESCE(SUM(recd_count), 0) AS total_recd FROM pending_cases_company_recd WHERE case_id = %s", (row_id,))
        sum_recd = int(cursor.fetchone()['total_recd'] or 0)

        # 3. Calculate:
        # Total Cases = Pending Cases (Last Week) + Recd Cases (Current Week)
        # Under Prog = Total Cases - Published This Week
        p_val = int(case_row.get('pending_last_week') or 0)
        pub_val = int(case_row.get('pub_this_week') or 0)
        tot_val = p_val + sum_recd
        under_val = max(0, tot_val - pub_val)

        # 4. Update pending_cases row
        cursor.execute("""
            UPDATE pending_cases
            SET recd_current_week = %s,
                total_cases = %s,
                under_prog = %s,
                remarks = COALESCE(NULLIF(%s, ''), remarks),
                updated_by = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (sum_recd, tot_val, under_val, remark_text, user_name, row_id))

        # 5. Insert remark if provided
        if remark_text:
            cursor.execute("""
                INSERT INTO pending_case_remarks (case_id, remark, remarked_by, remarked_by_role, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (row_id, remark_text, user_name, f"ONCO ({user_company})"))

        conn.commit()

        cursor.execute("""
            SELECT id, type_of_case, pending_last_week, recd_current_week, total_cases,
                   pub_this_week, under_prog, remarks, updated_by,
                   DATE_FORMAT(updated_at, '%d %b %Y %h:%i %p') AS updated_at,
                   UNIX_TIMESTAMP(updated_at) AS updated_at_ts
            FROM pending_cases WHERE id = %s
        """, (row_id,))
        updated_row = cursor.fetchone()
        updated_row['my_company_recd'] = new_company_recd

        cursor.execute("SELECT company, recd_count FROM pending_cases_company_recd WHERE case_id = %s", (row_id,))
        comp_rows = cursor.fetchall()
        updated_row['company_recd_map'] = {r['company']: r['recd_count'] for r in comp_rows}

        cursor.execute("""
            SELECT id, case_id, remark, remarked_by,
                   COALESCE(remarked_by_role, remarked_by) AS remarked_by_role,
                   DATE_FORMAT(created_at, '%d %b %Y %h:%i %p') AS created_at
            FROM pending_case_remarks
            WHERE case_id = %s
            ORDER BY id DESC
        """, (row_id,))
        row_remarks = cursor.fetchall()
        updated_row['remarks_list'] = row_remarks
        updated_row['remarks_count'] = len(row_remarks)

        return jsonify({
            'success': True,
            'row': updated_row,
            'my_company_recd': new_company_recd,
            'remarks_list': row_remarks,
            'remarks_count': len(row_remarks)
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
