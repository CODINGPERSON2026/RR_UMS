from imports import *
from datetime import datetime

sensitive_bp = Blueprint('sensitive_bp', __name__, url_prefix='/sensitive')

# Only OC, CO, ADJUTANT, 2IC (and Admin) have rights to view or mark sensitive personnel
ALLOWED_SENSITIVE_ROLES = {'CO', '2IC', 'ADJUTANT', 'OC', 'Admin', 'admin'}

def check_sensitive_auth(user, is_json=True):
    if not user:
        if is_json:
            return jsonify({"success": False, "error": "Unauthorized. Please log in first."}), 401
        return redirect(url_for('admin_login'))
    if user.get("role") not in ALLOWED_SENSITIVE_ROLES:
        if is_json:
            return jsonify({"success": False, "error": "Access Denied: Only OC, CO, Adjutant, and 2IC can access Sensitive Personnel."}), 403
        return "Access Denied: Only OC, CO, Adjutant, and 2IC can access Sensitive Personnel.", 403
    return None

@sensitive_bp.route("/remove_sensitive", methods=["POST"])
def remove_sensitive():
    user = require_login()
    auth_err = check_sensitive_auth(user, is_json=True)
    if auth_err:
        return auth_err

    army_number = request.form.get("army_number")
    if not army_number:
        return jsonify({"success": False, "error": "Missing army number"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sensitive_marking WHERE army_number = %s", (army_number,))
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "Personnel not found in sensitive list"}), 404
        
        conn.commit()
        return jsonify({"success": True, "message": "Personnel removed from sensitive list."})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": "Remove failed"}), 500
    finally:
        cursor.close()
        conn.close()


@sensitive_bp.route("/mark_sensitive", methods=["POST"])
def mark_sensitive():
    user = require_login()
    auth_err = check_sensitive_auth(user, is_json=True)
    if auth_err:
        return auth_err

    army_number = request.form.get("army_number")
    reason = request.form.get("reason")

    if not army_number or not reason:
        return jsonify({"success": False, "error": "Missing army number or reason"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert into sensitive_marking if not already there
        cursor.execute("SELECT 1 FROM sensitive_marking WHERE army_number = %s", (army_number,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO sensitive_marking (army_number, marked_on)
                VALUES (%s, %s)
            """, (army_number, datetime.now()))

        # Always log the reason with user info
        cursor.execute("""
            INSERT INTO sensitive_reason_log (army_number, reason, added_by, added_by_role, added_on)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            army_number,
            reason.strip(),
            user.get('username', 'Unknown'),
            user.get('role', 'Unknown'),
            datetime.now()
        ))

        conn.commit()
        return jsonify({"success": True, "message": "Personnel marked as sensitive successfully."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()


@sensitive_bp.route("/update_sensitive_reason", methods=["POST"])
def update_sensitive_reason():
    user = require_login()
    auth_err = check_sensitive_auth(user, is_json=True)
    if auth_err:
        return auth_err

    army_number = request.form.get("army_number")
    reason = request.form.get("reason")

    if not army_number or not reason:
        return jsonify({"success": False, "error": "Missing data"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM sensitive_marking WHERE army_number = %s", (army_number,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Personnel not found in sensitive list"}), 404

        cursor.execute("""
            INSERT INTO sensitive_reason_log (army_number, reason, added_by, added_by_role, added_on)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            army_number,
            reason.strip(),
            user.get('username', 'Unknown'),
            user.get('role', 'Unknown'),
            datetime.now()
        ))

        conn.commit()
        return jsonify({"success": True, "message": "Reason added successfully."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": "Update failed"}), 500
    finally:
        cursor.close()
        conn.close()


@sensitive_bp.route("/get_sensitive_list")
def get_sensitive_list():
    user = require_login()
    auth_err = check_sensitive_auth(user, is_json=True)
    if auth_err:
        return auth_err

    user_company = user.get("company")
    user_role = user.get("role")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if user_company == "Admin" or user_role in ["Admin", "admin", "CO", "2IC", "ADJUTANT"]:
            cursor.execute("""
                SELECT s.army_number, s.marked_on,
                       p.name, p.rank, p.company
                FROM sensitive_marking s
                JOIN personnel p ON s.army_number = p.army_number
                ORDER BY s.marked_on DESC
            """)
        else:
            cursor.execute("""
                SELECT s.army_number, s.marked_on,
                       p.name, p.rank, p.company
                FROM sensitive_marking s
                JOIN personnel p ON s.army_number = p.army_number
                WHERE LOWER(p.company) = LOWER(%s)
                ORDER BY s.marked_on DESC
            """, (user_company,))

        rows = cursor.fetchall()

        now = datetime.now()
        result = []
        alarm_count = 0
        recent_30_count = 0

        for r in rows:
            army_number = r[0]
            marked_on_dt = r[1]

            cursor.execute("""
                SELECT reason, added_by, added_by_role, added_on
                FROM sensitive_reason_log
                WHERE army_number = %s
                ORDER BY added_on ASC
            """, (army_number,))
            logs = cursor.fetchall()

            # Determine latest remark or marking date
            latest_date = marked_on_dt
            if logs and logs[-1][3]:
                latest_date = logs[-1][3]

            days_since = (now - latest_date).days if latest_date else 0
            months_since = round(days_since / 30.0, 1)
            is_alarm = days_since >= 90  # 3 months (90 days) threshold

            if is_alarm:
                alarm_count += 1
            if days_since <= 30:
                recent_30_count += 1

            reason_logs = [{
                "reason": l[0],
                "added_by": l[1],
                "added_by_role": l[2],
                "added_on": l[3].strftime("%d %b %Y, %H:%M") if l[3] else ""
            } for l in logs]

            result.append({
                "army_number": army_number,
                "marked_on": marked_on_dt.strftime("%Y-%m-%d %H:%M:%S") if marked_on_dt else "",
                "name": r[2],
                "rank": r[3],
                "company": r[4] or "N/A",
                "reason_logs": reason_logs,
                "last_remark_date": latest_date.strftime("%d %b %Y, %H:%M") if latest_date else "",
                "days_since_last_remark": days_since,
                "months_since_last_remark": months_since,
                "is_alarm": is_alarm
            })

        total_count = len(result)
        up_to_date_count = total_count - alarm_count

        return jsonify({
            "success": True,
            "data": result,
            "metrics": {
                "total_count": total_count,
                "alarm_count": alarm_count,
                "recent_30_count": recent_30_count,
                "up_to_date_count": up_to_date_count
            }
        })

    finally:
        cursor.close()
        conn.close()


@sensitive_bp.route("/mark_personnel", methods=["GET"])
def mark_personnel():
    user = require_login()
    auth_err = check_sensitive_auth(user, is_json=False)
    if auth_err:
        return auth_err

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.army_number, s.marked_on,
               p.name, p.rank, p.company
        FROM sensitive_marking s
        JOIN personnel p ON s.army_number = p.army_number
        ORDER BY s.marked_on DESC
    """)
    rows = cursor.fetchall()

    sensitive_list = []
    for r in rows:
        sensitive_list.append({
            "army_number": r[0],
            "marked_on": r[1].strftime("%Y-%m-%d %H:%M:%S") if r[1] else "",
            "name": r[2],
            "rank": r[3],
            "company": r[4] or "N/A"
        })

    cursor.close()
    conn.close()

    response = make_response(render_template(
        "sensitive_indl/mark_personnel.html",
        sensitive_list=sensitive_list,
        current_user=user
    ))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response
