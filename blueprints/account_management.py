from imports import *
from datetime import datetime

accounts_bp = Blueprint('account', __name__, url_prefix='/account')


# ==========================================
# HELPER: FINANCIAL YEAR
# ==========================================
def get_financial_year():
    today = datetime.today()
    year = today.year

    if today.month >= 4:  # April onwards
        return f"{year}-{year+1}"
    else:
        return f"{year-1}-{year}"


# ==========================================
# DASHBOARD PAGE
# ==========================================
@accounts_bp.route('/')
def accounts():

    fy = request.args.get("fy") or get_financial_year()

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT 
            g.id,
            g.name,
            g.code_head,
            IFNULL(a.total_allotment, 0) AS total_allotment,
            IFNULL(s.no_of_sos, 0) AS no_of_sos,
            IFNULL(e.total_expenditure, 0) AS total_expenditure
        FROM grants g

        LEFT JOIN (
            SELECT grant_id, SUM(amount) AS total_allotment
            FROM grant_allocations
            WHERE financial_year = %s
            GROUP BY grant_id
        ) a ON g.id = a.grant_id

        LEFT JOIN (
            SELECT grant_id, COUNT(*) AS no_of_sos
            FROM sanction_orders
            WHERE financial_year = %s
            GROUP BY grant_id
        ) s ON g.id = s.grant_id

        LEFT JOIN (
            SELECT grant_id, SUM(amount) AS total_expenditure
            FROM expenditures
            WHERE financial_year = %s
            GROUP BY grant_id
        ) e ON g.id = e.grant_id

        WHERE g.financial_year = %s
    """

    cursor.execute(query, (fy, fy, fy, fy))
    grants = cursor.fetchall()

    for row in grants:

        total_allotment = float(row['total_allotment'] or 0)
        total_expenditure = float(row['total_expenditure'] or 0)

        row['balance'] = total_allotment - total_expenditure
        row['exp_percent'] = (
            round((total_expenditure / total_allotment) * 100, 2)
            if total_allotment > 0 else 0
        )


    cursor.close()
    db.close()

    return render_template(
        "account_management/account.html",
        grants=grants,
        current_fy=fy
    )


# ==========================================
# SUMMARY API
# ==========================================
@accounts_bp.route('/grants/summary')
def grant_summary():

    fy = request.args.get("fy") or get_financial_year()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            g.id,
            g.name,
            g.code_head,
            IFNULL(a.total_allotment, 0) AS total_allotment,
            IFNULL(s.no_of_sos, 0) AS no_of_sos,
            IFNULL(e.total_expenditure, 0) AS total_expenditure
        FROM grants g

        LEFT JOIN (
            SELECT grant_id, SUM(amount) AS total_allotment
            FROM grant_allocations
            WHERE financial_year = %s
            GROUP BY grant_id
        ) a ON g.id = a.grant_id

        LEFT JOIN (
            SELECT grant_id, COUNT(*) AS no_of_sos
            FROM sanction_orders
            WHERE financial_year = %s
            GROUP BY grant_id
        ) s ON g.id = s.grant_id

        LEFT JOIN (
            SELECT grant_id, SUM(amount) AS total_expenditure
            FROM expenditures
            WHERE financial_year = %s
            GROUP BY grant_id
        ) e ON g.id = e.grant_id

        WHERE g.financial_year = %s
    """

    cursor.execute(query, (fy, fy, fy, fy))
    results = cursor.fetchall()

    for row in results:

        total_allotment = float(row['total_allotment'] or 0)
        total_expenditure = float(row['total_expenditure'] or 0)

        row['balance'] = total_allotment - total_expenditure
        row['exp_percent'] = (
            round((total_expenditure / total_allotment) * 100, 2)
            if total_allotment > 0 else 0
        )


    cursor.close()
    conn.close()

    return jsonify(results)


