from imports import *


inteview_bp = Blueprint('inteview_bp',__name__,url_prefix='/interview_update')


@inteview_bp.route('/pending_interview_list')
def get_pending_kunba_interviews():
    user = require_login()
    user_company = user['company'].strip()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('select home_state from personnel where army_number = %s',(user['army_number'],))
    result = cursor.fetchone()
    
    if not result:
        cursor.close()
        return jsonify([])

    home_state = result['home_state']



    # STRICT FILTERING TEST - Case-insensitive and trimmed
    cursor.execute("""
      SELECT id, army_number, `rank`, name, home_state, company
      FROM personnel
      WHERE interview_status = 0
        AND LOWER(TRIM(home_state)) = LOWER(TRIM(%s))
        AND LOWER(TRIM(company)) = LOWER(TRIM(%s))
        AND `rank` NOT IN ('Naib Subedar', 'Subedar', 'Sub Maj', 'Subedar Major');
    """,(home_state, user_company))
    data = cursor.fetchall()
    
    cursor.close()
    return jsonify(data)


@inteview_bp.route('/update_interview_status', methods=['POST'])
def complete_kunba_interview():
    data = request.json
    personnel_id = data['id']
    remarks = data.get('remarks', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE personnel
        SET interview_status = 1, interview_remarks = %s
        WHERE id = %s
    """, (remarks, personnel_id))
    conn.commit()
    cursor.close()
    return jsonify({"success": True})




@inteview_bp.route('/completed_interview_list', methods=['GET'])
def completed_interview_list():
    
    user = require_login()
    user_company = user['company'].strip()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Get User's Home State
        cursor.execute('SELECT home_state FROM personnel WHERE army_number = %s', (user['army_number'],))
        result = cursor.fetchone()
        
        if not result:
            return jsonify([])

        home_state = result['home_state']

        # 2. Filter Completed Interviews by State, Company, and Non-JCO Rank
        query = """
            SELECT
                id,
                army_number,
                `rank`,
                name,
                home_state,interview_remarks,
                updated_at AS completed_on
            FROM personnel
            WHERE interview_status = 1
              AND LOWER(TRIM(home_state)) = LOWER(TRIM(%s))
              AND LOWER(TRIM(company)) = LOWER(TRIM(%s))
              AND `rank` NOT IN ('Naib Subedar', 'Subedar', 'Sub Maj', 'Subedar Major')
            ORDER BY updated_at DESC
        """
        cursor.execute(query, (home_state, user_company))
        rows = cursor.fetchall()

        return jsonify(rows)

    except Exception as e:
        return jsonify([])

    finally:
        if cursor:
            cursor.close()
            conn.close()



@inteview_bp.route('/jco-availabilty')
def company_interview_pending():
    user = require_login()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    company = user['company']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        excluded_ranks = ('Naib Subedar', 'Subedar', 'Sub Maj', 'Subedar Major')
        rank_placeholders = ",".join(["%s"] * len(excluded_ranks))

        # 1️⃣ Pending interviews (unchanged)
        cursor.execute(f"""
            SELECT name, army_number, home_state, company, `rank`
            FROM personnel
            WHERE interview_status = 0
              AND `rank` NOT IN ({rank_placeholders})
            ORDER BY home_state, name
        """, (*excluded_ranks,))

        pending_data = cursor.fetchall()

        # 2️⃣ Collect unique home_states (unchanged)
        home_states = list({
            row['home_state']
            for row in pending_data
            if row['home_state']
        })

        jco_map = {}          # key = (home_state, company)
        assigned_jco_map = {} # assigned (Pending) JCOs (unchanged)

        if home_states:
            placeholders = ",".join(["%s"] * len(home_states))

            # 3️⃣ Live eligible JCOs — now fetching company too
            cursor.execute(f"""
                SELECT name, home_state, `rank`, company
                FROM personnel
                WHERE home_state IN ({placeholders})
                  AND `rank` IN ('Naib Subedar', 'Subedar', 'Sub Maj', 'Subedar Major')
                  AND onleave_status = 0
                  AND detachment_status = 0
                  AND posting_status = 0
                ORDER BY
                  FIELD(`rank`,
                        'Sub Maj',
                        'Subedar Major',
                        'Subedar',
                        'Naib Subedar'),
                  name
            """, home_states)

            senior_ranks = cursor.fetchall()

            for jco in senior_ranks:
                state = jco['home_state']
                jco_company = jco['company']
                key = (state, jco_company)          # ← keyed by both
                if key not in jco_map:
                    jco_map[key] = jco['name']       # most senior per state+company

            # 4️⃣ Assigned JCOs (Pending) — unchanged
            cursor.execute(f"""
                SELECT 
                    ja.additional_assigned_home_state AS home_state,
                    p.name AS jco_name
                FROM jco_kunda_assignment ja
                JOIN personnel p
                    ON p.army_number = ja.army_number
                WHERE ja.additional_assigned_home_state IN ({placeholders})
                  AND ja.interview_status = 'Pending'
            """, home_states)

            assigned_rows = cursor.fetchall()

            for row in assigned_rows:
                state = row['home_state']
                if state not in assigned_jco_map:
                    assigned_jco_map[state] = row['jco_name']

        # 5️⃣ Attach JCO with fallback logic — company-aware lookup
        for row in pending_data:
            state = row['home_state']
            soldier_company = row['company']
            key = (state, soldier_company)           # ← match soldier's company

            if key in jco_map:
                row['jco_name'] = jco_map[key]
                row['jco_source'] = 'live'

            elif state in assigned_jco_map:
                row['jco_name'] = f"Temporaray assigned JCO {assigned_jco_map[state]}"
                row['jco_source'] = 'assigned'

            else:
                row['jco_name'] = None
                row['jco_source'] = None

        return jsonify({
            "status": "success",
            "pending_interviews": pending_data
        })

    finally:
        cursor.close()
        conn.close()


@inteview_bp.route('/get-available-jcos')
def get_available_jcos():
    user = require_login()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    company = user['company']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT 
                army_number,
                name,
                `rank`,
                company,
                home_state
            FROM personnel
            
              where `rank` IN ('Naib Subedar', 'Subedar', 'Sub Maj', 'Subedar Major')
              AND onleave_status = 0
              AND detachment_status = 0
              AND posting_status = 0
            ORDER BY
              FIELD(`rank`,
                    'Sub Maj',
                    'Subedar Major',
                    'Subedar',
                    'Naib Subedar'),
              name
        """,)

        jco_result = cursor.fetchall()

        return jsonify({
            "status": "success",
            "jcos": jco_result
        })

    finally:
        cursor.close()
        conn.close()


