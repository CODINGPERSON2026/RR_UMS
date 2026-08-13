from imports import *

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'yawar@123',
    
    'database': 'hrmsnew',
    'port': 3306
}


def get_db_connection():
    
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        return None
