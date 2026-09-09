"""
Database Loader for AI/ML Fitness Trend.
Uses parameterized queries to safely and efficiently fetch data from MySQL.
"""

import sys
import os
import logging
import mysql.connector
from mysql.connector import Error

# Configure module logger
logger = logging.getLogger("fitness_trend.db_loader")

# Import database connection from root UMS db_config
try:
    from db_config import get_db_connection
except ImportError:
    # Fallback if imported from a standalone subpackage
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from db_config import get_db_connection


def fetch_ideal_weights_table():
    """
    Fetch the complete ideal weights reference table.
    Returns:
        list of dicts containing id, height_cm, age_range, ideal_weight_kg
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Database connection failed when fetching ideal weights.")
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, height_cm, age_range, ideal_weight_kg FROM ideal_weights ORDER BY height_cm, age_range"
        cursor.execute(query)
        rows = cursor.fetchall()
        # Convert Decimal values to float
        for r in rows:
            if r.get('ideal_weight_kg') is not None:
                r['ideal_weight_kg'] = float(r['ideal_weight_kg'])
        return rows
    except Error as e:
        logger.error(f"Error fetching ideal weights: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def fetch_total_weight_info_count():
    """
    Returns total count of personnel records available in weight_info table.
    """
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT COUNT(*) AS total_count FROM weight_info WHERE army_number IS NOT NULL AND army_number != ''"
        cursor.execute(query)
        row = cursor.fetchone()
        if row and row.get('total_count') is not None:
            return int(row['total_count'])
        return 0
    except Error as e:
        logger.error(f"Error counting weight_info records: {e}")
        return 0
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def fetch_personnel_list_for_search(query_str="", limit=50):
    """
    Fetch a list of personnel for autocomplete and selection in the UI.
    Only personnel available in weight_info table are returned.
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        if query_str:
            q_clean = query_str.strip()
            search_param = f"%{q_clean}%"
            search_param_nospace = f"%{q_clean.replace(' ', '')}%"
            query = """
                SELECT w.army_number,
                       COALESCE(NULLIF(w.name, ''), p.name, 'Soldier') AS name,
                       COALESCE(NULLIF(w.`rank`, ''), p.`rank`, 'Soldier') AS `rank`,
                       COALESCE(NULLIF(w.company, ''), p.company, 'Unit HQ') AS company,
                       p.trade,
                       w.status_type, w.actual_weight, w.height, w.age
                FROM weight_info w
                LEFT JOIN personnel p ON TRIM(w.army_number) = TRIM(p.army_number)
                WHERE w.army_number IS NOT NULL AND w.army_number != ''
                  AND (
                    w.army_number LIKE %s OR REPLACE(w.army_number, ' ', '') LIKE %s
                    OR p.army_number LIKE %s OR REPLACE(p.army_number, ' ', '') LIKE %s
                    OR w.name LIKE %s OR p.name LIKE %s
                    OR w.company LIKE %s OR p.company LIKE %s
                  )
                ORDER BY COALESCE(NULLIF(w.name, ''), p.name) ASC
                LIMIT %s
            """
            cursor.execute(query, (
                search_param, search_param_nospace,
                search_param, search_param_nospace,
                search_param, search_param,
                search_param, search_param,
                limit
            ))
        else:
            query = """
                SELECT w.army_number,
                       COALESCE(NULLIF(w.name, ''), p.name, 'Soldier') AS name,
                       COALESCE(NULLIF(w.`rank`, ''), p.`rank`, 'Soldier') AS `rank`,
                       COALESCE(NULLIF(w.company, ''), p.company, 'Unit HQ') AS company,
                       p.trade,
                       w.status_type, w.actual_weight, w.height, w.age
                FROM weight_info w
                LEFT JOIN personnel p ON TRIM(w.army_number) = TRIM(p.army_number)
                WHERE w.army_number IS NOT NULL AND w.army_number != ''
                ORDER BY COALESCE(NULLIF(w.name, ''), p.name) ASC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
        return cursor.fetchall()
    except Error as e:
        logger.error(f"Error fetching personnel search list: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def fetch_single_personnel_data(army_number):
    """
    Fetch complete fitness-related records for a single soldier across all tables.
    Only personnel available in weight_info table are processed.
    Returns:
        dict: {
            'personnel': dict,
            'weight_info': dict,
            'sports': list of dicts,
            'ideal_weights': list of dicts
        } or None if personnel not found in weight_info table.
    """
    if not army_number or not isinstance(army_number, str):
        return None
    
    army_num = army_number.strip()
    conn = get_db_connection()
    if not conn:
        logger.error(f"Failed to connect to DB for soldier: {army_num}")
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Fetch weight_info record (mandatory requirement: personnel must be in weight_info table)
        query_w = """
            SELECT troop_id, name, `rank`, army_number, actual_weight, age, height,
                   company, status_type, category_type, restrictions
            FROM weight_info
            WHERE army_number = %s
            LIMIT 1
        """
        cursor.execute(query_w, (army_num,))
        weight_row = cursor.fetchone()
        
        if not weight_row:
            # Soldier is not available in weight_info table
            return None

        # 2. Fetch personnel record
        query_p = """
            SELECT id, name, army_number, `rank`, trade, date_of_enrollment, date_of_birth,
                   bpet_grading, ppt_grading, bpet_date, participation_activities,
                   height, weight, med_cat, medical_problem, restrictions,
                   company, section
            FROM personnel
            WHERE army_number = %s
            LIMIT 1
        """
        cursor.execute(query_p, (army_num,))
        personnel_row = cursor.fetchone()
        
        if not personnel_row:
            personnel_row = {
                'id': None,
                'name': weight_row.get('name', 'Soldier'),
                'army_number': weight_row.get('army_number', army_num),
                'rank': weight_row.get('rank', 'Soldier'),
                'trade': 'GD',
                'date_of_enrollment': None,
                'date_of_birth': None,
                'bpet_grading': None,
                'ppt_grading': None,
                'bpet_date': None,
                'participation_activities': None,
                'height': weight_row.get('height'),
                'weight': weight_row.get('actual_weight'),
                'med_cat': 'SHAPE-1' if weight_row.get('status_type') == 'shape' else 'LMC',
                'medical_problem': weight_row.get('category_type'),
                'restrictions': weight_row.get('restrictions'),
                'company': weight_row.get('company', 'Unit HQ'),
                'section': None
            }
        
        # 3. Fetch sports records
        query_s = """
            SELECT id, personnel_id, army_number, sport_type, sport_name, created_at
            FROM personnel_sports
            WHERE army_number = %s
            ORDER BY id ASC
        """
        cursor.execute(query_s, (army_num,))
        sports_rows = cursor.fetchall()
        
        # 4. Fetch ideal weights reference
        ideal_weights = fetch_ideal_weights_table()
        
        return {
            'personnel': personnel_row,
            'weight_info': weight_row,
            'sports': sports_rows,
            'ideal_weights': ideal_weights
        }
    except Error as e:
        logger.error(f"Database error fetching soldier {army_num}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def fetch_all_personnel_fitness_data():
    """
    Fetch all joined fitness data for model training and dataset extraction.
    Only personnel with weight_info records are included.
    Returns:
        tuple: (list of personnel dicts, list of weight_info dicts, list of sports dicts, list of ideal_weights)
    """
    conn = get_db_connection()
    if not conn:
        logger.error("DB Connection failed in fetch_all_personnel_fitness_data")
        return [], [], [], []
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Personnel filtered to those present in weight_info
        cursor.execute("""
            SELECT id, name, army_number, `rank`, trade, date_of_enrollment, date_of_birth,
                   bpet_grading, ppt_grading, bpet_date, participation_activities,
                   height, weight, med_cat, medical_problem, restrictions,
                   company, section
            FROM personnel
            WHERE army_number IN (SELECT DISTINCT army_number FROM weight_info WHERE army_number IS NOT NULL AND army_number != '')
        """)
        personnel_rows = cursor.fetchall()
        
        # Weight info
        cursor.execute("""
            SELECT troop_id, name, `rank`, army_number, actual_weight, age, height,
                   company, status_type, category_type, restrictions
            FROM weight_info
            WHERE army_number IS NOT NULL AND army_number != ''
        """)
        weight_rows = cursor.fetchall()
        
        # Sports
        cursor.execute("""
            SELECT id, personnel_id, army_number, sport_type, sport_name, created_at
            FROM personnel_sports
        """)
        sports_rows = cursor.fetchall()
        
        ideal_weights = fetch_ideal_weights_table()
        
        return personnel_rows, weight_rows, sports_rows, ideal_weights
    except Error as e:
        logger.error(f"Error fetching all fitness data: {e}")
        return [], [], [], []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