@inteview_bp.route('/assign_jco', methods=['POST'])
def assign_jco():
    data = request.get_json()

    army_number = data.get('army_number')
    state = data.get('additional_assigned_home_state')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO jco_kunda_assignment 
            (army_number, additional_assigned_home_state, interview_status)
            VALUES (%s, %s, 'Pending')
            ON DUPLICATE KEY UPDATE
                additional_assigned_home_state = VALUES(additional_assigned_home_state),
                interview_status = 'Pending'
        """, (army_number, state))

        conn.commit()
        return jsonify(success=True)

    except Exception as e:
        conn.rollback()
        return jsonify(success=False, message=str(e))

    finally:
        cursor.close()
        conn.close()
@inteview_bp.route('/get_remarks/<int:id>', methods=['GET'])
def get_remarks(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT interview_remarks FROM personnel WHERE id = %s",
            (id,)
        )
        row = cursor.fetchone()
        return jsonify({ 'remarks': row['interview_remarks'] if row else '' })
    except Exception as e:
        return jsonify({ 'remarks': '' })
    finally:
        if cursor: cursor.close()
        conn.close()
@inteview_bp.route('/temp_completed_kunba', methods=['GET'])
def my_completed_interviews():

    user = require_login()

    current_army_number = user['army_number'].strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                army_number,
                `rank`,
                name,
                company,
                home_state,
                interview_remarks,
                temp_interview_done_by,
                updated_at AS completed_on
            FROM personnel
            WHERE interview_status = 1
              AND LOWER(TRIM(temp_interview_done_by)) = LOWER(TRIM(%s))
            ORDER BY updated_at DESC
        """

        cursor.execute(query, (current_army_number,))

        rows = cursor.fetchall()

        return jsonify(rows)

    except Exception as e:
        return jsonify([])

    finally:
        if cursor:
            cursor.close()
            conn.close()

