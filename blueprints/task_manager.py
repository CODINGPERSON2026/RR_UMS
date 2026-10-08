from imports import *

task_bp = Blueprint('task',__name__,url_prefix='/task_manager')

@task_bp.route('/')
def home():
    return render_template('/task_manager/task.html')

@task_bp.route('/api/stats')
def get_task_stats():
    user = require_login()
    if not user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get task stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COALESCE(SUM(LOWER(task_status) = 'pending' OR task_status IS NULL), 0) as pending,
                COALESCE(SUM(LOWER(task_status) = 'in progress'), 0) as in_progress,
                COALESCE(SUM(LOWER(task_status) = 'completed'), 0) as completed
            FROM tasks
        """)
        stats = cursor.fetchone()
        
        # Get 5 most recent tasks
        cursor.execute("""
            SELECT 
                t.id,
                t.task_name,
                t.task_status,
                t.priority,
                t.due_date,
                p.name AS assigned_name
            FROM tasks t
            LEFT JOIN personnel p ON t.assigned_to = p.army_number
            ORDER BY t.id DESC
            LIMIT 5
        """)
        recent_tasks = cursor.fetchall()
        for task in recent_tasks:
            if task['due_date']:
                task['due_date'] = task['due_date'].strftime('%Y-%m-%d')
                
        return jsonify({
            "status": "success",
            "stats": stats,
            "recent_tasks": recent_tasks
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@task_bp.route('/create-task', methods=['POST'])
def update_task():
    data = request.get_json()
    task_name = data.get('task_name')
    description = data.get('description')
    priority = data.get('priority')
    assigned_to = data.get('assigned_to')
    due_date = data.get('due_date')
    user = require_login()
    admin = user['role']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
    INSERT INTO tasks (task_name, description, priority, assigned_to, assigned_by, due_date)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

        cursor.execute(query, (
    task_name,
    description,
    priority,
    assigned_to,
    admin,
    due_date
))


        conn.commit()

        return jsonify({"status": "success", "message": "Task updated successfully"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@task_bp.route("/view_task")
def view_task():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            t.id,
            t.task_name,
            t.task_status,
            t.assigned_to,
            p.name AS assigned_name
        FROM tasks t
        LEFT JOIN personnel p 
            ON t.assigned_to = p.army_number
        ORDER BY t.id DESC
    """)

    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(tasks)


@task_bp.route("/get_task/<int:id>")
def get_task_details(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            t.id,
            t.task_name,
            t.description,
            t.priority,
            t.assigned_to,
            t.assigned_by,
            t.due_date,
            t.task_status,
            t.remarks,
            t.range_status,
            t.remark_updated_at,
            p.name AS assigned_name,
            p.company AS assigned_company,
            p.rank AS assigned_rank
        FROM tasks t
        LEFT JOIN personnel p ON t.assigned_to = p.army_number
        WHERE t.id = %s
    """, (id,))
    task = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify(task)

@task_bp.route('/delete_task/<int:id>', methods=['DELETE'])
def delete_task(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = 'DELETE FROM tasks WHERE id = %s'
        cursor.execute(query, (id,))
        conn.commit()
        status = 200
        response = {'status': 'success', 'message': f'Task {id} deleted'}
    except Exception as e:
        conn.rollback()
        status = 500
        response = {'status': 'error', 'message': str(e)}
    finally:
        cursor.close()
        conn.close()
    return jsonify(response), status



@task_bp.route('/get_task_update/<int:task_id>')
def get_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
    task = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if task:
        # Format date as yyyy-mm-dd for input[type=date]
        task['due_date'] = task['due_date'].strftime('%Y-%m-%d') if task['due_date'] else ''
        return jsonify(task)
    else:
        return jsonify({"error": "Task not found"}), 404





# the below route is for updating the task
@task_bp.route('/update_task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    try:
        data = request.form  

        task_name = data.get("task_name")
        description = data.get("description")
        priority = data.get("priority")
        assigned_to = data.get("assigned_to")
        due_date = data.get("due_date")

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            UPDATE tasks
            SET task_name=%s, description=%s, priority=%s,
                assigned_to=%s, due_date=%s
            WHERE id=%s
        """

        cursor.execute(query, (task_name, description, priority, assigned_to, due_date, task_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Task updated successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to update task"}), 500
    



@task_bp.route('/get_my_tasks')
def get_my_tasks():
    user =require_login()
    current_user = user['army_number']  # assume username is stored in session
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, task_name, description, priority, due_date, task_status, remarks, range_status
        FROM tasks
        WHERE assigned_to = %s
        ORDER BY due_date ASC
    """, (current_user,))
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'tasks': tasks})



@task_bp.route('/update_task', methods=['POST'])
def jco_update_task():
    conn = None
    try:
        user = require_login()
        user_name = user.get('name', 'User')

        data = request.get_json()
        task_id = data.get('id')
        if not task_id:
            return jsonify({'error': 'Missing task id'}), 400
            
        task_status = data.get('task_status')
        new_remark = data.get('new_remark')
        range_status = data.get('range_status')

        conn = get_db_connection()
        # Create cursor with dictionary capability to easily fetch current remarks
        cursor = conn.cursor(dictionary=True)

        updates = []
        params = []
        
        if task_status is not None:
            updates.append("task_status = %s")
            params.append(task_status)
            
        if new_remark:
            # Fetch existing remarks
            cursor.execute("SELECT remarks FROM tasks WHERE id = %s", (task_id,))
            row = cursor.fetchone()
            current_remarks = row['remarks'] if row and row['remarks'] else ""
            
            import datetime
            timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            formatted_new_remark = f"[{timestamp}]: {new_remark}"
            
            if current_remarks:
                updated_remarks = f"{current_remarks}\n{formatted_new_remark}"
            else:
                updated_remarks = formatted_new_remark
                
            updates.append("remarks = %s")
            params.append(updated_remarks)
            updates.append("remark_updated_at = NOW()")
            
        if range_status is not None:
            updates.append("range_status = %s")
            params.append(int(range_status))
            
        # Support old single-field update format as fallback
        field = data.get('field')
        value = data.get('value')
        if field and value is not None:
            allowed_fields = {
                'task_status': 'task_status',
                'remarks': 'remarks',
                'range_status': 'range_status'
            }
            if field in allowed_fields:
                column = allowed_fields[field]
                if field == 'remarks':
                    # Fallback single field remarks append
                    cursor.execute("SELECT remarks FROM tasks WHERE id = %s", (task_id,))
                    row = cursor.fetchone()
                    current_remarks = row['remarks'] if row and row['remarks'] else ""
                    
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    formatted_new_remark = f"[{timestamp}]: {value}"
                    
                    if current_remarks:
                        value = f"{current_remarks}\n{formatted_new_remark}"
                    else:
                        value = formatted_new_remark
                    updates.append("remark_updated_at = NOW()")
                updates.append(f"{column} = %s")
                params.append(int(value) if field == 'range_status' else value)
            
        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'No changes to update'})
            
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s"
        params.append(task_id)
        
        # Convert cursor back to normal or just execute (dictionary cursor execute works fine)
        cursor.execute(query, tuple(params))
        conn.commit()
        
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Task updated successfully'})

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except:
                pass
            try:
                conn.close()
            except:
                pass
        return jsonify({'error': str(e)}), 500