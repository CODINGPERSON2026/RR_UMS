import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration loaded dynamically from .env
DB_CONFIG = {
    'host': os.getenv('DB_HOST') or os.getenv('host') or 'localhost',
    'user': os.getenv('DB_USER') or 'root',
    'password': os.getenv('DB_PASSWORD') or 'yawar@123',
    'database': os.getenv('DB_NAME') or 'hrmsnew',
    'port': int(os.getenv('DB_PORT') or 3306)
}


def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        return None
