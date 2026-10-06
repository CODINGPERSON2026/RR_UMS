"""
Safe, parameterized SQL queries for AI Company Readiness module.
Integrates with MySQL tables: ai_company_requirements, personnel, courses,
weight_info, and ai_company_readiness_history.
"""

from typing import List, Dict, Any, Optional
import mysql.connector
from .utils import get_db_company_variants, normalize_company_name


_TABLES_ENSURED = False


def ensure_company_readiness_tables(conn) -> None:
    """
    Auto-creates `ai_company_requirements` and `ai_company_readiness_history` tables
    if they do not exist, and seeds default baseline requirements if empty.
    """
    global _TABLES_ENSURED
    if _TABLES_ENSURED:
        return

    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_company_requirements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company VARCHAR(100) NOT NULL,
                requirement_type VARCHAR(100) NOT NULL,
                requirement_name VARCHAR(255) NOT NULL,
                required_count INT NOT NULL DEFAULT 0,
                priority VARCHAR(50) DEFAULT 'Medium',
                status VARCHAR(20) DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                INDEX idx_company (company),
                INDEX idx_requirement_type (requirement_type),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_company_readiness_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company VARCHAR(100) NOT NULL,
                snapshot_date DATE NOT NULL,
                strength_score FLOAT NOT NULL,
                qualification_score FLOAT NOT NULL,
                course_score FLOAT NOT NULL,
                trade_score FLOAT NOT NULL,
                fitness_score FLOAT NOT NULL,
                medical_score FLOAT NOT NULL,
                availability_score FLOAT NOT NULL,
                overall_readiness FLOAT NOT NULL,
                main_gap_type VARCHAR(100),
                gap_count INT DEFAULT 0,
                actual_strength INT DEFAULT 0,
                required_strength INT DEFAULT 0,
                available_strength INT DEFAULT 0,
                unfit_count INT DEFAULT 0,
                onleave_count INT DEFAULT 0,
                detachment_count INT DEFAULT 0,
                td_count INT DEFAULT 0,
                oncourse_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                INDEX idx_comp_date (company, snapshot_date),
                INDEX idx_company_hist (company)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        conn.commit()

        # Check if ai_company_requirements has data
        cursor.execute("SELECT COUNT(*) FROM ai_company_requirements")
        row = cursor.fetchone()
        count = row[0] if isinstance(row, (tuple, list)) else 0

        if count == 0:
            seed_data = [
                # HQ COY
                ("HQ COY", "Strength", "Total Personnel", 100, "Critical", "Active"),
                ("HQ COY", "Trade", "TTC", 40, "High", "Active"),
                ("HQ COY", "Trade", "LMN", 20, "High", "Active"),
                ("HQ COY", "Trade", "EFS", 15, "Medium", "Active"),
                ("HQ COY", "Trade", "OCC", 10, "Medium", "Active"),
                ("HQ COY", "Trade", "CLK SD", 10, "High", "Active"),
                ("HQ COY", "Qualification", "12th", 80, "Medium", "Active"),
                ("HQ COY", "Qualification", "Graduation", 20, "Low", "Active"),
                ("HQ COY", "Course", "TTC CL I", 15, "High", "Active"),
                ("HQ COY", "Course", "Signals", 25, "Medium", "Active"),

                # COMN COY
                ("COMN COY", "Strength", "Total Personnel", 120, "Critical", "Active"),
                ("COMN COY", "Trade", "TTC", 50, "High", "Active"),
                ("COMN COY", "Trade", "LMN", 35, "High", "Active"),
                ("COMN COY", "Trade", "EFS", 20, "Medium", "Active"),
                ("COMN COY", "Trade", "OCC", 15, "Medium", "Active"),
                ("COMN COY", "Qualification", "12th", 90, "Medium", "Active"),
                ("COMN COY", "Course", "TTC CL I", 20, "High", "Active"),
                ("COMN COY", "Course", "Signals", 40, "High", "Active"),

                # 3 COY
                ("3 COY", "Strength", "Total Personnel", 110, "Critical", "Active"),
                ("3 COY", "Trade", "TTC", 45, "High", "Active"),
                ("3 COY", "Trade", "LMN", 25, "High", "Active"),
                ("3 COY", "Trade", "EFS", 15, "Medium", "Active"),
                ("3 COY", "Qualification", "12th", 85, "Medium", "Active"),
                ("3 COY", "Course", "TTC CL I", 15, "High", "Active"),
            ]
            insert_stmt = """
                INSERT INTO ai_company_requirements (company, requirement_type, requirement_name, required_count, priority, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_stmt, seed_data)
            conn.commit()

        _TABLES_ENSURED = True
    except Exception as err:
        print(f"[AI Company Readiness] Error in ensure_company_readiness_tables: {err}")
    finally:
        cursor.close()


def fetch_company_requirements(conn, canonical_company: str) -> List[Dict[str, Any]]:
    """
    Fetches active requirements for the specified company.
    Queries ai_company_requirements matching the canonical company name.
    """
    ensure_company_readiness_tables(conn)
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT id, company, requirement_type, requirement_name, required_count, priority, status
        FROM ai_company_requirements
        WHERE (company = %s OR company = %s) AND status = 'Active'
        ORDER BY priority DESC, requirement_type ASC
    """
    variants = get_db_company_variants(canonical_company)
    primary_var = variants[1] if len(variants) > 1 else canonical_company
    cursor.execute(query, (canonical_company, primary_var))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def fetch_all_active_requirements(conn) -> List[Dict[str, Any]]:
    """Fetches all active baseline requirements across companies."""
    ensure_company_readiness_tables(conn)
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT id, company, requirement_type, requirement_name, required_count, priority, status
        FROM ai_company_requirements
        WHERE status = 'Active'
        ORDER BY company ASC, priority DESC, requirement_type ASC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def fetch_company_personnel(conn, canonical_company: str) -> List[Dict[str, Any]]:
    """
    Fetches all soldier records in the specified company.
    Uses variants to match company names like 'HQ company' and 'HQ COY'.
    """
    cursor = conn.cursor(dictionary=True)
    variants = get_db_company_variants(canonical_company)
    placeholders = ", ".join(["%s"] * len(variants))
    query = f"""
        SELECT 
            id, army_number, name, `rank`, trade, company,
            civ_qualifications, lacking_qualifications,
            bpet_grading, ppt_grading, bpet_date,
            med_cat, medical_problem, restrictions,
            detailed_course, onleave_status, detachment_status,
            posting_status, personnel_status, td_status,
            interview_status, section, oncourse_status,
            next_recat_due, height, weight
        FROM personnel
        WHERE company IN ({placeholders})
        ORDER BY `rank` ASC, name ASC
    """
    cursor.execute(query, tuple(variants))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def fetch_personnel_courses(conn, army_numbers: List[str]) -> List[Dict[str, Any]]:
    """Fetches course records for a list of army numbers."""
    if not army_numbers:
        return []
    cursor = conn.cursor(dictionary=True)
    placeholders = ", ".join(["%s"] * len(army_numbers))
    query = f"""
        SELECT personnel_id, army_number, course, grading, from_date, to_date, institute
        FROM courses
        WHERE army_number IN ({placeholders})
    """
    cursor.execute(query, tuple(army_numbers))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def fetch_personnel_weight_info(conn, army_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetches physical/weight information keyed by army_number."""
    if not army_numbers:
        return {}
    cursor = conn.cursor(dictionary=True)
    placeholders = ", ".join(["%s"] * len(army_numbers))
    query = f"""
        SELECT troop_id, army_number, name, `rank`, actual_weight, height, age,
               status_type, category_type, restrictions
        FROM weight_info
        WHERE army_number IN ({placeholders})
    """
    cursor.execute(query, tuple(army_numbers))
    rows = cursor.fetchall()
    cursor.close()
    return {r["army_number"]: r for r in rows if r.get("army_number")}


def insert_readiness_snapshot(conn, data: Dict[str, Any]) -> int:
    """Inserts a calculated readiness snapshot into ai_company_readiness_history."""
    ensure_company_readiness_tables(conn)
    cursor = conn.cursor()
    query = """
        INSERT INTO ai_company_readiness_history (
            company, snapshot_date, strength_score, qualification_score,
            course_score, trade_score, fitness_score, medical_score,
            availability_score, overall_readiness, main_gap_type,
            gap_count, actual_strength, required_strength, available_strength,
            unfit_count, onleave_count, detachment_count, td_count, oncourse_count
        ) VALUES (
            %(company)s, %(snapshot_date)s, %(strength_score)s, %(qualification_score)s,
            %(course_score)s, %(trade_score)s, %(fitness_score)s, %(medical_score)s,
            %(availability_score)s, %(overall_readiness)s, %(main_gap_type)s,
            %(gap_count)s, %(actual_strength)s, %(required_strength)s, %(available_strength)s,
            %(unfit_count)s, %(onleave_count)s, %(detachment_count)s, %(td_count)s, %(oncourse_count)s
        )
    """
    cursor.execute(query, data)
    conn.commit()
    inserted_id = cursor.lastrowid
    cursor.close()
    return inserted_id


def fetch_historical_snapshots(conn, canonical_company: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetches historical readiness snapshots ordered by date."""
    ensure_company_readiness_tables(conn)
    cursor = conn.cursor(dictionary=True)
    if canonical_company:
        query = """
            SELECT * FROM ai_company_readiness_history
            WHERE company = %s
            ORDER BY snapshot_date DESC, id DESC
            LIMIT %s
        """
        cursor.execute(query, (canonical_company, limit))
    else:
        query = """
            SELECT * FROM ai_company_readiness_history
            ORDER BY snapshot_date DESC, id DESC
            LIMIT %s
        """
        cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def upsert_requirement(conn, data: Dict[str, Any]) -> int:
    """Inserts or updates a requirement in ai_company_requirements."""
    ensure_company_readiness_tables(conn)
    cursor = conn.cursor()
    req_id = data.get("id")
    if req_id:
        query = """
            UPDATE ai_company_requirements
            SET company = %(company)s,
                requirement_type = %(requirement_type)s,
                requirement_name = %(requirement_name)s,
                required_count = %(required_count)s,
                priority = %(priority)s,
                status = %(status)s
            WHERE id = %(id)s
        """
        cursor.execute(query, data)
        conn.commit()
        ret_id = req_id
    else:
        query = """
            INSERT INTO ai_company_requirements (
                company, requirement_type, requirement_name, required_count, priority, status
            ) VALUES (
                %(company)s, %(requirement_type)s, %(requirement_name)s, %(required_count)s, %(priority)s, %(status)s
            )
        """
        cursor.execute(query, data)
        conn.commit()
        ret_id = cursor.lastrowid
    cursor.close()
    return ret_id


def delete_requirement(conn, req_id: int) -> bool:
    """Deletes or archives a requirement from ai_company_requirements."""
    ensure_company_readiness_tables(conn)
    cursor = conn.cursor()
    query = "DELETE FROM ai_company_requirements WHERE id = %s"
    cursor.execute(query, (req_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    cursor.close()
    return deleted
