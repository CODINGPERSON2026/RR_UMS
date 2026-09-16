import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from aiml.fitness_trend.api import calculate_all_individuals_fitness, get_all_reports_paginated

# 1. Run batch calculation
print("Running calculate_all_individuals_fitness()...")
res = calculate_all_individuals_fitness()
print(f"Result: success={res['success']}, total_processed={res['total_processed']}, unfit={res['unfit_count']}, fit={res['fit_count']}")

# 2. Query CO, 2IC, Adjutant role table reports
reports_res = get_all_reports_paginated(status="Unfit", page=1, per_page=500)
unfit_rows = reports_res.get('data', [])
print(f"Total reports fetched for CO/2IC/Adjutant table: {len(unfit_rows)}")

# 3. Verify ALL records in CO/2IC/Adjutant table are UNFIT
all_unfit = True
fit_leaks = []
for r in unfit_rows:
    score = r.get('fitness_score')
    status = str(r.get('fitness_status', '')).lower()
    is_unfit = False
    if score is None or score < 70:
        is_unfit = True
    elif any(k in status for k in ('risk', 'unfit', 'poor', 'fail', 'lmc', 'improvement', 'needs imp', 'overweight', 'underweight')):
        is_unfit = True
    
    if not is_unfit:
        all_unfit = False
        fit_leaks.append(r)

if all_unfit:
    print(f"SUCCESS: All {len(unfit_rows)} fetched records are strictly UNFIT! Zero fit soldiers leaked.")
else:
    print(f"FAIL: Found {len(fit_leaks)} fit records in unfit table!")
