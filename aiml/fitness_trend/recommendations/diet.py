"""
Personalized Dietary & Macronutrient Recommendation Engine.
Calculates energy requirements and balanced nutrition plans tailored for military personnel.
"""


def generate_personalized_diet(soldier_features, goal="Overall Fitness"):
    """
    Computes caloric targets, macronutrient split, hydration, and structured meal recommendations.
    
    Args:
        soldier_features: dict containing soldier metrics.
        goal: str ('Overall Fitness', 'Weight Loss', 'Endurance', 'Strength', 'BPET Improvement', 'PPT Improvement')
        
    Returns:
        dict: Complete personalized nutrition guidelines.
    """
    wt = soldier_features.get('actual_weight_kg') or 70.0
    ht = soldier_features.get('height_cm') or 172.0
    age = soldier_features.get('age') or 30
    bmi = soldier_features.get('bmi') or 23.5
    dev_pct = soldier_features.get('weight_deviation_percent') or 0.0
    
    # 1. BMR Calculation (Mifflin-St Jeor for males)
    bmr = (10.0 * wt) + (6.25 * ht) - (5.0 * age) + 5.0
    
    # 2. Activity Multiplier (Military baseline training is moderate to high)
    activity_multiplier = 1.55
    if soldier_features.get('has_sport') or goal in ['Endurance', 'BPET Improvement']:
        activity_multiplier = 1.70
    elif soldier_features.get('has_medical_restriction'):
        activity_multiplier = 1.40
        
    tdee = bmr * activity_multiplier
    
    # 3. Goal & Weight-Status Based Calorie Target
    if goal == 'Weight Loss' or dev_pct > 10.0:
        target_calories = int(round(tdee - 450))
        calorie_strategy = "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina."
    elif dev_pct < -8.0:
        target_calories = int(round(tdee + 350))
        calorie_strategy = "Nutrient-Dense Calorie Surplus (+350 kcal) to build lean functional muscle mass."
    elif goal == 'Strength':
        target_calories = int(round(tdee + 200))
        calorie_strategy = "Slight Surplus (+200 kcal) paired with high protein for maximum strength & power development."
    elif goal in ['Endurance', 'BPET Improvement']:
        target_calories = int(round(tdee))
        calorie_strategy = "Isocaloric High-Energy Balance with optimal complex carbohydrates for sustained endurance."
    else:
        target_calories = int(round(tdee))
        calorie_strategy = "Maintenance Calorie Intake optimized for physical conditioning and SHAPE-1 preservation."
        
    # Cap calories within safe boundaries
    target_calories = max(1800, min(3400, target_calories))
    
    # 4. Macronutrient Breakdown
    # Protein: 1.6 - 1.9 g/kg
    protein_g_per_kg = 1.8 if (goal in ['Strength', 'PPT Improvement', 'Weight Loss']) else 1.6
    protein_grams = int(round(wt * protein_g_per_kg))
    protein_cals = protein_grams * 4
    
    # Fats: 22% of total calories
    fat_cals = target_calories * 0.23
    fat_grams = int(round(fat_cals / 9.0))
    
    # Carbohydrates: Remaining calories
    carb_cals = max(0, target_calories - protein_cals - (fat_grams * 9))
    carb_grams = int(round(carb_cals / 4.0))
    
    # 5. Hydration Target
    # Base 35ml/kg + 1.0L for military physical training
    hydration_liters = round(max(3.0, (wt * 0.035) + 1.0), 1)
    
    # 6. Structured Meal Plan (tailored to unit mess & accessible Indian food)
    if dev_pct > 10.0 or goal == 'Weight Loss':
        sample_menu = [
            {"meal": "Early Morning (06:00)", "items": "Warm water with lemon/jeera + 5 soaked almonds + 1 walnut"},
            {"meal": "Breakfast (08:00)", "items": "3 boiled egg whites + 1 whole egg (or 1 bowl sprouts/dal chilla) + 2 multigrain rotis/oats + green tea"},
            {"meal": "Mid-Morning (11:00)", "items": "1 seasonal fruit (apple/orange/guava) or 1 glass fresh buttermilk (chaas)"},
            {"meal": "Lunch (13:00)", "items": "1 big bowl cucumber-tomato salad + 2 dry chapatis + 1 bowl yellow dal + 1 cup stir-fried green vegetables + curd"},
            {"meal": "Pre-PT / Evening (16:30)", "items": "Handful roasted chana (gram) + black coffee / green tea (no sugar)"},
            {"meal": "Dinner (20:00)", "items": "Grilled paneer (100g) or chicken breast (150g) + large bowl vegetable soup + 1 multigrain roti (finish 2 hrs before sleep)"}
        ]
    elif dev_pct < -8.0:
        sample_menu = [
            {"meal": "Early Morning (06:00)", "items": "1 glass milk with 1 banana + handful of mixed nuts (almonds, cashews, raisins)"},
            {"meal": "Breakfast (08:00)", "items": "3 whole eggs / paneer paratha + 1 bowl vegetable porridge (dalia) + banana shake"},
            {"meal": "Mid-Morning (11:00)", "items": "2 whole wheat peanut butter sandwiches + seasonal fruit"},
            {"meal": "Lunch (13:00)", "items": "3-4 chapatis with ghee + 1 bowl rajma/chole + 1 bowl rice + chicken/paneer curry + fresh curd"},
            {"meal": "Pre-PT / Evening (16:30)", "items": "Boiled sweet potatoes / boiled eggs + handful of dates and roasted peanuts"},
            {"meal": "Dinner (20:00)", "items": "3 rotis + 1 bowl mixed dal + paneer/meat preparation + 1 glass warm milk before bed"}
        ]
    else:
        sample_menu = [
            {"meal": "Early Morning (06:00)", "items": "500ml water + 5 soaked almonds + 2 dates"},
            {"meal": "Breakfast (08:00)", "items": "2 whole eggs + 2 egg whites (or paneer bhurji) + 2 chapatis/poha/upma + 1 glass milk/tea"},
            {"meal": "Mid-Morning (11:00)", "items": "1 whole seasonal fruit (banana/apple/pomegranate) + 1 glass chaas with roasted jeera"},
            {"meal": "Lunch (13:00)", "items": "2-3 chapatis + 1 bowl dal/lentils + 1 cup seasonal sabzi + fresh green salad + 1 cup curd"},
            {"meal": "Pre-PT / Evening (16:30)", "items": "Handful roasted chana / 1 boiled egg + black coffee or lemon water"},
            {"meal": "Dinner (20:00)", "items": "2 chapatis + 1 cup dal or lean protein (paneer/chicken/fish) + green leafy vegetable + vegetable clear soup"}
        ]
        
    return {
        'target_calories': target_calories,
        'strategy': calorie_strategy,
        'macros': {
            'protein_grams': protein_grams,
            'carb_grams': carb_grams,
            'fat_grams': fat_grams,
            'protein_pct': round((protein_cals / target_calories) * 100),
            'carb_pct': round((carb_cals / target_calories) * 100),
            'fat_pct': round((fat_cals / target_calories) * 100)
        },
        'hydration_liters': hydration_liters,
        'dietary_guidelines': [
            "Maintain consistent meal timings; finish dinner at least 2 hours before lights out.",
            "Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.",
            "Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.",
            "Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.",
            "Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes."
        ],
        'recommended_items': [
            "Lean poultry, boiled eggs & paneer for muscle protein synthesis",
            "Whole lentils, dal & sprouted beans for sustained amino acids",
            "Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment",
            "Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients",
            "Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily"
        ],
        'limit_items': [
            "Deep-fried mess snacks, pakoras, and processed canteen confectionery",
            "Refined sugar, sugary tea/coffee, and carbonated beverages",
            "Excessive table salt, pickles, and high-sodium processed rations",
            "Irregular meal timings or skipping breakfast prior to morning PT",
            "Heavy meals consumed less than 2 hours before lights out"
        ],
        'sample_menu': sample_menu
    }