@inteview_bp.route('/get_remarks_by_army/<army_number>', methods=['GET'])
def get_remarks_by(army_number):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT interview_remarks FROM personnel WHERE army_number = %s",
            (army_number,)
        )
        row = cursor.fetchone()
        return jsonify({ 'remarks': row['interview_remarks'] if row else '' })
    except Exception as e:
        return jsonify({ 'remarks': '' })
    finally:
        if cursor: cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════════════
#  COMPANY INTERVIEW  — NEW TABLE + ROUTES
# ═══════════════════════════════════════════════════════════

@inteview_bp.route('/init_company_interview_table', methods=['POST'])
def init_company_interview_table():
    """One-time setup: create company_interview table if not exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_interview (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                army_number      VARCHAR(100) NOT NULL UNIQUE,
                interview_status TINYINT      NOT NULL DEFAULT 0,
                interview_done_on DATE         DEFAULT NULL,
                remarks          TEXT         DEFAULT NULL,
                created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_ci_army
                    FOREIGN KEY (army_number)
                    REFERENCES personnel(army_number)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
        """)
        conn.commit()
        return jsonify({"status": "success", "message": "company_interview table ready"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@inteview_bp.route('/company_interview_pending', methods=['GET'])
def get_company_interview_pending():
    """
    Returns personnel whose interview is pending:
    - interview_status = 0 (or no record yet)
    - OR interview_status = 1 AND interview_done_on is older than 3 months.
    If user's company is Admin/ADMIN/ALL or role in CO/2IC/ADJUTANT, fetch all companies.
    """
    user = require_login()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    req_coy = request.args.get('company', '').strip()
    user_coy = user.get('company', '').strip()
    role = user.get('role', '').strip().upper()

    coy_to_check = req_coy if req_coy else user_coy

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        is_admin_view = (coy_to_check.upper() in ['ADMIN', 'ALL']) or (role in ['CO', '2IC', 'ADJUTANT'])

        if coy_to_check and coy_to_check.upper() not in ['ADMIN', 'ALL'] and role not in ['CO', '2IC', 'ADJUTANT']:
            cursor.execute("""
                SELECT
                    p.army_number,
                    p.`rank`,
                    p.name,
                    p.company,
                    ci.id                   AS ci_id,
                    COALESCE(ci.interview_status, 0) AS interview_status,
                    ci.interview_done_on,
                    ci.remarks
                FROM personnel p
                LEFT JOIN company_interview ci ON ci.army_number = p.army_number
                WHERE (
                    ci.id IS NULL
                    OR ci.interview_status = 0
                    OR (ci.interview_status = 1 AND ci.interview_done_on <= DATE_SUB(CURDATE(), INTERVAL 3 MONTH))
                )
                AND LOWER(TRIM(p.company)) = LOWER(TRIM(%s))
                ORDER BY p.`rank`, p.name
            """, (coy_to_check,))
            pending_rows = cursor.fetchall()

            cursor.execute("""
                SELECT
                    p.army_number,
                    p.`rank`,
                    p.name,
                    p.company,
                    ci.id                   AS ci_id,
                    ci.interview_status,
                    ci.interview_done_on,
                    ci.remarks
                FROM personnel p
                JOIN company_interview ci ON ci.army_number = p.army_number
                WHERE ci.interview_status = 1
                  AND ci.interview_done_on > DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                  AND LOWER(TRIM(p.company)) = LOWER(TRIM(%s))
                ORDER BY ci.interview_done_on DESC, p.`rank`, p.name
            """, (coy_to_check,))
            completed_rows = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT
                    p.army_number,
                    p.`rank`,
                    p.name,
                    p.company,
                    ci.id                   AS ci_id,
                    COALESCE(ci.interview_status, 0) AS interview_status,
                    ci.interview_done_on,
                    ci.remarks
                FROM personnel p
                LEFT JOIN company_interview ci ON ci.army_number = p.army_number
                WHERE (
                    ci.id IS NULL
                    OR ci.interview_status = 0
                    OR (ci.interview_status = 1 AND ci.interview_done_on <= DATE_SUB(CURDATE(), INTERVAL 3 MONTH))
                )
                ORDER BY p.company, p.`rank`, p.name
            """)
            pending_rows = cursor.fetchall()

            cursor.execute("""
                SELECT
                    p.army_number,
                    p.`rank`,
                    p.name,
                    p.company,
                    ci.id                   AS ci_id,
                    ci.interview_status,
                    ci.interview_done_on,
                    ci.remarks
                FROM personnel p
                JOIN company_interview ci ON ci.army_number = p.army_number
                WHERE ci.interview_status = 1
                  AND ci.interview_done_on > DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                ORDER BY ci.interview_done_on DESC, p.company, p.`rank`, p.name
            """)
            completed_rows = cursor.fetchall()

        # Format dates reliably in Python
        for r in pending_rows + completed_rows:
            if r.get('interview_done_on'):
                try:
                    if hasattr(r['interview_done_on'], 'strftime'):
                        r['interview_done_on'] = r['interview_done_on'].strftime('%d %b %Y')
                    else:
                        r['interview_done_on'] = str(r['interview_done_on'])
                except Exception:
                    r['interview_done_on'] = str(r['interview_done_on'])

        return jsonify({
            "status":    "success",
            "count":     len(pending_rows),
            "pending":   pending_rows,
            "completed": completed_rows,
            "is_admin":  is_admin_view
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@inteview_bp.route('/company_interview_count', methods=['GET'])
def get_company_interview_count():
    """Lightweight count-only endpoint for the dashboard card (pending out of total)."""
    user = require_login()
    if not user:
        return jsonify({"count": 0, "pending": 0, "total": 0})

    req_coy = request.args.get('company', '').strip()
    user_coy = user.get('company', '').strip()
    role = user.get('role', '').strip().upper()

    coy_to_check = req_coy if req_coy else user_coy

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if coy_to_check and coy_to_check.upper() not in ['ADMIN', 'ALL'] and role not in ['CO', '2IC', 'ADJUTANT']:
            cursor.execute("""
                SELECT COUNT(*)
                FROM personnel p
                LEFT JOIN company_interview ci ON ci.army_number = p.army_number
                WHERE (
                    ci.id IS NULL
                    OR ci.interview_status = 0
                    OR (ci.interview_status = 1 AND ci.interview_done_on <= DATE_SUB(CURDATE(), INTERVAL 3 MONTH))
                )
                AND LOWER(TRIM(p.company)) = LOWER(TRIM(%s))
            """, (coy_to_check,))
            pending = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM personnel WHERE LOWER(TRIM(company)) = LOWER(TRIM(%s))", (coy_to_check,))
            total = cursor.fetchone()[0]
        else:
            cursor.execute("""
                SELECT COUNT(*)
                FROM personnel p
                LEFT JOIN company_interview ci ON ci.army_number = p.army_number
                WHERE (
                    ci.id IS NULL
                    OR ci.interview_status = 0
                    OR (ci.interview_status = 1 AND ci.interview_done_on <= DATE_SUB(CURDATE(), INTERVAL 3 MONTH))
                )
            """)
            pending = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM personnel")
            total = cursor.fetchone()[0]

        return jsonify({"status": "success", "count": pending, "pending": pending, "total": total})

    except Exception as e:
        return jsonify({"status": "error", "count": 0, "pending": 0, "total": 0}), 500

    finally:
        cursor.close()
        conn.close()


@inteview_bp.route('/company_interview_done', methods=['POST'])
def mark_company_interview_done():
    """
    Mark a company_interview record as done for a soldier.
    Expects JSON: { "army_number": "<string>", "ci_id": <int (optional)>, "remarks": "<string>" }
    """
    user = require_login()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data        = request.get_json() or {}
    army_number = data.get('army_number', '').strip()
    ci_id       = data.get('ci_id')
    remarks     = data.get('remarks', '').strip()

    if not army_number and not ci_id:
        return jsonify({"status": "error", "message": "army_number or ci_id is required"}), 400

    word_count = len(remarks.split()) if remarks else 0
    if word_count < 30:
        return jsonify({"status": "error", "message": f"Remarks must be at least 30 words minimum (currently {word_count} words)"}), 400

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        if ci_id:
            cursor.execute("""
                UPDATE company_interview
                SET interview_status   = 1,
                    interview_done_on  = CURDATE(),
                    remarks            = %s
                WHERE id = %s
            """, (remarks, ci_id))
        else:
            cursor.execute("""
                INSERT INTO company_interview (army_number, interview_status, interview_done_on, remarks)
                VALUES (%s, 1, CURDATE(), %s)
                ON DUPLICATE KEY UPDATE
                    interview_status  = 1,
                    interview_done_on = CURDATE(),
                    remarks           = VALUES(remarks)
            """, (army_number, remarks))

        conn.commit()

        return jsonify({"status": "success", "message": "Interview marked as done"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
