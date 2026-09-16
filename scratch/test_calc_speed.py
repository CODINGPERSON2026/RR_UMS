import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import time
from aiml.fitness_trend.api import analyze_personnel_fitness
from db_config import get_db_connection

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT army_number FROM weight_info LIMIT 5")
rows = cursor.fetchall()
cursor.close()
conn.close()

for r in rows:
    ano = r['army_number']
    t0 = time.time()
    res = analyze_personnel_fitness(ano, regenerate=True)
    dt = time.time() - t0
    score = res.get('prediction', {}).get('fitness_score')
    cat = res.get('prediction', {}).get('category_label')
    print(f"Soldier {ano}: took {dt:.3f}s -> score={score}, category={cat}")
