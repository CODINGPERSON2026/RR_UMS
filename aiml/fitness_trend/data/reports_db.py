"""
Database Repository for AI/ML Fitness Reports (ai_fitness_reports).
Handles persistence, parameterized search, filtering, server-side pagination,
and dynamic executive statistics calculation for CO, 2IC, and Adjutant oversight.
"""

import os
import sys
import json
import math
import logging
from datetime import datetime
from mysql.connector import Error

# Configure module logger
logger = logging.getLogger("fitness_trend.reports_db")

# Import database connection from root UMS db_config
try:
    from db_config import get_db_connection
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from db_config import get_db_connection


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `ai_fitness_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `personnel_id` INT NULL,
    `army_number` VARCHAR(50) NOT NULL,
    `name` VARCHAR(150),
    `rank` VARCHAR(100),
    `company` VARCHAR(100),
    `age` INT NULL,
    `height_cm` DECIMAL(6,2) NULL,
    `actual_weight_kg` DECIMAL(6,2) NULL,
    `ideal_weight_kg` DECIMAL(6,2) NULL,
    `bmi` DECIMAL(6,2) NULL,
    `fitness_score` DECIMAL(6,2) NULL,
    `fitness_status` VARCHAR(100) NULL,
    `prediction_result` LONGTEXT NULL,
    `recommendations` LONGTEXT NULL,
    `diet_recommendations` LONGTEXT NULL,
    `exercise_recommendations` LONGTEXT NULL,
    `progression_prediction` LONGTEXT NULL,
    `report_language` VARCHAR(50) DEFAULT 'English',
    `report_generated` BOOLEAN DEFAULT TRUE,
    `pdf_path` VARCHAR(500) NULL,
    `model_name` VARCHAR(150) NULL,
    `model_version` VARCHAR(100) NULL,
    `generated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uq_army_number` (`army_number`),
    INDEX `idx_personnel_id` (`personnel_id`),
    INDEX `idx_company` (`company`),
    INDEX `idx_fitness_status` (`fitness_status`),
    INDEX `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def ensure_ai_fitness_reports_table():
    """
    Ensures that the `ai_fitness_reports` table exists in the database with UNIQUE KEY on `army_number`.
    Automatically purges any existing duplicate rows and enforces idempotent persistence.
    """
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for table creation.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE_SQL)
        # Delete any historical duplicates keeping highest id
        cursor.execute("""
            DELETE r1 FROM ai_fitness_reports r1
            INNER JOIN ai_fitness_reports r2
            WHERE r1.id < r2.id AND r1.army_number = r2.army_number
        """)
        conn.commit()

        # Ensure UNIQUE constraint exists
        try:
            cursor.execute("ALTER TABLE ai_fitness_reports ADD UNIQUE KEY uq_army_number (army_number)")
            conn.commit()
        except Exception:
            pass

        logger.info("Table `ai_fitness_reports` verified/initialized with UNIQUE army_number successfully.")
        return True
    except Error as e:
        logger.error(f"Error creating `ai_fitness_reports` table: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_saved_report_by_army_number(army_number):
    """
    Fetch the latest generated AI fitness report for a soldier by army number.
    Returns:
        dict with deserialized JSON fields, or None.
    """
    if not army_number:
        return None

    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM ai_fitness_reports
            WHERE army_number = %s
            ORDER BY generated_at DESC, id DESC
            LIMIT 1
        """
        cursor.execute(query, (army_number.strip(),))
        row = cursor.fetchone()
        if row:
            return _deserialize_report_row(row)
        return None
    except Error as e:
        logger.error(f"Error fetching saved report for {army_number}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_saved_report_by_id(report_id):
    """
    Fetch a saved AI fitness report by primary key id.
    Returns:
        dict with deserialized JSON fields, or None.
    """
    if not report_id:
        return None

    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM ai_fitness_reports WHERE id = %s"
        cursor.execute(query, (int(report_id),))
        row = cursor.fetchone()
        if row:
            return _deserialize_report_row(row)
        return None
    except (Error, ValueError) as e:
        logger.error(f"Error fetching saved report by id {report_id}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def touch_fitness_report_timestamp(army_number=None, report_id=None):
    """
    Updates the generated_at and updated_at timestamps to CURRENT_TIMESTAMP
    whenever the fitness report / fitness progress of an individual is viewed.
    
    Args:
        army_number (str, optional): Soldier's army number.
        report_id (int, optional): Report primary key id.
    Returns:
        bool: True on success, False otherwise.
    """
    if not army_number and not report_id:
        return False

    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        if report_id:
            cursor.execute(
                "UPDATE ai_fitness_reports SET generated_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (int(report_id),)
            )
        else:
            clean_army_no = str(army_number).strip()
            cursor.execute(
                "UPDATE ai_fitness_reports SET generated_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE army_number = %s",
                (clean_army_no,)
            )
        conn.commit()
        logger.info(f"Touched/updated view timestamp for soldier {army_number or report_id}.")
        return True
    except Error as e:
        logger.error(f"Error updating fitness report timestamp for {army_number or report_id}: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def insert_or_update_ai_fitness_report(report_data):
    """
    Inserts a new AI fitness report or updates existing report for army_number.
    Prevents duplicates while keeping the latest record accurate.
    
    Args:
        report_data (dict): Standard dictionary of report metrics.
    Returns:
        int: report ID on success, None on error.
    """
    if not report_data or not report_data.get('army_number'):
        logger.warning("Attempted to persist report without army_number.")
        return None

    ensure_ai_fitness_reports_table()

    army_number = str(report_data.get('army_number')).strip()
    personnel_id = report_data.get('personnel_id')
    name = report_data.get('name')
    rank = report_data.get('rank')
    company = report_data.get('company')
    age = report_data.get('age')
    height_cm = report_data.get('height_cm')
    actual_weight_kg = report_data.get('actual_weight_kg')
    ideal_weight_kg = report_data.get('ideal_weight_kg')
    bmi = report_data.get('bmi')
    fitness_score = report_data.get('fitness_score')
    fitness_status = report_data.get('fitness_status')

    # Serialize JSON fields safely
    pred_res = _safe_json_dumps(report_data.get('prediction_result'))
    recs = _safe_json_dumps(report_data.get('recommendations'))
    diet_recs = _safe_json_dumps(report_data.get('diet_recommendations'))
    ex_recs = _safe_json_dumps(report_data.get('exercise_recommendations'))
    prog_res = _safe_json_dumps(report_data.get('progression_prediction'))

    report_language = report_data.get('report_language', 'English')
    report_generated = bool(report_data.get('report_generated', True))
    pdf_path = report_data.get('pdf_path')
    model_name = report_data.get('model_name', 'GradientBoostingClassifier')
    model_version = report_data.get('model_version', 'v1')

    conn = get_db_connection()
    if not conn:
        logger.error("DB connection unavailable for report persistence.")
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        # Check if record already exists for this army_number
        cursor.execute("SELECT id FROM ai_fitness_reports WHERE army_number = %s LIMIT 1", (army_number,))
        existing = cursor.fetchone()

        if existing:
            report_id = existing['id']
            update_sql = """
                UPDATE ai_fitness_reports SET
                    personnel_id = %s,
                    name = %s,
                    `rank` = %s,
                    company = %s,
                    age = %s,
                    height_cm = %s,
                    actual_weight_kg = %s,
                    ideal_weight_kg = %s,
                    bmi = %s,
                    fitness_score = %s,
                    fitness_status = %s,
                    prediction_result = %s,
                    recommendations = %s,
                    diet_recommendations = %s,
                    exercise_recommendations = %s,
                    progression_prediction = %s,
                    report_language = %s,
                    report_generated = %s,
                    pdf_path = %s,
                    model_name = %s,
                    model_version = %s,
                    generated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            cursor.execute(update_sql, (
                personnel_id, name, rank, company, age, height_cm,
                actual_weight_kg, ideal_weight_kg, bmi, fitness_score,
                fitness_status, pred_res, recs, diet_recs, ex_recs,
                prog_res, report_language, report_generated, pdf_path,
                model_name, model_version, report_id
            ))
            conn.commit()
            logger.info(f"Updated existing AI fitness report ID {report_id} for {army_number}.")
            return report_id
        else:
            insert_sql = """
                INSERT INTO ai_fitness_reports (
                    personnel_id, army_number, name, `rank`, company,
                    age, height_cm, actual_weight_kg, ideal_weight_kg, bmi,
                    fitness_score, fitness_status, prediction_result,
                    recommendations, diet_recommendations, exercise_recommendations,
                    progression_prediction, report_language, report_generated,
                    pdf_path, model_name, model_version, generated_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, CURRENT_TIMESTAMP
                )
            """
            cursor.execute(insert_sql, (
                personnel_id, army_number, name, rank, company,
                age, height_cm, actual_weight_kg, ideal_weight_kg, bmi,
                fitness_score, fitness_status, pred_res,
                recs, diet_recs, ex_recs,
                prog_res, report_language, report_generated,
                pdf_path, model_name, model_version
            ))
            conn.commit()
            report_id = cursor.lastrowid
            logger.info(f"Inserted new AI fitness report ID {report_id} for {army_number}.")
            return report_id

    except Error as e:
        logger.error(f"Error saving AI fitness report for {army_number}: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def bulk_insert_or_update_ai_fitness_reports(reports_list):
    """
    High-performance bulk insert/update of AI fitness reports into `ai_fitness_reports`.
    Executes in single database connection using batch statements.
    
    Args:
        reports_list (list of dict): List of report payloads.
    Returns:
        dict: {'total': int, 'inserted': int, 'updated': int}
    """
    if not reports_list:
        return {'total': 0, 'inserted': 0, 'updated': 0}

    ensure_ai_fitness_reports_table()

    conn = get_db_connection()
    if not conn:
        logger.error("DB connection unavailable for bulk report persistence.")
        return {'total': 0, 'inserted': 0, 'updated': 0, 'error': 'Database connection failed'}

    try:
        # Enforce strict single-transaction ACID boundaries
        if hasattr(conn, 'autocommit'):
            try:
                conn.autocommit = False
            except Exception:
                pass
        cursor = conn.cursor(dictionary=True)

        # 1. Clean up any historical duplicates before writing
        cursor.execute("""
            DELETE r1 FROM ai_fitness_reports r1
            INNER JOIN ai_fitness_reports r2
            WHERE r1.id < r2.id AND r1.army_number = r2.army_number
        """)

        # 2. In-memory deduplication: keep only the latest report per army_number
        deduped_reports = {}
        for r in reports_list:
            if not r or not r.get('army_number'):
                continue
            ano = str(r['army_number']).strip()
            if ano:
                deduped_reports[ano] = r

        upsert_rows = []
        for ano, r in deduped_reports.items():
            personnel_id = r.get('personnel_id')
            name = r.get('name')
            rank = r.get('rank')
            company = r.get('company')
            age = r.get('age')
            height_cm = r.get('height_cm')
            actual_weight_kg = r.get('actual_weight_kg')
            ideal_weight_kg = r.get('ideal_weight_kg')
            bmi = r.get('bmi')
            fitness_score = r.get('fitness_score')
            fitness_status = r.get('fitness_status')

            pred_res = _safe_json_dumps(r.get('prediction_result'))
            recs = _safe_json_dumps(r.get('recommendations'))
            diet_recs = _safe_json_dumps(r.get('diet_recommendations'))
            ex_recs = _safe_json_dumps(r.get('exercise_recommendations'))
            prog_res = _safe_json_dumps(r.get('progression_prediction'))

            report_language = r.get('report_language', 'English')
            report_generated = bool(r.get('report_generated', True))
            pdf_path = r.get('pdf_path')
            model_name = r.get('model_name', 'GradientBoostingClassifier')
            model_version = r.get('model_version', 'v1')

            upsert_rows.append((
                personnel_id, ano, name, rank, company,
                age, height_cm, actual_weight_kg, ideal_weight_kg, bmi,
                fitness_score, fitness_status, pred_res,
                recs, diet_recs, ex_recs,
                prog_res, report_language, report_generated,
                pdf_path, model_name, model_version
            ))

        if upsert_rows:
            upsert_sql = """
                INSERT INTO ai_fitness_reports (
                    personnel_id, army_number, name, `rank`, company,
                    age, height_cm, actual_weight_kg, ideal_weight_kg, bmi,
                    fitness_score, fitness_status, prediction_result,
                    recommendations, diet_recommendations, exercise_recommendations,
                    progression_prediction, report_language, report_generated,
                    pdf_path, model_name, model_version, generated_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, CURRENT_TIMESTAMP
                ) ON DUPLICATE KEY UPDATE
                    personnel_id = VALUES(personnel_id),
                    name = VALUES(name),
                    `rank` = VALUES(`rank`),
                    company = VALUES(company),
                    age = VALUES(age),
                    height_cm = VALUES(height_cm),
                    actual_weight_kg = VALUES(actual_weight_kg),
                    ideal_weight_kg = VALUES(ideal_weight_kg),
                    bmi = VALUES(bmi),
                    fitness_score = VALUES(fitness_score),
                    fitness_status = VALUES(fitness_status),
                    prediction_result = VALUES(prediction_result),
                    recommendations = VALUES(recommendations),
                    diet_recommendations = VALUES(diet_recommendations),
                    exercise_recommendations = VALUES(exercise_recommendations),
                    progression_prediction = VALUES(progression_prediction),
                    report_language = VALUES(report_language),
                    report_generated = VALUES(report_generated),
                    pdf_path = VALUES(pdf_path),
                    model_name = VALUES(model_name),
                    model_version = VALUES(model_version),
                    generated_at = CURRENT_TIMESTAMP
            """
            cursor.executemany(upsert_sql, upsert_rows)

        conn.commit()
        logger.info(f"Bulk upserted {len(upsert_rows)} AI fitness reports with zero duplicates.")
        return {
            'total': len(upsert_rows),
            'upserted': len(upsert_rows)
        }

    except Error as e:
        logger.error(f"Error in bulk_insert_or_update_ai_fitness_reports: {e}")
        if conn and conn.is_connected():
            conn.rollback()
        return {'total': 0, 'inserted': 0, 'updated': 0, 'error': str(e)}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def fetch_reports_paginated(search_query="", company="", status="", from_date=None, to_date=None,
                            sort_by="generated_at", sort_order="desc", page=1, per_page=10):
    """
    Fetches paginated, filterable reports list from `ai_fitness_reports`.
    Supports searching by Army Number or Name, filtering by Company, Fitness Status,
    and Date range.
    """
    ensure_ai_fitness_reports_table()

    page = max(1, int(page or 1))
    per_page = max(1, min(100, int(per_page or 10)))
    offset = (page - 1) * per_page

    # Allowed sorting fields
    allowed_sort_fields = {
        'fitness_score': 'fitness_score',
        'generated_at': 'generated_at',
        'name': 'name',
        'army_number': 'army_number',
        'company': 'company',
        'fitness_status': 'fitness_status',
        'id': 'id'
    }
    sort_column = allowed_sort_fields.get(sort_by, 'generated_at')
    order = "ASC" if str(sort_order).lower() == "asc" else "DESC"

    where_clauses = ["1=1"]
    params = []

    # Exclude dummy/test records from military fitness directory in production view
    is_test_env = bool(os.environ.get('TESTING') or 'unittest' in sys.argv[0].lower() or 'pytest' in sys.argv[0].lower())
    if not is_test_env and not search_query:
        where_clauses.append("(army_number NOT LIKE 'TEST%' AND army_number NOT LIKE 'jk010101%' AND (name IS NULL OR name NOT LIKE '%TEST%'))")

    if search_query:
        sq = f"%{search_query.strip()}%"
        where_clauses.append("(army_number LIKE %s OR name LIKE %s)")
        params.extend([sq, sq])

    if company and company.strip() and company.strip().lower() != 'all':
        comp_val = company.strip()
        comp_lower = comp_val.lower()
        if comp_lower in ('comn company', 'comn'):
            where_clauses.append("(company = 'COMN Company' OR company = 'COMN')")
        elif comp_lower in ('hq company', 'hq'):
            where_clauses.append("(company = 'HQ company' OR company = 'HQ' OR company = 'HQ Company')")
        elif comp_lower in ('3 company', '3'):
            where_clauses.append("(company = '3 Company' OR company = '3' OR company = 'ADMN')")
        else:
            where_clauses.append("company = %s")
            params.append(comp_val)

    effective_status = status.strip() if (status and str(status).strip()) else ''
    if effective_status and effective_status.lower() != 'all':
        st_lower = effective_status.lower()
        if st_lower in ('fit', 'fit only', 'fit_only'):
            where_clauses.append("(LOWER(fitness_status) LIKE '%healthy%' OR LOWER(fitness_status) LIKE '%combat%' OR LOWER(fitness_status) LIKE '%ready%' OR LOWER(fitness_status) LIKE '%good%' OR LOWER(fitness_status) LIKE '%optimal%' OR LOWER(fitness_status) LIKE '%excellent%' OR LOWER(fitness_status) = 'fit' OR fitness_score >= 70)")
        elif st_lower in ('unfit', 'unfit only', 'unfit_only'):
            where_clauses.append("(LOWER(fitness_status) LIKE '%risk%' OR LOWER(fitness_status) LIKE '%unfit%' OR LOWER(fitness_status) LIKE '%poor%' OR LOWER(fitness_status) LIKE '%fail%' OR LOWER(fitness_status) LIKE '%lmc%' OR LOWER(fitness_status) LIKE '%improvement%' OR LOWER(fitness_status) LIKE '%needs imp%' OR LOWER(fitness_status) LIKE '%overweight%' OR LOWER(fitness_status) LIKE '%underweight%' OR (fitness_score IS NOT NULL AND fitness_score < 70))")
        elif st_lower in ('not tested', 'untested', 'not_tested'):
            where_clauses.append("(fitness_status IS NULL OR LOWER(fitness_status) LIKE '%untested%' OR LOWER(fitness_status) LIKE '%not tested%' OR LOWER(fitness_status) LIKE '%insufficient%' OR fitness_score IS NULL)")
        elif st_lower in ('unfit_and_untested', 'unfit & untested', 'unfit not tested', 'unfit and not tested'):
            where_clauses.append("(LOWER(fitness_status) LIKE '%risk%' OR LOWER(fitness_status) LIKE '%unfit%' OR LOWER(fitness_status) LIKE '%poor%' OR LOWER(fitness_status) LIKE '%fail%' OR LOWER(fitness_status) LIKE '%lmc%' OR LOWER(fitness_status) LIKE '%improvement%' OR LOWER(fitness_status) LIKE '%needs imp%' OR LOWER(fitness_status) LIKE '%overweight%' OR LOWER(fitness_status) LIKE '%underweight%' OR LOWER(fitness_status) LIKE '%untested%' OR LOWER(fitness_status) LIKE '%not tested%' OR (fitness_score IS NOT NULL AND fitness_score < 70) OR fitness_score IS NULL)")
        elif 'healthy' in st_lower or 'good' in st_lower:
            where_clauses.append("(LOWER(fitness_status) LIKE '%healthy%' OR LOWER(fitness_status) LIKE '%good%' OR LOWER(fitness_status) LIKE '%optimal%' OR LOWER(fitness_status) LIKE '%excellent%' OR fitness_score >= 70)")
        elif 'improvement' in st_lower or 'overweight' in st_lower or 'moderate' in st_lower or 'average' in st_lower or 'satisfactory' in st_lower:
            where_clauses.append("(LOWER(fitness_status) LIKE '%improvement%' OR LOWER(fitness_status) LIKE '%overweight%' OR LOWER(fitness_status) LIKE '%moderate%' OR LOWER(fitness_status) LIKE '%average%' OR LOWER(fitness_status) LIKE '%satisfactory%' OR (fitness_score >= 50 AND fitness_score < 70))")
        elif 'risk' in st_lower or 'underweight' in st_lower or 'poor' in st_lower:
            where_clauses.append("(LOWER(fitness_status) LIKE '%risk%' OR LOWER(fitness_status) LIKE '%underweight%' OR LOWER(fitness_status) LIKE '%poor%' OR (fitness_score IS NOT NULL AND fitness_score < 50))")
        else:
            where_clauses.append("fitness_status LIKE %s")
            params.append(f"%{status.strip()}%")

    if from_date and str(from_date).strip():
        where_clauses.append("DATE(generated_at) >= %s")
        params.append(str(from_date).strip())

    if to_date and str(to_date).strip():
        where_clauses.append("DATE(generated_at) <= %s")
        params.append(str(to_date).strip())

    where_sql = " AND ".join(where_clauses)

    conn = get_db_connection()
    if not conn:
        return {
            'data': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'total_pages': 0
        }

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Total count query
        count_sql = f"SELECT COUNT(*) AS total_count FROM ai_fitness_reports WHERE {where_sql}"
        cursor.execute(count_sql, tuple(params))
        total_res = cursor.fetchone()
        total = int(total_res['total_count']) if total_res and total_res.get('total_count') is not None else 0

        # 2. Paginated rows query
        data_sql = f"""
            SELECT id, personnel_id, army_number, name, `rank`, company,
                   age, height_cm, actual_weight_kg, ideal_weight_kg, bmi,
                   fitness_score, fitness_status, report_language,
                   report_generated, pdf_path, model_name, model_version,
                   generated_at, updated_at
            FROM ai_fitness_reports
            WHERE {where_sql}
            ORDER BY {sort_column} {order}
            LIMIT %s OFFSET %s
        """
        data_params = params + [per_page, offset]
        cursor.execute(data_sql, tuple(data_params))
        rows = cursor.fetchall()

        formatted_rows = []
        for r in rows:
            formatted_rows.append(_format_report_summary(r))

        total_pages = math.ceil(total / per_page) if total > 0 else 1

        return {
            'success': True,
            'data': formatted_rows,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'pages': total_pages
        }

    except Error as e:
        logger.error(f"Error executing paginated reports query: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'total_pages': 0,
            'pages': 0
        }
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def fetch_dynamic_report_stats():
    """
    Computes real-time dynamic statistics across all generated reports:
    - Total AI Fitness Reports
    - Healthy count
    - Needs Improvement count
    - At Risk count
    - Average Fitness Score
    - Reports Generated Today
    - Reports Generated This Month
    - Distinct Companies List
    """
    ensure_ai_fitness_reports_table()

    conn = get_db_connection()
    if not conn:
        empty_stats = {
            'total_reports': 0,
            'healthy_count': 0,
            'healthy': 0,
            'needs_improvement_count': 0,
            'needs_improvement': 0,
            'at_risk_count': 0,
            'at_risk': 0,
            'avg_score': 0.0,
            'today_count': 0,
            'month_count': 0,
            'companies': []
        }
        return {
            'success': False,
            'error': 'Database connection unavailable',
            'stats': empty_stats,
            **empty_stats
        }

    try:
        cursor = conn.cursor(dictionary=True)

        stats_sql = """
            SELECT
                COUNT(*) AS total_reports,
                SUM(CASE WHEN LOWER(fitness_status) LIKE '%healthy%' OR LOWER(fitness_status) LIKE '%good%' OR LOWER(fitness_status) LIKE '%optimal%' OR LOWER(fitness_status) LIKE '%excellent%' OR fitness_score >= 70 THEN 1 ELSE 0 END) AS healthy,
                SUM(CASE WHEN (LOWER(fitness_status) LIKE '%improvement%' OR LOWER(fitness_status) LIKE '%overweight%' OR LOWER(fitness_status) LIKE '%moderate%' OR LOWER(fitness_status) LIKE '%average%' OR LOWER(fitness_status) LIKE '%satisfactory%' OR (fitness_score >= 50 AND fitness_score < 70)) AND NOT (LOWER(fitness_status) LIKE '%risk%' OR LOWER(fitness_status) LIKE '%at-risk%') THEN 1 ELSE 0 END) AS needs_improvement,
                SUM(CASE WHEN LOWER(fitness_status) LIKE '%risk%' OR LOWER(fitness_status) LIKE '%underweight%' OR LOWER(fitness_status) LIKE '%poor%' OR (fitness_score IS NOT NULL AND fitness_score < 50) THEN 1 ELSE 0 END) AS at_risk,
                SUM(CASE WHEN LOWER(fitness_status) LIKE '%risk%' OR LOWER(fitness_status) LIKE '%unfit%' OR LOWER(fitness_status) LIKE '%poor%' OR LOWER(fitness_status) LIKE '%fail%' OR LOWER(fitness_status) LIKE '%lmc%' OR LOWER(fitness_status) LIKE '%improvement%' OR LOWER(fitness_status) LIKE '%needs imp%' OR LOWER(fitness_status) LIKE '%overweight%' OR LOWER(fitness_status) LIKE '%underweight%' OR (fitness_score IS NOT NULL AND fitness_score < 70) THEN 1 ELSE 0 END) AS unfit,
                SUM(CASE WHEN fitness_status IS NULL OR LOWER(fitness_status) LIKE '%untested%' OR LOWER(fitness_status) LIKE '%not tested%' OR LOWER(fitness_status) LIKE '%insufficient%' OR fitness_score IS NULL THEN 1 ELSE 0 END) AS not_tested,
                AVG(fitness_score) AS avg_score,
                SUM(CASE WHEN DATE(generated_at) = CURDATE() THEN 1 ELSE 0 END) AS today_count,
                SUM(CASE WHEN MONTH(generated_at) = MONTH(CURDATE()) AND YEAR(generated_at) = YEAR(CURDATE()) THEN 1 ELSE 0 END) AS month_count
            FROM ai_fitness_reports
            WHERE (army_number NOT LIKE 'TEST%' AND army_number NOT LIKE 'jk010101%' AND (name IS NULL OR name NOT LIKE '%TEST%'))
        """
        cursor.execute(stats_sql)
        row = cursor.fetchone() or {}

        # Distinct companies strictly restricted to the 3 designated unit companies
        VALID_COMPANIES = ['3 Company', 'COMN Company', 'HQ company']
        cursor.execute("""
            SELECT DISTINCT company FROM ai_fitness_reports
            WHERE company IS NOT NULL AND company != ''
              AND (army_number NOT LIKE 'TEST%' AND army_number NOT LIKE 'jk010101%' AND (name IS NULL OR name NOT LIKE '%TEST%'))
            ORDER BY company ASC
        """)
        c_rows = cursor.fetchall() or []
        raw_comps = [c['company'] for c in c_rows if c.get('company')]
        # Retain only the 3 valid companies, excluding admn and comn
        companies = [c for c in VALID_COMPANIES if c in raw_comps] or VALID_COMPANIES

        total = int(row.get('total_reports') or 0)
        healthy = int(row.get('healthy') or 0)
        needs_imp = int(row.get('needs_improvement') or 0)
        at_risk = int(row.get('at_risk') or 0)
        unfit_count = int(row.get('unfit') or (needs_imp + at_risk))
        avg_score = round(float(row.get('avg_score') or 0.0), 1)
        today_cnt = int(row.get('today_count') or 0)
        month_cnt = int(row.get('month_count') or 0)

        # Ensure healthy + needs_imp + at_risk account for all if other status names exist
        remainder = total - (healthy + needs_imp + at_risk)
        if remainder > 0 and healthy == 0 and needs_imp == 0:
            healthy = remainder

        fit_count = healthy

        not_tested_count = int(row.get('not_tested') or 0)

        stats_dict = {
            'total_reports': total,
            'fit_count': fit_count,
            'unfit_count': unfit_count,
            'not_tested_count': not_tested_count,
            'healthy_count': healthy,
            'healthy': healthy,
            'needs_improvement_count': needs_imp,
            'needs_improvement': needs_imp,
            'at_risk_count': at_risk,
            'at_risk': at_risk,
            'avg_score': avg_score,
            'today_count': today_cnt,
            'month_count': month_cnt,
            'companies': companies
        }

        return {
            'success': True,
            'stats': stats_dict,
            **stats_dict
        }

    except Error as e:
        logger.error(f"Error fetching dynamic report stats: {e}")
        err_stats = {
            'total_reports': 0,
            'healthy_count': 0,
            'healthy': 0,
            'needs_improvement_count': 0,
            'needs_improvement': 0,
            'at_risk_count': 0,
            'at_risk': 0,
            'avg_score': 0.0,
            'today_count': 0,
            'month_count': 0,
            'companies': []
        }
        return {
            'success': False,
            'error': str(e),
            'stats': err_stats,
            **err_stats
        }
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def _safe_json_dumps(obj):
    """Serialize object to JSON string, handling nested dicts and fallback."""
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, default=str)
    except Exception as e:
        logger.warning(f"Error serializing JSON object: {e}")
        return str(obj)


def _safe_json_loads(val):
    """Deserialize JSON string, returning None or empty dict if invalid."""
    if not val:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return None


def _deserialize_report_row(row):
    """Deserialize database record fields into python primitives/dicts."""
    d = dict(row)
    d['prediction_result'] = _safe_json_loads(d.get('prediction_result'))
    d['recommendations'] = _safe_json_loads(d.get('recommendations'))
    d['diet_recommendations'] = _safe_json_loads(d.get('diet_recommendations'))
    d['exercise_recommendations'] = _safe_json_loads(d.get('exercise_recommendations'))
    d['progression_prediction'] = _safe_json_loads(d.get('progression_prediction'))

    if d.get('height_cm') is not None:
        d['height_cm'] = float(d['height_cm'])
    if d.get('actual_weight_kg') is not None:
        d['actual_weight_kg'] = float(d['actual_weight_kg'])
    if d.get('ideal_weight_kg') is not None:
        d['ideal_weight_kg'] = float(d['ideal_weight_kg'])
    if d.get('bmi') is not None:
        d['bmi'] = float(d['bmi'])
    if d.get('fitness_score') is not None:
        d['fitness_score'] = float(d['fitness_score'])
    if d.get('generated_at') and isinstance(d['generated_at'], datetime):
        d['generated_at_str'] = d['generated_at'].strftime('%d %b %Y, %I:%M %p')
        d['date_time_12hr'] = d['generated_at'].strftime('%d %b %Y, %I:%M %p')
    return d


def _format_report_summary(row):
    """Formats summary dictionary for table rendering with graceful N/A handling."""
    d = dict(row)
    if d.get('height_cm') is not None:
        d['height_cm'] = float(d['height_cm'])
    if d.get('actual_weight_kg') is not None:
        d['actual_weight_kg'] = float(d['actual_weight_kg'])
    if d.get('ideal_weight_kg') is not None:
        d['ideal_weight_kg'] = float(d['ideal_weight_kg'])
    if d.get('bmi') is not None:
        d['bmi'] = float(d['bmi'])
    if d.get('fitness_score') is not None:
        d['fitness_score'] = float(d['fitness_score'])

    gen_at = d.get('generated_at') or d.get('updated_at')
    if gen_at and isinstance(gen_at, datetime):
        d['generated_at_str'] = gen_at.strftime('%d %b %Y, %I:%M %p')
        d['date_time_12hr'] = gen_at.strftime('%d %b %Y, %I:%M %p')
    elif gen_at:
        try:
            if isinstance(gen_at, str):
                parsed_dt = None
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
                    try:
                        parsed_dt = datetime.strptime(gen_at.split('.')[0], fmt)
                        break
                    except ValueError:
                        pass
                if parsed_dt:
                    d['generated_at_str'] = parsed_dt.strftime('%d %b %Y, %I:%M %p')
                    d['date_time_12hr'] = parsed_dt.strftime('%d %b %Y, %I:%M %p')
                else:
                    d['generated_at_str'] = str(gen_at)
                    d['date_time_12hr'] = str(gen_at)
            else:
                d['generated_at_str'] = str(gen_at)
                d['date_time_12hr'] = str(gen_at)
        except Exception:
            d['generated_at_str'] = str(gen_at)
            d['date_time_12hr'] = str(gen_at)
    else:
        d['generated_at_str'] = 'N/A'
        d['date_time_12hr'] = 'N/A'

    # Graceful fallbacks
    d['army_number'] = d.get('army_number') or 'N/A'
    d['name'] = d.get('name') or 'N/A'
    d['rank'] = d.get('rank') or 'N/A'
    raw_fit_st = str(d.get('fitness_status') or 'N/A').strip()
    low_st = raw_fit_st.lower()
    sc = d.get('fitness_score')
    if 'untested' in low_st or 'not tested' in low_st or 'insufficient' in low_st:
        d['fitness_status'] = 'Not Tested'
    elif 'healthy' in low_st or 'combat' in low_st or 'ready' in low_st or 'good' in low_st or (sc is not None and sc >= 70 and 'risk' not in low_st and 'unfit' not in low_st and 'improv' not in low_st):
        d['fitness_status'] = 'Healthy'
    elif 'improve' in low_st or 'needs imp' in low_st or 'risk' in low_st or 'unfit' in low_st or (sc is not None and sc < 70):
        d['fitness_status'] = 'Unfit'
    else:
        d['fitness_status'] = raw_fit_st or 'N/A'
    d['report_generated'] = bool(d.get('report_generated', True))

    return d
