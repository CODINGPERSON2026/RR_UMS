from imports import *
loan_bp = Blueprint('loan_bp', __name__, url_prefix='/loan_details')

@loan_bp.route("/summary")
def loan_summary():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            SUM(CASE WHEN CAST(total_amount AS DECIMAL(12,2)) BETWEEN 0 AND 500000 THEN 1 ELSE 0 END) AS l0_5,
            SUM(CASE WHEN CAST(total_amount AS DECIMAL(12,2)) BETWEEN 500001 AND 1000000 THEN 1 ELSE 0 END) AS l6_10,
            SUM(CASE WHEN CAST(total_amount AS DECIMAL(12,2)) BETWEEN 1000001 AND 1500000 THEN 1 ELSE 0 END) AS l11_15,
            SUM(CASE WHEN CAST(total_amount AS DECIMAL(12,2)) BETWEEN 1500001 AND 2000000 THEN 1 ELSE 0 END) AS l16_20,
            SUM(CASE WHEN CAST(total_amount AS DECIMAL(12,2)) > 2000000 THEN 1 ELSE 0 END) AS l20_plus
        FROM loans
    """)

    data = cursor.fetchone() or {'l0_5': 0, 'l6_10': 0, 'l11_15': 0, 'l16_20': 0, 'l20_plus': 0}
    cursor.close()
    conn.close()

    return jsonify(data)

@loan_bp.route("/by-range/<range_key>")
def loans_by_range(range_key):
    ranges = {
        "all": (0, 999999999),
        "0_5": (0, 500000),
        "6_10": (500001, 1000000),
        "11_15": (1000001, 1500000),
        "16_20": (1500001, 2000000),
        "20_plus": (2000000, None)
    }

    low, high = ranges.get(range_key, (0, 999999999))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    base_query = """
        SELECT
            l.army_number,
            p.rank,
            p.name AS name,
            p.company AS company_name,
            l.loan_type,
            l.total_amount,
            l.pending,
            l.emi_per_month
        FROM loans l
        JOIN personnel p ON p.id = l.personnel_id
    """

    if range_key == "all":
        query = base_query + " ORDER BY CAST(l.total_amount AS DECIMAL(12,2)) DESC"
        cursor.execute(query)
    elif high:
        query = base_query + " WHERE CAST(l.total_amount AS DECIMAL(12,2)) BETWEEN %s AND %s ORDER BY CAST(l.total_amount AS DECIMAL(12,2)) DESC"
        cursor.execute(query, (low, high))
    else:
        query = base_query + " WHERE CAST(l.total_amount AS DECIMAL(12,2)) > %s ORDER BY CAST(l.total_amount AS DECIMAL(12,2)) DESC"
        cursor.execute(query, (low,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(rows)