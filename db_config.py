import os
import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration loaded dynamically from .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST') or os.getenv('host') or 'localhost',
    'user': os.getenv('DB_USER') or 'root',
    'password': os.getenv('DB_PASSWORD') or 'qaz123QAZ!@#',
    'database': os.getenv('DB_NAME') or 'hrms',
    'port': int(os.getenv('DB_PORT') or 3306)
}

# Connection pool size optimized for ~40-70 active users (mysql.connector supports up to 32 per pool)
POOL_SIZE = int(os.getenv('DB_POOL_SIZE') or 32)

_db_pool = None


def _init_pool():
    global _db_pool
    if _db_pool is None:
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
    global _db_pool
    if _db_pool is None:
        _init_pool()

    if _db_pool:
        try:
            return _db_pool.get_connection()
        except Error as e:
            # Fallback to direct connection if pool is temporarily exhausted
            try:
                return mysql.connector.connect(**DB_CONFIG)
            except Error:
                return None
    else:
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error:
            return None

