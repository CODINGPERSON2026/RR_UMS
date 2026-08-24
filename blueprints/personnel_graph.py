from imports import *
from middleware import require_login

personnel_graph_bp = Blueprint('personnel_graph_bp', __name__, url_prefix='/personnel_graph')

RANK_SHORT_MAP = {
    'subedar major':            'Sub Maj',
    'sb maj':                   'Sub Maj',
    'sub major':                'Sub Maj',
    'sub maj':                  'Sub Maj',
    'sb/maj':                   'Sub Maj',
    'sub/maj':                  'Sub Maj',
    'subedar_major':            'Sub Maj',
    'subedar':                  'Sub',
    'sb':                       'Sub',
    'sub':                      'Sub',
    'naib subedar':             'Nb Sub',
    'nb sub':                   'Nb Sub',
    'nb sb':                    'Nb Sub',
    'nbsub':                    'Nb Sub',
    'naib sub':                 'Nb Sub',
    'nb/sub':                   'Nb Sub',
    'regimental havildar major':'RHM',
    'rhm':                      'RHM',
    'company havildar major':   'CHM',
    'chm':                      'CHM',
    'company quartermaster havildar': 'CQMH',
    'cqmh':                     'CQMH',
    'havildar':                 'Hav',
    'hav':                      'Hav',
    'local havildar':           'Loc Hav',
    'loc havildar':             'Loc Hav',
    'loc hav':                  'Loc Hav',
    'loc-hav':                  'Loc Hav',
    'lance havildar':           'L Hav',
    'l havildar':               'L Hav',
    'l hav':                    'L Hav',
    'l/hav':                    'L Hav',
    'lhav':                     'L Hav',
    'l-hav':                    'L Hav',
    'naik':                     'NK',
    'nk':                       'NK',
    'local naik':               'Loc NK',
    'loc naik':                 'Loc NK',
    'loc nk':                   'Loc NK',
    'loc-nk':                   'Loc NK',
    'lance naik':               'L NK',
    'l naik':                   'L NK',
    'l nk':                     'L NK',
    'l/nk':                     'L NK',
    'lnk':                      'L NK',
    'l-nk':                     'L NK',
    'craftsman':                'CFN',
    'cfn':                      'CFN',
    'signal man':               'Sigmn',
    'signalman':                'Sigmn',
    'sgl mn':                   'Sigmn',
    'sglman':                   'Sigmn',
    'sigmn':                    'Sigmn',
    'sgl':                      'Sigmn',
    'sig':                      'Sigmn',
    'sigman':                   'Sigmn',
    'sig mn':                   'Sigmn',
    'agniveer':                 'Agv',
    'agnl':                     'Agv',
    'agni':                     'Agv',
    'agv':                      'Agv',
    'agn':                      'Agv'
}

# Build mapping from displayed short name back to raw database values
DISPLAY_TO_RAW_RANKS = {}
for raw_val, short_display in RANK_SHORT_MAP.items():
    s_key = short_display.strip().lower()
    if s_key not in DISPLAY_TO_RAW_RANKS:
        DISPLAY_TO_RAW_RANKS[s_key] = set()
    DISPLAY_TO_RAW_RANKS[s_key].add(raw_val.strip().lower())

