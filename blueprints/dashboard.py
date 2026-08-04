from imports import *
from db_config  import get_db_connection
dashboard_bp =  Blueprint('dasboard',__name__,url_prefix='/stats')





@dashboard_bp.route("/get_all_dets", methods=["GET"])
def get_all_dets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT det_id, det_name FROM dets ORDER BY det_name")
        dets = cursor.fetchall()
        return jsonify({"status": "success", "data": dets})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()






@dashboard_bp.route('/get_detachment_details')
def get_detachment_details():
    det_id = request.args.get("det_id")  # optional
    min_days = request.args.get("min_days", 0, type=int) # optional filter
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get logged in user
    user = require_login()

    try:
        # Base query: only active det assignments (det_status=1)
        query = """
            SELECT 
                p.name, 
                p.army_number, 
                p.rank, 
                p.company, 
                d.det_name,
                DATEDIFF(CURDATE(), a.assigned_on) AS days_on_det
            FROM assigned_det a
            JOIN personnel p ON p.army_number = a.army_number
            JOIN dets d ON d.det_id = a.det_id
            WHERE a.det_status = 1 AND p.detachment_status = 1
        """
        params = []

        # Apply filter if det_id is provided
        if det_id:
            query += " AND a.det_id = %s"
            params.append(det_id)
            
        # Apply min_days filter
        if min_days > 0:
            query += " AND DATEDIFF(CURDATE(), a.assigned_on) > %s"
            params.append(min_days)

        # ---------- COMPANY FILTER (Admin bypass) ----------
        
        if user['company'] != "Admin" and user['company'] !='Center':
            query += " AND p.company = %s"
            params.append(user['company'])

        cursor.execute(query, params)
        data = cursor.fetchall()

        return jsonify({"status": "success", "data": data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
@dashboard_bp.route('/delete_personnel', methods=['POST'])
def delete_personnel():
    data = request.get_json()
    army_number = data.get('army_number')
    status= 0

    if not army_number:
        return jsonify({"status": "error", "message": "Missing army_number"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Start transaction
        conn.start_transaction()

        # Update personnel table
        cursor.execute("""
            UPDATE personnel
            SET detachment_status = 0
            WHERE army_number = %s
        """, (army_number,))

        # Update assigned_det table with det_removed_date
        cursor.execute("""
            UPDATE assigned_det
            SET det_removed_date = %s,
                        det_status = %s
            WHERE army_number = %s
        """, (datetime.now(),0,army_number))

        # Commit transaction
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": f"{army_number} removed from detachment"})

    except Exception as e:
        conn.rollback()  # rollback on error
        return jsonify({"status": "error", "message": "Database error"}), 500








@dashboard_bp.route("/attachment-details", methods=["GET"])
def attachment_details():
    user = require_login()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    # role = user.get("role")
    company = user.get("company")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if company == "Admin":
            cursor.execute("""
                SELECT
                    t.id,
                    t.company,
                    t.army_number,
                    p.rank,
                    p.name,
                    t.location,
                    t.authority,
                    t.td_date
                FROM td_table t
                LEFT JOIN personnel p
                    ON p.army_number = t.army_number
                ORDER BY t.td_date DESC
            """)
        else:
            cursor.execute("""
                SELECT
                    t.id,
                    t.company,
                    t.army_number,
                    p.rank,
                    p.name,
                    t.location,
                    t.authority,
                    t.td_date
                FROM td_table t
                LEFT JOIN personnel p
                    ON p.army_number = t.army_number
                WHERE t.company = %s
                ORDER BY t.td_date DESC
            """, (company,))

        rows = cursor.fetchall()
        # ✅ FORCE JSON SAFE DATE
        for r in rows:
            td = r.get("td_date")
            r["td_date"] = td.strftime("%d-%m-%Y") if td else ""

        return jsonify(rows), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()








@dashboard_bp.route("/assigned_attachment_alarm", methods=["GET"])
def assigned_attachment_alarm():
    user = require_login()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user['role'] != 'CO':
        return jsonify({"error": 'Forbidden'}), 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                t.id,
                t.army_number,
                COALESCE(p.rank, 'N/A') AS `rank`,
                COALESCE(p.name, 'N/A') AS `name`,
                COALESCE(t.company, p.company, 'N/A') AS company,
                COALESCE(t.location, 'N/A') AS location,
                COALESCE(t.authority, 'N/A') AS authority,
                t.td_date,
                DATEDIFF(NOW(), t.td_date) AS days_on_td,
                COALESCE(t.remarks, '') AS remarks
            FROM td_table t
            LEFT JOIN personnel p ON p.army_number = t.army_number
            WHERE t.td_date <= NOW() - INTERVAL 90 DAY
            ORDER BY t.td_date ASC
        """)

        rows = cursor.fetchall()
        for r in rows:
            if r['td_date']:
                r['td_date'] = str(r['td_date'])

        return jsonify({
            "count": len(rows),
            "rows": rows
        })

    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500

    finally:
        cursor.close()
        conn.close()



@dashboard_bp.route("/delete-attachment/<army_number>", methods=["DELETE"])
def delete_attachment(army_number):
    user = require_login()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    company = user["company"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Soft delete in personnel
        cursor.execute("""
            UPDATE personnel
            SET td_status = 0
            WHERE army_number = %s 
        """, (army_number, ))

        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "Personnel record not found"}), 404

        # Delete from td_table
        cursor.execute("""
            DELETE FROM td_table
            WHERE army_number = %s
        """, (army_number,))

        # Commit only if both queries succeed
        conn.commit()
        return jsonify({"message": "Attachment marked inactive and TD record deleted successfully"})

    except Exception as e:
        conn.rollback()  # Rollback both queries if any fails
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@dashboard_bp.route("/get_honours_board", methods=["GET"])
def get_honours_board():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                hb.army_number, 
                p.name, 
                p.rank, 
                p.company, 
                hb.medal_icon, 
                hb.commendation, 
                hb.appreciation_type, 
                hb.appreciation_date, 
                hb.image
            FROM honours_board hb
            JOIN personnel p ON hb.army_number = p.army_number
            ORDER BY hb.appreciation_date DESC
        """
        cursor.execute(query)
        data = cursor.fetchall()
        
        # Format date for JSON response
        for row in data:
            if row['appreciation_date']:
                row['appreciation_date'] = row['appreciation_date'].strftime("%d-%m-%Y")
                
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

