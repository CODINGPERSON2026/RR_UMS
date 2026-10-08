from imports import *
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import calendar

nominal_bp = Blueprint("nominal_bp", __name__, url_prefix="/Nominal_Roll")

JCO_RANKS = ('Subedar Major', 'Subedar', 'Naib Subedar')


@nominal_bp.route('/')
def nominal():
    return render_template('nominal_Roll/nominal_roll.html')


def attach_present_month_info(cursor, rows):
    if not rows:
        return
    now = datetime.now()
    present_day_of_month = now.day
    year = now.year
    month = now.month
    num_days = calendar.monthrange(year, month)[1]
    first_of_month = now.replace(day=1).date()
    today_date = now.date()
    month_end = date(year, month, num_days)

    leave_map = {}
    army_numbers = [r['army_number'] for r in rows if r.get('army_number')]
    if army_numbers:
        format_strings = ','.join(['%s'] * len(army_numbers))
        sql = f"""
            SELECT army_number, from_date, to_date 
            FROM leave_status_info 
            WHERE request_status = 'Approved' 
              AND army_number IN ({format_strings})
              AND from_date <= %s AND to_date >= %s
        """
        params = army_numbers + [month_end, first_of_month]
        try:
            cursor.execute(sql, params)
            leaves = cursor.fetchall()
            for l in leaves:
                an = l['army_number']
                f_date = l['from_date']
                t_date = l['to_date']
                if isinstance(f_date, datetime): f_date = f_date.date()
                if isinstance(t_date, datetime): t_date = t_date.date()
                if f_date and t_date:
                    leaves_map.setdefault(an, []).append((f_date, t_date))
                    start = max(f_date, first_of_month)
                    end = min(t_date, today_date)
                    if start <= end:
                        days = (end - start).days + 1
                        leave_map[an] = leave_map.get(an, 0) + days
        except Exception:
            leaves_map = {}

    for row in rows:
        row['present_day_of_month'] = present_day_of_month
        an = row.get('army_number')
        leave_days_this_month = leave_map.get(an, 0)
        row['present_days'] = max(0, present_day_of_month - leave_days_this_month)
        is_present = not row.get('onleave_status') and not row.get('detachment_status') and not row.get('oncourse_status') and not row.get('td_status')
        row['present_status'] = 'P' if is_present else None

        # Build 1-31 daily sheet for individual detail view
        p_leaves = leaves_map.get(an, []) if 'leaves_map' in locals() else []
        daily_sheet = {}
        for d in range(1, num_days + 1):
            cur_d = date(year, month, d)
            on_leave = False
            for f_d, t_d in p_leaves:
                if f_d <= cur_d <= t_d:
                    on_leave = True
                    break
            if on_leave:
                st = 'L'
            elif cur_d == today_date:
                if row.get('onleave_status'): st = 'L'
                elif row.get('detachment_status'): st = 'DET'
                elif row.get('oncourse_status'): st = 'C'
                elif row.get('td_status'): st = 'TD'
                else: st = 'P'
            elif cur_d < today_date:
                if row.get('detachment_status'): st = 'DET'
                elif row.get('oncourse_status'): st = 'C'
                elif row.get('td_status'): st = 'TD'
                else: st = 'P'
            else:
                st = ''
            daily_sheet[str(d)] = st
        row['daily_sheet'] = daily_sheet
        row['num_days_in_month'] = num_days


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
                COALESCE(NULLIF(home_phone, ''), (SELECT number FROM mobile_phones mp WHERE mp.personnel_id = personnel.id ORDER BY mp.id ASC LIMIT 1), '—') AS mobile_number,
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

        attach_present_month_info(cursor, rows)

        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'data': rows,
            'present_day_of_month': datetime.now().day
        })

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
                date_of_tors,
                onleave_status,
                detachment_status,
                oncourse_status,
                td_status
            FROM personnel
            WHERE army_number = %s
        """
        cursor.execute(sql, (army_number,))
        row = cursor.fetchone()

        if row:
            attach_present_month_info(cursor, [row])

        cursor.close()
        conn.close()

        if not row:
            return jsonify({'status': 'error', 'message': 'Personnel not found'}), 404

        # Format dates for JSON
        for k, v in row.items():
            if isinstance(v, (date, datetime)):
                row[k] = v.strftime('%d/%m/%Y')

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
                COALESCE(NULLIF(home_phone, ''), (SELECT number FROM mobile_phones mp WHERE mp.personnel_id = personnel.id ORDER BY mp.id ASC LIMIT 1), '—') AS mobile_number,
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

        attach_present_month_info(cursor, rows)

        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'data': rows, 'present_day_of_month': datetime.now().day})

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
                row['from_date'] = row['from_date'].strftime('%d/%m/%Y')
            if row.get('to_date'):
                row['to_date'] = row['to_date'].strftime('%d/%m/%Y')

        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'data': rows})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@nominal_bp.route('/api/monthly_sheet', methods=['GET'])
def get_monthly_sheet():
    user = require_login()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    current_user_role    = user.get('role')
    current_user_company = user.get('company')

    try:
        company     = request.args.get('company', 'ALL')
        section     = request.args.get('section', 'ALL')
        rank_filter = request.args.get('rank',    'ALL')
        query_str   = request.args.get('q', '').strip()
        
        now = datetime.now()
        year = int(request.args.get('year', now.year))
        month = int(request.args.get('month', now.month))
        
        num_days = calendar.monthrange(year, month)[1]
        month_start = date(year, month, 1)
        month_end = date(year, month, num_days)
        today_date = now.date()

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

        if section != 'ALL':
            query += " AND section = %s"
            params.append(section)

        if rank_filter == 'JCO':
            placeholders = ','.join(['%s'] * len(JCO_RANKS))
            query += f" AND `rank` IN ({placeholders})"
            params.extend(JCO_RANKS)
        elif rank_filter != 'ALL':
            query += " AND `rank` = %s"
            params.append(rank_filter)

        if query_str:
            query += " AND (army_number LIKE %s OR name LIKE %s)"
            params.extend([f"%{query_str}%", f"%{query_str}%"])

        query += " ORDER BY company, `rank`, army_number LIMIT 200"

        cursor.execute(query, params)
        personnel_rows = cursor.fetchall()

        army_numbers = [r['army_number'] for r in personnel_rows if r.get('army_number')]
        leaves_map = {}
        
        if army_numbers:
            ph = ','.join(['%s'] * len(army_numbers))
            l_sql = f"""
                SELECT army_number, from_date, to_date, leave_type
                FROM leave_status_info
                WHERE request_status = 'Approved'
                  AND army_number IN ({ph})
                  AND from_date <= %s AND to_date >= %s
            """
            cursor.execute(l_sql, army_numbers + [month_end, month_start])
            leaves = cursor.fetchall()
            for l in leaves:
                an = l['army_number']
                f_date = l['from_date']
                t_date = l['to_date']
                if isinstance(f_date, datetime): f_date = f_date.date()
                if isinstance(t_date, datetime): t_date = t_date.date()
                if f_date and t_date:
                    leaves_map.setdefault(an, []).append((f_date, t_date, l.get('leave_type', 'L')))

        result_data = []
        for p in personnel_rows:
            an = p['army_number']
            p_leaves = leaves_map.get(an, [])
            
            daily_sheet = {}
            total_present = 0
            for d in range(1, num_days + 1):
                cur_d = date(year, month, d)
                
                on_leave = False
                for f_d, t_d, lt in p_leaves:
                    if f_d <= cur_d <= t_d:
                        on_leave = True
                        break
                
                if on_leave:
                    status = 'L'
                elif cur_d == today_date:
                    if p.get('onleave_status'): status = 'L'
                    elif p.get('detachment_status'): status = 'DET'
                    elif p.get('oncourse_status'): status = 'C'
                    elif p.get('td_status'): status = 'TD'
                    else: 
                        status = 'P'
                        total_present += 1
                elif cur_d < today_date:
                    if p.get('detachment_status'): status = 'DET'
                    elif p.get('oncourse_status'): status = 'C'
                    elif p.get('td_status'): status = 'TD'
                    else: 
                        status = 'P'
                        total_present += 1
                else:
                    status = ''
                
                daily_sheet[str(d)] = status

            p['daily_sheet'] = daily_sheet
            p['total_present'] = total_present
            result_data.append(p)

        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'year': year,
            'month': month,
            'month_name': month_start.strftime('%B %Y'),
            'num_days': num_days,
            'today_day': now.day if (now.year == year and now.month == month) else None,
            'data': result_data
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500