# ==========================================
# CREATE GRANT + ORIGINAL ALLOCATION
# ==========================================
@accounts_bp.route('/grants/add', methods=['POST'])
def add_grant():

    data = request.get_json()
    fy = get_financial_year()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO grants (name, code_head, allotment, financial_year, created_at)
        VALUES (%s, %s, %s, %s, NOW())
    """, (data['name'], data['code_head'], data['allotment'], fy))

    grant_id = cursor.lastrowid
    original_amount = float(data['allotment'] or 0)


    cursor.execute("""
        INSERT INTO grant_allocations
        (grant_id, amount, allocation_type, remarks, financial_year)
        VALUES (%s, %s, 'Original', 'Initial Allotment', %s)
    """, (grant_id, original_amount, fy))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True})


# ==========================================
# GRANT DETAIL PAGE
# ==========================================
@accounts_bp.route('/grants/<int:grant_id>')
def grant_detail(grant_id):

    fy = request.args.get("fy") or get_financial_year()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, code_head
        FROM grants
        WHERE id = %s AND financial_year = %s
    """, (grant_id, fy))
    grant = cursor.fetchone()

    if not grant:
        return "Grant not found", 404

    # TOTAL ALLOTMENT
    cursor.execute("""
        SELECT IFNULL(SUM(amount),0) AS total_allotment
        FROM grant_allocations
        WHERE grant_id = %s AND financial_year = %s
    """, (grant_id, fy))
    total_allotment = float(cursor.fetchone()['total_allotment'] or 0)

    grant["allotment"] = total_allotment

    # TOTAL EXPENDITURE
    cursor.execute("""
        SELECT IFNULL(SUM(amount),0) AS total_exp
        FROM expenditures
        WHERE grant_id = %s AND financial_year = %s
    """, (grant_id, fy))
    total_exp = float(cursor.fetchone()['total_exp'] or 0)

    # SANCTION ORDERS
    cursor.execute("""
        SELECT id, so_number, so_amount, created_at
        FROM sanction_orders
        WHERE grant_id = %s AND financial_year = %s
        ORDER BY created_at DESC
    """, (grant_id, fy))
    sos = cursor.fetchall()

    # EXPENDITURES
    cursor.execute("""
        SELECT id, amount, remarks, created_at
        FROM expenditures
        WHERE grant_id = %s AND financial_year = %s
        ORDER BY created_at DESC
    """, (grant_id, fy))
    expenditures = cursor.fetchall()

    # ALLOTMENTS / ALLOCATIONS
    cursor.execute("""
        SELECT id, amount, allocation_type, remarks, created_at
        FROM grant_allocations
        WHERE grant_id = %s AND financial_year = %s
        ORDER BY created_at DESC
    """, (grant_id, fy))
    allocations = cursor.fetchall()

    balance = total_allotment - total_exp
    exp_percent = (
        round((total_exp / total_allotment) * 100, 2)
        if total_allotment > 0 else 0
    )


    cursor.close()
    conn.close()

    return render_template(
        "account_management/grant_detail.html",
        grant=grant,
        total_exp=total_exp,
        sos=sos,
        expenditures=expenditures,
        allocations=allocations,
        balance=balance,
        exp_percent=exp_percent,
        current_fy=fy
    )


# ==========================================
# ADD ADDITIONAL ALLOCATION
# ==========================================
@accounts_bp.route('/grants/<int:grant_id>/add-allocation', methods=['POST'])
def add_allocation(grant_id):

    data = request.get_json()
    amount = float(data.get("amount") or 0)
    fy = get_financial_year()

    if amount <= 0:
        return jsonify({"success": False, "message": "Invalid amount"})

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO grant_allocations
        (grant_id, amount, allocation_type, remarks, financial_year)
        VALUES (%s, %s, 'Additional', %s, %s)
    """, (grant_id, amount, data.get("remarks", ""), fy))

    conn.commit()
    cursor.close()
    conn.close()


    return jsonify({"success": True})


# ==========================================
# ADD EXPENDITURE
# ==========================================
@accounts_bp.route("/grants/<int:grant_id>/add-exp", methods=["POST"])
def add_expenditure(grant_id):

    data = request.get_json()
    amount = float(data.get("amount") or 0)
    fy = get_financial_year()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT IFNULL(SUM(amount),0) AS total_allotment
        FROM grant_allocations
        WHERE grant_id = %s AND financial_year = %s
    """, (grant_id, fy))
    total_allotment = float(cursor.fetchone()["total_allotment"] or 0)

    cursor.execute("""
        SELECT IFNULL(SUM(amount),0) AS total_exp
        FROM expenditures
        WHERE grant_id = %s AND financial_year = %s
    """, (grant_id, fy))
    total_exp = float(cursor.fetchone()["total_exp"] or 0)

    current_balance = total_allotment - total_exp


    if amount > current_balance:
        cursor.close()
        conn.close()
        return jsonify({
            "success": False,
            "message": "Expenditure exceeds available balance"
        })

    cursor.execute("""
        INSERT INTO expenditures (grant_id, amount, financial_year)
        VALUES (%s, %s, %s)
    """, (grant_id, amount, fy))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True})