@personnel_graph_bp.route('/api/graph-personnel')
def get_graph_personnel():
    try:
        user = require_login()
        user_company = user.get('company', 'Admin') if (user and isinstance(user, dict)) else 'Admin'
    except Exception:
        user_company = 'Admin'

    graph_type = request.args.get('graph_type', '').strip()
    slice_label = request.args.get('slice_label', '').strip()
    req_company = request.args.get('company', 'All').strip()

    if user_company not in ['Admin', 'Center']:
        effective_company = user_company
    else:
        effective_company = req_company

    connection = get_db_connection()
    if not connection:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                p.id,
                p.name,
                p.army_number,
                p.rank,
                p.company,
                p.trade,
                p.home_state,
                p.med_cat,
                TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
                TIMESTAMPDIFF(YEAR, p.date_of_enrollment, CURDATE()) AS service_years
            FROM personnel p
        """
        where_clauses = []
        params = []

        # Company filter
        if effective_company and effective_company.lower() != 'all':
            where_clauses.append("LOWER(TRIM(p.company)) = LOWER(TRIM(%s))")
            params.append(effective_company)

        # Graph type filtering
        if graph_type == 'age':
            where_clauses.append("p.date_of_birth IS NOT NULL")
            if '-' in slice_label:
                parts = slice_label.split('-')
                try:
                    min_age, max_age = int(parts[0]), int(parts[1])
                    where_clauses.append("TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) BETWEEN %s AND %s")
                    params.extend([min_age, max_age])
                except ValueError:
                    pass
            elif '+' in slice_label:
                try:
                    min_age = int(slice_label.replace('+', ''))
                    where_clauses.append("TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) >= %s")
                    params.append(min_age)
                except ValueError:
                    pass

        elif graph_type == 'rank':
            target_label = slice_label.strip().lower()
            matched_raw_ranks = list(DISPLAY_TO_RAW_RANKS.get(target_label, {target_label}))
            if target_label not in matched_raw_ranks:
                matched_raw_ranks.append(target_label)

            rank_conditions = ["LOWER(TRIM(p.rank)) = %s" for _ in matched_raw_ranks]
            where_clauses.append("(" + " OR ".join(rank_conditions) + ")")
            params.extend(matched_raw_ranks)

        elif graph_type == 'state':
            where_clauses.append("LOWER(TRIM(p.home_state)) = LOWER(TRIM(%s))")
            params.append(slice_label)

        elif graph_type == 'service':
            where_clauses.append("p.date_of_enrollment IS NOT NULL")
            clean_label = slice_label.lower().replace('yrs', '').replace('years', '').strip()
            if '-' in clean_label:
                parts = clean_label.split('-')
                try:
                    min_yr, max_yr = int(parts[0]), int(parts[1])
                    where_clauses.append("TIMESTAMPDIFF(YEAR, p.date_of_enrollment, CURDATE()) BETWEEN %s AND %s")
                    params.extend([min_yr, max_yr])
                except ValueError:
                    pass
            elif '+' in clean_label:
                try:
                    min_yr = int(clean_label.replace('+', ''))
                    where_clauses.append("TIMESTAMPDIFF(YEAR, p.date_of_enrollment, CURDATE()) >= %s")
                    params.append(min_yr)
                except ValueError:
                    pass

        elif graph_type == 'sports':
            query = """
                SELECT DISTINCT
                    p.id,
                    p.name,
                    p.army_number,
                    p.rank,
                    p.company,
                    p.trade,
                    p.home_state,
                    p.med_cat,
                    TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
                    TIMESTAMPDIFF(YEAR, p.date_of_enrollment, CURDATE()) AS service_years
                FROM personnel p
                INNER JOIN personnel_sports ps ON p.id = ps.personnel_id
            """
            where_clauses.append("(LOWER(TRIM(ps.sport_name)) = LOWER(TRIM(%s)) OR LOWER(TRIM(ps.sport_type)) = LOWER(TRIM(%s)))")
            params.extend([slice_label, slice_label])

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY p.id DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        # Sanitize data types
        for r in rows:
            r['age'] = r['age'] if r.get('age') is not None else '—'
            r['service_years'] = r['service_years'] if r.get('service_years') is not None else '—'
            r['home_state'] = r['home_state'] if r.get('home_state') else '—'
            r['trade'] = r['trade'] if r.get('trade') else '—'

        return jsonify({'status': 'success', 'count': len(rows), 'rows': rows}), 200

    except Exception as e:
        print(f"Error in personnel graph personnel API: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        cursor.close()
        connection.close()
