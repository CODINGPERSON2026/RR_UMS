import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import time
from aiml.fitness_trend.api import calculate_all_individuals_fitness
from db_config import get_db_connection

t0 = time.time()
res = calculate_all_individuals_fitness()
dt = time.time() - t0
print(f"calculate_all_individuals_fitness completed in {dt:.2f}s!")
print(f"Success: {res.get('success')}")
print(f"Total processed: {res.get('total_processed')}")
print(f"Unfit count: {res.get('unfit_count')}")
print(f"Fit count: {res.get('fit_count')}")
print(f"Saved: {res.get('saved')}")

# Verify in DB
conn = get_db_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT COUNT(*) AS total_in_db FROM ai_fitness_reports")
print("Total rows now in ai_fitness_reports:", cursor.fetchone()['total_in_db'])
cursor.close()
conn.close()