# ==========================================
# EDIT GRANT DETAILS
# ==========================================
@accounts_bp.route("/grants/<int:grant_id>/edit", methods=["POST"])
def edit_grant(grant_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    code_head = (data.get("code_head") or "").strip()
    allotment = float(data.get("allotment") or 0)

    if not name or not code_head:
        return jsonify({"success": False, "message": "Name and Code Head are required"})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update grant row
        cursor.execute("""
            UPDATE grants
            SET name = %s, code_head = %s, allotment = %s
            WHERE id = %s
        """, (name, code_head, allotment, grant_id))

        # Update the 'Original' allotment entry in grant_allocations if it exists
        cursor.execute("""
            UPDATE grant_allocations
            SET amount = %s
            WHERE grant_id = %s AND allocation_type = 'Original'
        """, (allotment, grant_id))

        conn.commit()
        return jsonify({"success": True, "message": "Grant updated successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==========================================
# ADD SANCTION ORDER
# ==========================================
@accounts_bp.route("/grants/<int:grant_id>/add-so", methods=["POST"])
def add_so(grant_id):
    data = request.get_json() or {}
    so_number = (data.get("so_number") or "").strip()
    so_amount = float(data.get("so_amount") or 0)
    fy = request.args.get("fy") or get_financial_year()

    if not so_number or so_amount <= 0:
        return jsonify({"success": False, "message": "Valid SO Number and Amount required"})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO sanction_orders (grant_id, so_number, so_amount, financial_year, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (grant_id, so_number, so_amount, fy))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==========================================
# EDIT / DELETE SANCTION ORDER
# ==========================================
@accounts_bp.route("/so/<int:so_id>/edit", methods=["POST"])
def edit_so(so_id):
    data = request.get_json() or {}
    so_number = (data.get("so_number") or "").strip()
    so_amount = float(data.get("so_amount") or 0)

    if not so_number or so_amount <= 0:
        return jsonify({"success": False, "message": "Valid SO Number and Amount required"})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE sanction_orders
            SET so_number = %s, so_amount = %s
            WHERE id = %s
        """, (so_number, so_amount, so_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@accounts_bp.route("/so/<int:so_id>/delete", methods=["POST", "DELETE"])
def delete_so(so_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM sanction_orders WHERE id = %s", (so_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ==========================================
# EDIT / DELETE EXPENDITURE
# ==========================================
@accounts_bp.route("/exp/<int:exp_id>/edit", methods=["POST"])
def edit_expenditure(exp_id):
    data = request.get_json() or {}
    amount = float(data.get("amount") or 0)
    remarks = (data.get("remarks") or "").strip()

    if amount <= 0:
        return jsonify({"success": False, "message": "Amount must be greater than zero"})

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE expenditures
            SET amount = %s, remarks = %s
            WHERE id = %s
        """, (amount, remarks, exp_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@accounts_bp.route("/exp/<int:exp_id>/delete", methods=["POST", "DELETE"])
def delete_expenditure(exp_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM expenditures WHERE id = %s", (exp_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()


# ==========================================
# EDIT / DELETE ALLOCATION (ALLOTMENT)
# ==========================================
@accounts_bp.route("/allocation/<int:alloc_id>/edit", methods=["POST"])
def edit_allocation(alloc_id):
    data = request.get_json() or {}
    amount = float(data.get("amount") or 0)
    remarks = (data.get("remarks") or "").strip()

    if amount <= 0:
        return jsonify({"success": False, "message": "Amount must be greater than zero"})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT grant_id, allocation_type FROM grant_allocations WHERE id = %s", (alloc_id,))
        alloc = cursor.fetchone()
        if not alloc:
            return jsonify({"success": False, "message": "Allocation record not found"}), 404

        cursor.execute("""
            UPDATE grant_allocations
            SET amount = %s, remarks = %s
            WHERE id = %s
        """, (amount, remarks, alloc_id))

        if alloc['allocation_type'] == 'Original':
            cursor.execute("""
                UPDATE grants
                SET allotment = %s
                WHERE id = %s
            """, (amount, alloc['grant_id']))

        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@accounts_bp.route("/allocation/<int:alloc_id>/delete", methods=["POST", "DELETE"])
def delete_allocation(alloc_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM grant_allocations WHERE id = %s", (alloc_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
