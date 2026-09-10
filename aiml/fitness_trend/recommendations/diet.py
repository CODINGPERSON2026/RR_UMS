"""
Personalized Dietary & Macronutrient Recommendation Engine for Military Personnel.
Constrains nutrition recommendations strictly to the individual's actual military mess menu
(OR MESS for Agniveer -> Havildar; JCO MESS for JCO ranks), computing portion sizes in grams/pieces/ml,
nutritional targets vs estimated intake, and an optional outside-mess diet plan.
"""

from datetime import datetime
import logging
from ..data.mess_menu_db import classify_mess_by_rank, get_mess_menu

logger = logging.getLogger("fitness_trend.recommendations.diet")


def generate_personalized_diet(soldier_features, goal="Overall Fitness", report_date=None):
    """
    Computes caloric targets, macronutrient split, hydration, and structured meal recommendations
    strictly constrained by the individual's applicable military mess menu for the day.
    
    Args:
        soldier_features (dict): Soldier particulars (weight, height, age, rank, fitness status, etc.)
        goal (str): Fitness goal ('Overall Fitness', 'Weight Loss', 'Strength', 'Endurance', etc.)
        report_date (str or datetime, optional): Specific report date. Defaults to current server date.
        
    Returns:
        dict: Complete personalized nutrition plan with mess menu portions, targets vs intake,
              optional diet plan, and backward-compatible fields.
    """
    wt = float(soldier_features.get('actual_weight_kg') or 70.0)
    ht = float(soldier_features.get('height_cm') or 172.0)
    age = int(soldier_features.get('age') or 28)
    bmi = float(soldier_features.get('bmi') or 23.5)
    dev_pct = float(soldier_features.get('weight_deviation_percent') or 0.0)
    fitness_status = str(soldier_features.get('fitness_status') or '').strip().lower()
    rank_str = str(soldier_features.get('rank') or 'Soldier').strip()

    # 1. Automatic Rank -> Mess Category Mapping
    mess_info = classify_mess_by_rank(rank_str)
    mess_type = mess_info['mess_type']      # 'OR' or 'JCO'
    mess_label = mess_info['mess_label']    # 'OR MESS' or 'JCO MESS'

    # 2. Determine Day of the Week
    if report_date:
        if isinstance(report_date, datetime):
            day_of_week = report_date.strftime('%A')
        else:
            try:
                # Try common formats
                parsed_d = None
                for fmt in ('%Y-%m-%d', '%d %b %Y', '%Y/%m/%d', '%d-%m-%Y'):
                    try:
                        parsed_d = datetime.strptime(str(report_date).split('T')[0].split(',')[0].strip(), fmt)
                        break
                    except ValueError:
                        pass
                day_of_week = parsed_d.strftime('%A') if parsed_d else datetime.now().strftime('%A')
            except Exception:
                day_of_week = datetime.now().strftime('%A')
    else:
        day_of_week = datetime.now().strftime('%A')

    # 3. BMR Calculation (Mifflin-St Jeor equation)
    bmr = (10.0 * wt) + (6.25 * ht) - (5.0 * age) + 5.0

    # 4. Activity Multiplier
    activity_multiplier = 1.55
    if soldier_features.get('has_sport') or goal in ['Endurance', 'BPET Improvement']:
        activity_multiplier = 1.70
    elif soldier_features.get('has_medical_restriction'):
        activity_multiplier = 1.40
        
    tdee = bmr * activity_multiplier

    # 5. Goal & Weight Status Strategy
    is_unfit_or_overweight = (
        'risk' in fitness_status or 'unfit' in fitness_status or 'needs' in fitness_status or
        'poor' in fitness_status or bmi >= 25.0 or dev_pct > 10.0 or goal == 'Weight Loss'
    )
    is_underweight = (bmi < 18.5 or dev_pct < -8.0)

    if is_unfit_or_overweight:
        target_calories = int(round(tdee - 450))
        calorie_strategy = f"Calorie Deficit Strategy (~450 kcal below expenditure) for steady body composition optimization while sustaining military operational endurance in {mess_label}."
    elif is_underweight:
        target_calories = int(round(tdee + 350))
        calorie_strategy = f"Nutrient-Dense Calorie Surplus (+350 kcal) to build functional lean muscle mass and restore standard military BMI from {mess_label}."
    elif goal == 'Strength':
        target_calories = int(round(tdee + 200))
        calorie_strategy = f"High-Protein Muscle Power Surplus (+200 kcal) tailored to tactical physical conditioning in {mess_label}."
    elif goal in ['Endurance', 'BPET Improvement']:
        target_calories = int(round(tdee))
        calorie_strategy = f"High-Endurance Isocaloric Balance optimized for BPET/PPT speed and stamina using {mess_label} rations."
    else:
        target_calories = int(round(tdee))
        calorie_strategy = f"Maintenance Calorie Intake optimized for physical conditioning and SHAPE-1 preservation from {mess_label}."

    # Safe boundaries
    target_calories = max(1800, min(3400, target_calories))

    # 6. Macronutrient Targets
    protein_g_per_kg = 1.85 if is_unfit_or_overweight or goal in ['Strength', 'PPT Improvement'] else 1.65
    protein_target = int(round(wt * protein_g_per_kg))
    protein_cals = protein_target * 4

    fat_cals = target_calories * 0.22
    fat_target = int(round(fat_cals / 9.0))

    carb_cals = max(0, target_calories - protein_cals - (fat_target * 9))
    carb_target = int(round(carb_cals / 4.0))

    fiber_target = 35  # grams/day
    hydration_liters = round(max(3.0, (wt * 0.035) + 1.0), 1)

    # 7. Fetch Actual Available Mess Menu Items
    # 7. Helper function to compute calibrated portions for a specific day
    meal_order = ['Breakfast', 'Tea', 'Lunch', 'Dinner'] if mess_type == 'OR' else ['Breakfast', 'Lunch', 'Dinner']

    def _calculate_portions_for_day(day_name):
        menu_day = get_mess_menu(mess_type, day_name)
        day_meals = {}
        day_sample_menu = []
        d_cals, d_p, d_c, d_f, d_fib = 0.0, 0.0, 0.0, 0.0, 0.0

        for meal_type in meal_order:
            items = menu_day.get(meal_type, [])
            if not items:
                continue

            meal_items_rec = []
            meal_display_strings = []

            for it in items:
                food_name = it['food_item']
                unit = it['serving_unit']
                cal_100 = it['calories_per_100g']
                p_100 = it['protein_per_100g']
                c_100 = it['carb_per_100g']
                f_100 = it['fat_per_100g']
                fib_100 = it['fiber_per_100g']
                is_dense = it['is_calorie_dense']
                is_prot = it['is_protein_rich']

                # Calculate personalized serving quantity
                if unit == 'pieces':
                    if 'Egg' in food_name or 'Omelet' in food_name:
                        qty = 2
                        portion_desc = f"{qty} eggs"
                        mult = qty
                    elif 'Roti' in food_name or 'Chapati' in food_name:
                        qty = 2 if is_unfit_or_overweight else (4 if is_underweight else 3)
                        portion_desc = f"{qty} pieces (~{qty * 30} g)"
                        mult = qty
                    elif 'Paratha' in food_name or 'Porota' in food_name or 'Bhatura' in food_name:
                        qty = 1 if is_unfit_or_overweight else 2
                        portion_desc = f"{qty} piece (~{qty * 80} g)" if qty == 1 else f"{qty} pieces (~{qty * 80} g)"
                        mult = qty
                    elif 'Puri' in food_name:
                        qty = 1 if is_unfit_or_overweight else (3 if is_underweight else 2)
                        portion_desc = f"{qty} pieces (~{qty * 30} g)"
                        mult = qty
                    elif 'Papad' in food_name:
                        qty = 1
                        portion_desc = "1 piece"
                        mult = 1
                    elif 'Gulab Jamun' in food_name:
                        qty = 1 if not is_unfit_or_overweight else 0.5
                        portion_desc = "1 piece (controlled)" if is_unfit_or_overweight else "1 piece"
                        mult = 1
                    else:
                        qty = 1
                        portion_desc = "1 piece"
                        mult = 1

                    item_cals = round(cal_100 * mult, 1)
                    item_p = round(p_100 * mult, 1)
                    item_c = round(c_100 * mult, 1)
                    item_f = round(f_100 * mult, 1)
                    item_fib = round(fib_100 * mult, 1)

                elif unit == 'serving':
                    if 'Tea' in food_name:
                        portion_desc = "1 cup (150 ml)" if 'Pakoda' not in food_name else "1 serving (controlled portion)"
                        mult = 0.8 if is_unfit_or_overweight and is_dense else 1.0
                    elif 'Sunday' in food_name:
                        portion_desc = "1 serving (150 ml tea with light snack)"
                        mult = 1.0
                    else:
                        portion_desc = "1 standard serving"
                        mult = 1.0

                    item_cals = round(cal_100 * mult, 1)
                    item_p = round(p_100 * mult, 1)
                    item_c = round(c_100 * mult, 1)
                    item_f = round(f_100 * mult, 1)
                    item_fib = round(fib_100 * mult, 1)

                elif unit == 'ml':
                    portion_desc = "150 ml (minimal sugar)" if is_unfit_or_overweight else "150 ml"
                    mult = 1.5
                    item_cals = round(cal_100 * mult, 1)
                    item_p = round(p_100 * mult, 1)
                    item_c = round(c_100 * mult, 1)
                    item_f = round(f_100 * mult, 1)
                    item_fib = round(fib_100 * mult, 1)

                else:  # grams ('g')
                    if 'Rice' in food_name or 'Biryani' in food_name or 'Khichdi' in food_name or 'Pulav' in food_name:
                        g_val = 120 if is_unfit_or_overweight else (180 if is_underweight else 150)
                    elif 'Chicken' in food_name or 'Fish' in food_name:
                        g_val = 150 if is_unfit_or_overweight else (160 if is_underweight else 130)
                    elif 'Paneer' in food_name or 'Soyabeen' in food_name or 'Egg' in food_name:
                        g_val = 120 if is_unfit_or_overweight else (150 if is_underweight else 120)
                    elif 'Dal' in food_name or 'Kadhi' in food_name or 'Sambar' in food_name or 'Shambhar' in food_name:
                        g_val = 160 if is_unfit_or_overweight else (180 if is_underweight else 150)
                    elif 'Salad' in food_name or 'Kachumber' in food_name:
                        g_val = 130 if is_unfit_or_overweight else 100
                    elif 'Kheer' in food_name or 'Halwa' in food_name or 'Sabudana' in food_name:
                        g_val = 50 if is_unfit_or_overweight else (100 if is_underweight else 75)
                    elif 'Chutney' in food_name or 'Achar' in food_name or 'Mirchi' in food_name:
                        g_val = 25
                    elif 'Upma' in food_name or 'Poha' in food_name:
                        g_val = 130 if is_unfit_or_overweight else (180 if is_underweight else 150)
                    else:  # Veg curries, mix veg, seasonal veg
                        g_val = 150 if is_unfit_or_overweight else (160 if is_underweight else 140)

                    portion_desc = f"{g_val} g"
                    mult = g_val / 100.0

                    item_cals = round(cal_100 * mult, 1)
                    item_p = round(p_100 * mult, 1)
                    item_c = round(c_100 * mult, 1)
                    item_f = round(f_100 * mult, 1)
                    item_fib = round(fib_100 * mult, 1)

                d_cals += item_cals
                d_p += item_p
                d_c += item_c
                d_f += item_f
                d_fib += item_fib

                meal_items_rec.append({
                    'food_item': food_name,
                    'portion': portion_desc,
                    'calories': item_cals,
                    'protein_g': item_p,
                    'carb_g': item_c,
                    'fat_g': item_f,
                    'fiber_g': item_fib,
                    'is_protein_rich': is_prot,
                    'is_calorie_dense': is_dense
                })

                meal_display_strings.append(f"{food_name}: {portion_desc}")

            day_meals[meal_type] = meal_items_rec
            day_sample_menu.append({
                'meal': f"{meal_type} ({day_name})",
                'items': " + ".join(meal_display_strings)
            })

        day_est_intake = {
            'calories': int(round(d_cals)),
            'protein': int(round(d_p)),
            'carbs': int(round(d_c)),
            'fat': int(round(d_f)),
            'fiber': int(round(d_fib))
        }

        return day_meals, day_sample_menu, day_est_intake

    # 8. Compute Full 7-Day Weekly Schedule (Monday to Sunday)
    all_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_schedule = {}
    weekly_schedule_list = []

    for d_name in all_days:
        d_meals, d_sample, d_intake = _calculate_portions_for_day(d_name)
        day_payload = {
            'day': d_name,
            'mess_type': mess_type,
            'mess_category': mess_label,
            'meals': d_meals,
            'sample_menu': d_sample,
            'estimated_intake': d_intake,
            'is_current_day': (d_name.lower() == day_of_week.lower())
        }
        weekly_schedule[d_name] = day_payload
        weekly_schedule_list.append(day_payload)

    # Active day payload for backward compatibility
    current_day_data = weekly_schedule.get(day_of_week, weekly_schedule['Monday'])
    mess_nutrition_plan = current_day_data['meals']
    sample_menu = current_day_data['sample_menu']
    estimated_intake = current_day_data['estimated_intake']

    # 9. Build 30-Day Tactical Nutrition Roadmap (4-Week Cycle: Mon-Sun)
    roadmap_30d = [
        {
            "week": "Week 1 (Days 1–7)",
            "phase": "Metabolic & Caloric Reset",
            "focus": "Strict adherence to designated mess portions and establishing daily hydration baseline.",
            "mess_strategy": f"Adhere strictly to designated {mess_label} portions; eliminate unscheduled fried canteen snacks.",
            "milestone": "Stabilize blood glucose, normalize digestive transit, and establish disciplined water intake."
        },
        {
            "week": "Week 2 (Days 8–14)",
            "phase": "Glycogen & Work Capacity Fueling",
            "focus": "Complex carbohydrate fueling for BPET/PPT drills with post-PT protein recovery.",
            "mess_strategy": "Prioritize dal, eggs, and lean curries within 45 minutes post-morning physical training.",
            "milestone": "Enhanced muscular endurance, reduced post-drill muscle soreness, and sustained training energy."
        },
        {
            "week": "Week 3 (Days 15–21)",
            "phase": "Body Composition & Muscle Recovery",
            "focus": "Accelerated fat oxidation or lean muscle accretion based on soldier's target category.",
            "mess_strategy": "Maintain portion discipline for staple rice/roti while maximizing fresh greens and vegetable curries.",
            "milestone": "Target weight adjustment of 0.8–1.5 kg toward military SHAPE-1 authorization benchmark."
        },
        {
            "week": "Week 4 (Days 22–30)",
            "phase": "Peak Operational Readiness & Consolidation",
            "focus": "Consolidation of 30-day nutritional adaptations and long-term habit institutionalization.",
            "mess_strategy": "Sustain balanced mess rotation; maintain light dinner 2+ hours prior to sleep.",
            "milestone": "Optimized power-to-weight ratio, peak 5km run speed, and sustained SHAPE-1 military readiness."
        }
    ]

    # 10. Build Optional Diet Plan (strictly separated from mess menu)
    optional_diet_plan = [
        {"item": "Hydration Fluid", "recommendation": f"Minimum {hydration_liters} Liters of clean water daily, paced across morning outdoor drills and evening recovery."},
        {"item": "Seasonal Fresh Fruit", "recommendation": "1 whole seasonal fruit (e.g. orange, guava, apple) during mid-morning break if available outside mess."},
        {"item": "Operational Electrolytes", "recommendation": "Coconut water or lemon water with a pinch of black salt during high-heat field or BPET endurance training."},
        {"item": "Night Recovery", "recommendation": "Ensure dinner is finished at least 2 hours before lights-out; 1 glass of warm milk or water prior to sleep if needed."}
    ]

    daily_targets = {
        'calories': target_calories,
        'protein': protein_target,
        'carbs': carb_target,
        'fat': fat_target,
        'fiber': fiber_target,
        'hydration': hydration_liters
    }

    # 10. Assemble Full Nutrition Payload
    return {
        'target_calories': target_calories,
        'strategy': calorie_strategy,
        'mess_category': mess_label,
        'mess_type': mess_type,
        'day_of_week': day_of_week,
        'rank_detected': rank_str,
        'macros': {
            'protein_grams': protein_target,
            'carb_grams': carb_target,
            'fat_grams': fat_target,
            'fiber_grams': fiber_target,
            'protein_pct': round((protein_cals / target_calories) * 100),
            'carb_pct': round((carb_cals / target_calories) * 100),
            'fat_pct': round((fat_cals / target_calories) * 100)
        },
        'daily_targets': daily_targets,
        'estimated_intake': estimated_intake,
        'hydration_liters': hydration_liters,
        'mess_nutrition_plan': mess_nutrition_plan,
        'weekly_schedule': weekly_schedule,
        'weekly_schedule_list': weekly_schedule_list,
        'roadmap_30d': roadmap_30d,
        'optional_diet_plan': optional_diet_plan,
        'sample_menu': sample_menu,
        'dietary_guidelines': [
            f"Adhere strictly to authorized {mess_label} meal timings and portion recommendations.",
            "Finish dinner at least 2 hours prior to lights out for optimal sleep and metabolic recovery.",
            "Prioritize protein-rich mess items (dal, chicken curry, paneer, eggs) immediately post-exercise.",
            "Avoid excessive fried snacks or processed confectionery from unit canteen.",
            f"Maintain daily hydration discipline with at least {hydration_liters} Liters of water."
        ],
        'recommended_items': [
            f"Authorized {mess_label} preparations: dals, lentils, and lean proteins for muscle preservation",
            "Complex carbohydrate portions (chapati, rice) calibrated to daily physical exertion",
            "Seasonal vegetables and salads from unit rations for vital micronutrients",
            f"Daily scheduled hydration of minimum {hydration_liters} Liters"
        ],
        'limit_items': [
            "Excessive portions of calorie-dense fried snacks (pakoras, puris) beyond recommendation",
            "Refined sugar, heavily sweetened tea/coffee, and carbonated beverages",
            "Skipping scheduled breakfast prior to morning physical training",
            "Consuming heavy meals less than 2 hours before lights out"
        ]
    }
