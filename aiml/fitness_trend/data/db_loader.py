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


def fetch_personnel_list_for_search(query_str="", limit=50):
    """
    Fetch a list of personnel for autocomplete and selection in the UI.
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        if query_str:
            search_param = f"%{query_str.strip()}%"
            query = """
                SELECT p.army_number, p.name, p.rank, p.company, p.trade,
                       w.status_type, w.actual_weight, w.height, w.age
                FROM personnel p
                LEFT JOIN weight_info w ON p.army_number = w.army_number
                WHERE p.army_number LIKE %s OR p.name LIKE %s OR p.company LIKE %s
                ORDER BY p.name ASC
                LIMIT %s
            """
            cursor.execute(query, (search_param, search_param, search_param, limit))
        else:
            query = """
                SELECT p.army_number, p.name, p.rank, p.company, p.trade,
                       w.status_type, w.actual_weight, w.height, w.age
                FROM personnel p
                LEFT JOIN weight_info w ON p.army_number = w.army_number
                ORDER BY p.name ASC
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
    Fetch complete fitness-related records for a single soldier across all 4 tables.
    Returns:
        dict: {
            'personnel': dict,
            'weight_info': dict,
            'sports': list of dicts,
            'ideal_weights': list of dicts
        } or None if personnel not found.
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
        
        # 1. Fetch personnel record
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
            return None
        
        # 2. Fetch weight_info record
        query_w = """
            SELECT troop_id, name, `rank`, army_number, actual_weight, age, height,
                   company, status_type, category_type, restrictions
            FROM weight_info
            WHERE army_number = %s
            LIMIT 1
        """
        cursor.execute(query_w, (army_num,))
        weight_row = cursor.fetchone()
        
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
    Returns:
        tuple: (list of personnel dicts, list of weight_info dicts, list of sports dicts, list of ideal_weights)
    """
    conn = get_db_connection()
    if not conn:
        logger.error("DB Connection failed in fetch_all_personnel_fitness_data")
        return [], [], [], []
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Personnel
        cursor.execute("""
            SELECT id, name, army_number, `rank`, trade, date_of_enrollment, date_of_birth,
                   bpet_grading, ppt_grading, bpet_date, participation_activities,
                   height, weight, med_cat, medical_problem, restrictions,
                   company, section
            FROM personnel
        """)
        personnel_rows = cursor.fetchall()
        
        # Weight info
        cursor.execute("""
            SELECT troop_id, name, `rank`, army_number, actual_weight, age, height,
                   company, status_type, category_type, restrictions
            FROM weight_info
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
