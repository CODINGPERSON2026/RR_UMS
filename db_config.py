import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Reynolds@88',
    
    'database': 'ums',
    'port': 3306
}


def get_db_connection():
    
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        return None
