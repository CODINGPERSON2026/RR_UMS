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
    try:
        company     = request.args.get('company', 'ALL')
        trade       = request.args.get('trade',   'ALL')
        section     = request.args.get('section', 'ALL')
        rank_filter = request.args.get('rank',    'ALL')
        batch       = request.args.get('batch',   'ALL')

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
                detachment_status
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
    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

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
                detachment_status
            FROM personnel
            WHERE army_number LIKE %s OR name LIKE %s
            LIMIT 20
        """
        search_val = f"%{query_str}%"
        cursor.execute(sql, (search_val, search_val))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'data': rows})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500