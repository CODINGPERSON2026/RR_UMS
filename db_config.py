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
        env_pass = 'qaz123QAZ!@#'

    return {
        'host': os.getenv('DB_HOST') or os.getenv('host') or 'localhost',
        'user': os.getenv('DB_USER') or 'root',
        'password': env_pass,
        'database': os.getenv('DB_NAME') or 'hrms',
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

