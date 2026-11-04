import os
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_db_config():
    """
    Retrieves current DB configuration from environment variables.
    Preserves empty string password if explicitly set.
    """
    load_dotenv(override=True)
    env_pass = os.getenv('DB_PASSWORD')
    if env_pass is None:
        env_pass = os.getenv('DB_PASS')
    if env_pass is None:
        env_pass = 'yawar@123'

    return {
        'host': os.getenv('DB_HOST') or os.getenv('host') or 'localhost',
        'user': os.getenv('DB_USER') or 'root',
        'password': env_pass,
        'database': os.getenv('DB_NAME') or 'rr_ums',
        'port': int(os.getenv('DB_PORT') or 3306)
    }


DB_CONFIG = get_db_config()
POOL_SIZE = int(os.getenv('DB_POOL_SIZE') or 32)

_db_pool = None


def _init_pool():
    global _db_pool, DB_CONFIG
    if _db_pool is None:
        DB_CONFIG = get_db_config()
        try:
            _db_pool = pooling.MySQLConnectionPool(
                pool_name="hrms_pool",
                pool_size=POOL_SIZE,
                pool_reset_session=True,
                **DB_CONFIG
            )
        except Error as e:
            print(f"[DB Pool Warning] Could not initialize connection pool: {e}")
            _db_pool = None


# Initialize pool on module import
_init_pool()


def get_db_connection():
    """
    Returns a pooled connection if available, otherwise falls back to a direct connection.
    Calling conn.close() on a pooled connection automatically returns it to the pool.
    """
    global _db_pool, DB_CONFIG
    if _db_pool is None:
        _init_pool()

    if _db_pool:
        try:
            return _db_pool.get_connection()
        except Error as e:
            # Fallback to direct connection if pool is temporarily exhausted
            try:
                return mysql.connector.connect(**DB_CONFIG)
            except Error as direct_err:
                print(f"[DB Connection Error] Direct connection failed: {direct_err}")
                return None
    else:
        try:
            DB_CONFIG = get_db_config()
            return mysql.connector.connect(**DB_CONFIG)
        except Error as direct_err:
            print(f"[DB Connection Error] Direct connection failed: {direct_err}")
            return None



def get_alarm_thresholds(existing_conn=None):
    """
    Returns a dict with {'detachment_alarm': int, 'attachment_alarm': int}.
    Defaults to {'detachment_alarm': 60, 'attachment_alarm': 80} if DB is unreachable.
    Auto-initializes table `det_td_alarm_days` and seeds default values if missing.
    """
    defaults = {
        'detachment_alarm': 60,
        'attachment_alarm': 80
    }
    close_conn = False
    conn = existing_conn
    cursor = None
    try:
        if not conn:
            conn = get_db_connection()
            close_conn = True
        if not conn:
            return defaults

        cursor = conn.cursor(dictionary=True)
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `det_td_alarm_days` (
                `alarm_name` VARCHAR(50) NOT NULL PRIMARY KEY,
                `days` INT NOT NULL DEFAULT 90,
                `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                `updated_by` VARCHAR(50) DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        # Ensure default rows exist
        cursor.execute("""
            INSERT IGNORE INTO `det_td_alarm_days` (`alarm_name`, `days`) VALUES 
            ('detachment_alarm', 60),
            ('attachment_alarm', 80);
        """)
        conn.commit()

        cursor.execute("SELECT `alarm_name`, `days` FROM `det_td_alarm_days`")
        rows = cursor.fetchall()
        for r in rows:
            name = (r.get('alarm_name') or '').strip().lower()
            val = r.get('days')
            if name in defaults and val is not None:
                try:
                    defaults[name] = max(1, int(val))
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        print(f"[Alarm Threshold Warning] Error fetching thresholds: {e}")
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if close_conn and conn:
            try: conn.close()
            except Exception: pass

    return defaults


def set_alarm_threshold(alarm_name, days, updated_by=None, existing_conn=None):
    """
    Sets the threshold days for an alarm in `det_td_alarm_days`.
    """
    close_conn = False
    conn = existing_conn
    cursor = None
    try:
        if not conn:
            conn = get_db_connection()
            close_conn = True
        if not conn:
            return False

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO `det_td_alarm_days` (`alarm_name`, `days`, `updated_by`)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE `days` = VALUES(`days`), `updated_by` = VALUES(`updated_by`);
        """, (alarm_name, int(days), updated_by))
        conn.commit()
        return True
    except Exception as e:
        print(f"[Alarm Threshold Error] Failed to update {alarm_name}: {e}")
        return False
    finally:
        if cursor:
            try: cursor.close()
            except Exception: pass
        if close_conn and conn:
            try: conn.close()
            except Exception: pass
