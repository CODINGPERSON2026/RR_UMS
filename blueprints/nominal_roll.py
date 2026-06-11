from imports import *
from dateutil.relativedelta import relativedelta
from datetime import datetime, date

nominal_bp = Blueprint("nominal_bp", __name__, url_prefix="/Nominal_Roll")

JCO_RANKS = ('Subedar Major', 'Subedar', 'Naib Subedar')


@nominal_bp.route('/')
def nominal():
    return render_template('nominal_Roll/nominal_roll.html')


@nominal_bp.route('/api/personnel', methods=['GET'])
def get_personnel():
    user = require_login()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    current_user_role    = user.get('role')
    current_user_company = user.get('company')

    try:
        company     = request.args.get('company', 'ALL')
        trade       = request.args.get('trade',   'ALL')
        section     = request.args.get('section', 'ALL')
        rank_filter = request.args.get('rank',    'ALL')
        batch       = request.args.get('batch',   'ALL')

        # Restriction logic
        if current_user_role not in ['CO', '2IC', 'ADJUTANT', 'Subedar Major', 'clerk', 'admin', 'O CENTRE NCO']:
            if current_user_company:
                company = current_user_company

        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                army_number,
                UPPER(name) AS name,
                `rank`,
                trade,
                UPPER(company) AS company,
                section,
                UPPER(batch) AS batch,
                onleave_status,
                detachment_status,
                oncourse_status,
                td_status
            FROM personnel
            WHERE 1=1
        """
        params = []

        if company != 'ALL':
            query += " AND UPPER(company) = %s"
            params.append(company.upper())

        if trade != 'ALL':
            query += " AND trade = %s"
            params.append(trade)

        if section != 'ALL':
            query += " AND section = %s"
            params.append(section)

        if rank_filter == 'Agniveer' and batch != 'ALL':
            query += " AND UPPER(batch) = %s"
            params.append(batch.upper())

        if rank_filter == 'JCO':
            placeholders = ','.join(['%s'] * len(JCO_RANKS))
            query += f" AND `rank` IN ({placeholders})"
            params.extend(JCO_RANKS)
        elif rank_filter != 'ALL':
            query += " AND `rank` = %s"
            params.append(rank_filter)

        query += " ORDER BY company, `rank`, army_number"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'data': rows})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@nominal_bp.route('/api/details/<army_number>', methods=['GET'])
def get_personnel_details(army_number):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT
                army_number,
                UPPER(name) AS name,
                `rank`,
                trade,
                section,
                UPPER(company) AS company,
                date_of_birth,
                blood_group,
                i_card_no,
                home_phone,
                home_to,
                home_po,
                home_ps,
                home_teh,
                home_nrs,
                home_nmh,
                home_district,
                date_of_tos,
                date_of_tors
            FROM personnel
            WHERE army_number = %s
        """
        cursor.execute(sql, (army_number,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            return jsonify({'status': 'error', 'message': 'Personnel not found'}), 404

        # Format dates for JSON
        for k, v in row.items():
            if isinstance(v, (date, datetime)):
                row[k] = v.strftime('%d %b %Y')

        return jsonify({'status': 'success', 'data': row})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@nominal_bp.route('/api/filters', methods=['GET'])
def get_filters():
    user = require_login()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    current_user_role    = user.get('role')
    current_user_company = user.get('company')

    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if current_user_role not in ['CO', '2IC', 'ADJUTANT', 'Subedar Major', 'clerk', 'admin', 'O CENTRE NCO'] and current_user_company:
            companies = [current_user_company.upper()]
        else:
            cursor.execute("SELECT DISTINCT UPPER(company) AS company FROM personnel WHERE company IS NOT NULL ORDER BY company")
            companies = [r['company'] for r in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT trade FROM personnel WHERE trade IS NOT NULL ORDER BY trade")
        trades = [r['trade'] for r in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT section FROM personnel WHERE section IS NOT NULL ORDER BY section")
        sections = [r['section'] for r in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT `rank` FROM personnel
            WHERE `rank` IS NOT NULL
            AND `rank` NOT IN ('Subedar Major', 'Subedar', 'Naib Subedar')
            ORDER BY `rank`
        """)
        other_ranks = [r['rank'] for r in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT UPPER(batch) AS batch FROM personnel WHERE batch IS NOT NULL AND batch != '' ORDER BY batch")
        batches = [r['batch'] for r in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({
            'status':      'success',
            'companies':   companies,
            'trades':      trades,
            'sections':    sections,
            'other_ranks': other_ranks,
            'batches':     batches
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@nominal_bp.route('/api/search', methods=['GET'])
def search_personnel():
    user = require_login()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    current_user_role    = user.get('role')
    current_user_company = user.get('company')

    try:
        query_str = request.args.get('q', '').strip()
        if not query_str:
            return jsonify({'status': 'success', 'data': []})

        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT
                army_number,
                UPPER(name) AS name,
                `rank`,
                trade,
                UPPER(company) AS company,
                section,
                UPPER(batch) AS batch,
                onleave_status,
                detachment_status,
                oncourse_status,
                td_status
            FROM personnel
            WHERE (army_number LIKE %s OR name LIKE %s)
        """
        params = [f"%{query_str}%", f"%{query_str}%"]

        if current_user_role not in ['CO', '2IC', 'ADJUTANT', 'Subedar Major', 'clerk', 'admin', 'O CENTRE NCO'] and current_user_company:
            sql += " AND UPPER(company) = %s"
            params.append(current_user_company.upper())

        sql += " LIMIT 20"
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'data': rows})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@nominal_bp.route('/api/leave_history', methods=['GET'])
def get_leave_history():
    user = require_login()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    current_user_role    = user.get('role')
    current_user_company = user.get('company')

    try:
        company = request.args.get('company', 'ALL')
        section = request.args.get('section', 'ALL')
        query_str = request.args.get('q', '').strip()

        # Restriction logic
        if current_user_role not in ['CO', '2IC', 'ADJUTANT', 'Subedar Major', 'clerk', 'admin', 'O CENTRE NCO']:
            if current_user_company:
                company = current_user_company

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                l.id,
                l.army_number,
                UPPER(l.name) AS name,
                l.`rank`,
                l.leave_type,
                l.leave_days,
                l.from_date,
                l.to_date,
                UPPER(l.company) AS company,
                p.section,
                l.request_status
            FROM leave_status_info l
            LEFT JOIN personnel p ON l.army_number = p.army_number
            WHERE 1=1
        """
        params = []

        if company != 'ALL':
            query += " AND UPPER(l.company) = %s"
            params.append(company.upper())

        if section != 'ALL':
            query += " AND p.section = %s"
            params.append(section)

        if query_str:
            query += " AND (l.army_number LIKE %s OR l.name LIKE %s)"
            search_val = f"%{query_str}%"
            params.append(search_val)
            params.append(search_val)

        query += " ORDER BY l.army_number ASC, l.from_date DESC LIMIT 100"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Format dates
        for row in rows:
            if row.get('from_date'):
                row['from_date'] = row['from_date'].strftime('%d %b %Y')
            if row.get('to_date'):
                row['to_date'] = row['to_date'].strftime('%d %b %Y')

        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'data': rows})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500