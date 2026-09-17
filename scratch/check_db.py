import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import time
from db_config import get_db_connection

t0 = time.time()
conn = get_db_connection()
if not conn:
    print("Could not connect to DB")
    sys.exit(1)

cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT COUNT(*) AS cnt FROM weight_info")
res = cursor.fetchone()
print(f"Connected in {time.time() - t0:.2f}s! Count in weight_info: {res['cnt']}")

cursor.execute("SELECT COUNT(*) AS cnt FROM ai_fitness_reports")
res2 = cursor.fetchone()
print(f"Count in ai_fitness_reports: {res2['cnt']}")

cursor.close()
conn.close()
