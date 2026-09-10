import unittest
import os
import sys
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from aiml.fitness_trend.data.mess_menu_db import (
    classify_mess_by_rank,
    get_mess_menu,
    ensure_mess_menus_table,
    OR_MESS_SCHEDULE,
    JCO_MESS_SCHEDULE
)
from aiml.fitness_trend.recommendations.diet import (
    generate_personalized_diet
)
from aiml.fitness_trend.recommendations.exercise import (
    generate_personalized_exercise_plan,
    filter_unsafe_exercises
)
from aiml.fitness_trend.reports.fitness_report import build_structured_fitness_report
from aiml.fitness_trend.pdf.report_generator import generate_multilingual_fitness_pdf
from aiml.fitness_trend.api import analyze_personnel_fitness


class TestMessAndExerciseUpgrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure tables exist
        ensure_mess_menus_table()

    def test_01_rank_classification(self):
        """Verify automatic rank classification for OR and JCO without user input."""
        # OR Ranks
        or_ranks = ['Agniveer', 'agniveer GD', 'Sepoy', 'Sep', 'L/NK', 'Lance Naik',
                    'NK', 'Naik', 'Havildar', 'HAV', 'Hav', 'CQMH', 'CHM', 'RHM',
                    'CFN', 'Craftsman', 'Signal Man', 'Sigman', 'Gunner', 'Rfn']
        for r in or_ranks:
            mess_info = classify_mess_by_rank(r)
            self.assertEqual(mess_info['mess_label'], 'OR MESS', f"Rank '{r}' should classify as OR MESS, got '{mess_info['mess_label']}'")
            self.assertEqual(mess_info['mess_type'], 'OR')

        # JCO Ranks
        jco_ranks = ['Naib Subedar', 'Nb Sub', 'nb subedar', 'Subedar', 'Sub',
                     'Subedar Major', 'Sub Maj', 'sub maj', 'Hony Capt', 'Hony Lt',
                     'Honorary Captain', 'Honorary Lieutenant']
        for r in jco_ranks:
            mess_info = classify_mess_by_rank(r)
            self.assertEqual(mess_info['mess_label'], 'JCO MESS', f"Rank '{r}' should classify as JCO MESS, got '{mess_info['mess_label']}'")
            self.assertEqual(mess_info['mess_type'], 'JCO')

    def test_02_database_menu_loading(self):
        """Verify menus can be retrieved for all 7 days for both OR and JCO."""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for d in days:
            or_menu = get_mess_menu('OR', d)
            self.assertGreater(len(or_menu), 0, f"OR Menu for {d} should have items")
            self.assertTrue({'Breakfast', 'Tea', 'Lunch', 'Dinner'}.issubset(set(or_menu.keys())),
                            f"OR Menu on {d} missing standard meals: {list(or_menu.keys())}")

            jco_menu = get_mess_menu('JCO', d)
            self.assertGreater(len(jco_menu), 0, f"JCO Menu for {d} should have items")
            self.assertTrue({'Breakfast', 'Lunch', 'Dinner'}.issubset(set(jco_menu.keys())),
                            f"JCO Menu on {d} missing standard meals: {list(jco_menu.keys())}")

    def test_03_no_invented_foods_constraint(self):
        """Verify recommendations strictly contain only items present in the official mess menu."""
        test_dates = [
            ('Monday', '2026-09-07'),
            ('Wednesday', '2026-09-09'),
            ('Friday', '2026-09-11'),
            ('Sunday', '2026-09-13')
        ]
        for day_name, date_str in test_dates:
            # Soldier OR
            soldier_or = {'rank': 'Havildar', 'actual_weight_kg': 72, 'height_cm': 172, 'age': 28, 'bmi': 24.3, 'weight_category': 'NORMAL'}
            diet_or = generate_personalized_diet(soldier_or, goal='Overall Fitness', report_date=date_str)
            self.assertEqual(diet_or['day_of_week'], day_name)
            valid_or_items = {food.strip().lower() for meal_items in OR_MESS_SCHEDULE.get(day_name, {}).values() for food in meal_items}
            
            for meal_name, items_list in diet_or['mess_nutrition_plan'].items():
                for item in items_list:
                    self.assertIn(item['food_item'].strip().lower(), valid_or_items,
                                  f"Invented food '{item['food_item']}' found in OR mess plan on {day_name}")

            # Soldier JCO
            soldier_jco = {'rank': 'Subedar', 'actual_weight_kg': 78, 'height_cm': 175, 'age': 44, 'bmi': 25.5, 'weight_category': 'OVERWEIGHT'}
            diet_jco = generate_personalized_diet(soldier_jco, goal='Weight Loss', report_date=date_str)
            self.assertEqual(diet_jco['day_of_week'], day_name)
            valid_jco_items = {food.strip().lower() for meal_items in JCO_MESS_SCHEDULE.get(day_name, {}).values() for food in meal_items}
            
            for meal_name, items_list in diet_jco['mess_nutrition_plan'].items():
                for item in items_list:
                    self.assertIn(item['food_item'].strip().lower(), valid_jco_items,
                                  f"Invented food '{item['food_item']}' found in JCO mess plan on {day_name}")

    def test_04_fit_vs_unfit_portion_calculations(self):
        """Verify calibrated portion sizes and caloric adjustments between Fit and Unfit/Overweight."""
        # Fit soldier
        fit_soldier = {'rank': 'Sepoy', 'actual_weight_kg': 68, 'ideal_weight_kg': 68, 'height_cm': 172, 'age': 24, 'bmi': 23.0, 'weight_category': 'NORMAL'}
        fit_diet = generate_personalized_diet(fit_soldier, goal='Overall Fitness')

        # Unfit / Overweight soldier
        unfit_soldier = {'rank': 'Sepoy', 'actual_weight_kg': 85, 'ideal_weight_kg': 68, 'height_cm': 172, 'age': 24, 'bmi': 28.7, 'weight_category': 'OVERWEIGHT'}
        unfit_diet = generate_personalized_diet(unfit_soldier, goal='Weight Loss')

        # Overweight target calories should have caloric deficit applied
        self.assertIn('Deficit', unfit_diet['strategy'])
        self.assertIn('daily_targets', unfit_diet)
        self.assertIn('daily_targets', fit_diet)

        # Underweight soldier
        underweight_soldier = {'rank': 'Sepoy', 'actual_weight_kg': 52, 'ideal_weight_kg': 68, 'height_cm': 172, 'age': 24, 'bmi': 17.6, 'weight_category': 'UNDERWEIGHT'}
        under_diet = generate_personalized_diet(underweight_soldier, goal='Overall Fitness')
        self.assertIn('Surplus', under_diet['strategy'])

    def test_05_portion_units(self):
        """Verify all meal items have units specified in grams, pieces, or ml."""
        soldier = {'rank': 'Agniveer', 'actual_weight_kg': 65, 'height_cm': 170, 'age': 21, 'bmi': 22.5}
        diet = generate_personalized_diet(soldier, report_date='2026-09-10')
        for meal_name, items_list in diet['mess_nutrition_plan'].items():
            for it in items_list:
                p = it['portion'].lower()
                has_unit = any(u in p for u in ['g', 'piece', 'ml', 'cup', 'bowl'])
                self.assertTrue(has_unit, f"Item {it['food_item']} lacks explicit unit in '{it['portion']}'")

    def test_06_optional_diet_plan_separation(self):
        """Verify optional diet plan is clearly demarcated from mess plan."""
        soldier = {'rank': 'Naib Subedar', 'actual_weight_kg': 80, 'ideal_weight_kg': 70, 'height_cm': 174, 'age': 40, 'bmi': 26.4}
        diet = generate_personalized_diet(soldier)
        self.assertIn('optional_diet_plan', diet)
        opt = diet['optional_diet_plan']
        self.assertIsInstance(opt, list)
        self.assertGreater(len(opt), 0)
        self.assertIn('item', opt[0])
        self.assertIn('recommendation', opt[0])

    def test_07_upgraded_exercise_drills(self):
        """Verify exercise drills contain sets, reps, duration, frequency, rest, and progression."""
        # Unfit / Overweight
        unfit_soldier = {'rank': 'Havildar', 'actual_weight_kg': 88, 'bmi': 29.5, 'bpet_grade': 'POOR', 'ppt_grade': 'POOR'}
        unfit_plan = generate_personalized_exercise_plan(unfit_soldier, goal='Weight Loss')
        self.assertIn('Conditioning', unfit_plan['title'])
        for ex in unfit_plan['exercises']:
            self.assertIn('sets', ex)
            self.assertIn('reps', ex)
            self.assertIn('duration', ex)
            self.assertIn('frequency', ex)
            self.assertIn('rest', ex)
            self.assertIn('progression_note', ex)

        # Operational Combat Readiness (Fit)
        fit_soldier = {'rank': 'Sepoy', 'actual_weight_kg': 68, 'bmi': 22.5, 'bpet_grade': 'EXCELLENT', 'ppt_grade': 'EXCELLENT'}
        fit_plan = generate_personalized_exercise_plan(fit_soldier, goal='Overall Fitness')
        for ex in fit_plan['exercises']:
            self.assertIn('sets', ex)
            self.assertIn('rest', ex)

    def test_08_medical_safety_filtering(self):
        """Verify safety filtering prevents dangerous drills for low medical category personnel."""
        soldier_knee = {'rank': 'Sepoy', 'has_medical_restriction': True, 'medical_category': 'LMC-KNEE', 'restrictions': 'Knee injury'}
        plan = generate_personalized_exercise_plan(soldier_knee)
        ex_names = [e['exercise'].lower() for e in plan['exercises']]
        self.assertFalse(any('box jump' in n or '5km' in n for n in ex_names), f"Dangerous exercises found: {ex_names}")

    def test_09_api_end_to_end_analysis(self):
        """Verify analyze_personnel_fitness integrates mess nutrition plan."""
        from aiml.fitness_trend.data.db_loader import fetch_personnel_list_for_search
        recs = fetch_personnel_list_for_search(limit=3)
        if recs:
            army_no = recs[0]['army_number']
            result = analyze_personnel_fitness(army_no, regenerate=True, report_date='2026-09-10')
            self.assertTrue(result['success'])
            diet = result['recommendations']['diet']
            self.assertIn('mess_category', diet)
            self.assertIn('mess_nutrition_plan', diet)
            self.assertIn('daily_targets', diet)
            self.assertIn('estimated_intake', diet)
            self.assertIn('optional_diet_plan', diet)
            ex = result['recommendations']['exercise']
            self.assertTrue(any('rest' in x for x in ex['exercises']))

    def test_10_pdf_generation(self):
        """Verify PDF builds successfully with upgraded mess and exercise sections."""
        soldier_features = {
            'army_number': '15150001X',
            'name': 'Suresh Kumar',
            'rank': 'Havildar',
            'company': 'Alpha',
            'section': 'Sec 1',
            'age': 29,
            'service_years': 9,
            'height_cm': 174,
            'actual_weight_kg': 72.0,
            'ideal_weight_kg': 70.0,
            'weight_difference_kg': 2.0,
            'weight_deviation_percent': 2.8,
            'bmi': 23.8,
            'weight_category': 'NORMAL',
            'medical_category': 'SHAPE-1',
            'has_medical_restriction': False,
            'bpet_grade': 'GOOD',
            'ppt_grade': 'GOOD',
            'sports_list': 'Cross Country'
        }
        pred_result = {
            'fitness_score': 82,
            'fitness_category': 'WARRIOR',
            'confidence': 88,
            'model_version': 'v1',
            'predicted_status': 'FIT',
            'strengths': ['Solid BPET score', 'SHAPE-1 Medical Clearance'],
            'improvements': ['Enhance Core Endurance']
        }
        diet = generate_personalized_diet(soldier_features, report_date='2026-09-10')
        exercise = generate_personalized_exercise_plan(soldier_features)
        recommendations = {
            'diet': diet,
            'exercise': exercise,
            'medical_notice': {'is_restricted': False, 'alert_class': 'success', 'title': 'Cleared', 'message': 'SHAPE-1'}
        }
        progression = {
            'milestones': [
                {'period': 'Baseline', 'days': 0, 'weight_kg': 72.0, 'bmi': 23.8, 'fitness_score': 82, 'badge': 'secondary'},
                {'period': '30-Day', 'days': 30, 'weight_kg': 71.5, 'bmi': 23.6, 'fitness_score': 85, 'badge': 'info'},
                {'period': '60-Day', 'days': 60, 'weight_kg': 70.8, 'bmi': 23.4, 'fitness_score': 88, 'badge': 'primary'},
                {'period': '90-Day', 'days': 90, 'weight_kg': 70.0, 'bmi': 23.1, 'fitness_score': 90, 'badge': 'success'}
            ],
            'chart_data': {
                'labels': ['Day 0', 'Day 30', 'Day 60', 'Day 90'],
                'actual_series': [72.0, None, None, None],
                'projected_series': [72.0, 71.5, 70.8, 70.0],
                'weight_series': [72.0, 71.5, 70.8, 70.0],
                'score_series': [82, 85, 88, 90],
                'bmi_series': [23.8, 23.6, 23.4, 23.1]
            }
        }

        # Generate English PDF
        pdf_stream = generate_multilingual_fitness_pdf(
            soldier_features=soldier_features,
            prediction_result=pred_result,
            recommendations=recommendations,
            progression_data=progression,
            language='en'
        )
        self.assertIsNotNone(pdf_stream)
        pdf_bytes = pdf_stream.getvalue()
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'), "Output must be a valid PDF binary")

    def test_11_multilingual_pdf_sample(self):
        """Verify PDF compiles in a non-English language (Hindi) with the updated template."""
        soldier_features = {
            'army_number': '15150002Y',
            'name': 'Rajesh Singh',
            'rank': 'Subedar',
            'company': 'Bravo',
            'section': 'Sec 2',
            'age': 42,
            'service_years': 21,
            'height_cm': 176,
            'actual_weight_kg': 79.0,
            'ideal_weight_kg': 72.0,
            'weight_difference_kg': 7.0,
            'weight_deviation_percent': 9.7,
            'bmi': 25.5,
            'weight_category': 'OVERWEIGHT',
            'medical_category': 'SHAPE-1',
            'has_medical_restriction': False,
            'bpet_grade': 'SATISFACTORY',
            'ppt_grade': 'SATISFACTORY',
            'sports_list': 'Volleyball'
        }
        pred_result = {
            'fitness_score': 74,
            'fitness_category': 'ACTIVE',
            'confidence': 85,
            'model_version': 'v1',
            'predicted_status': 'MONITOR',
            'strengths': ['Strong service experience'],
            'improvements': ['Caloric deficit required']
        }
        diet = generate_personalized_diet(soldier_features, report_date='2026-09-10')
        exercise = generate_personalized_exercise_plan(soldier_features)
        recommendations = {
            'diet': diet,
            'exercise': exercise,
            'medical_notice': {'is_restricted': False, 'alert_class': 'info', 'title': 'Guidelines', 'message': 'SHAPE-1'}
        }
        progression = {
            'milestones': [
                {'period': 'Baseline', 'days': 0, 'weight_kg': 79.0, 'bmi': 25.5, 'fitness_score': 74, 'badge': 'secondary'},
                {'period': '30-Day', 'days': 30, 'weight_kg': 77.5, 'bmi': 25.0, 'fitness_score': 78, 'badge': 'info'},
                {'period': '60-Day', 'days': 60, 'weight_kg': 75.0, 'bmi': 24.2, 'fitness_score': 82, 'badge': 'primary'},
                {'period': '90-Day', 'days': 90, 'weight_kg': 72.5, 'bmi': 23.4, 'fitness_score': 85, 'badge': 'success'}
            ],
            'chart_data': {
                'labels': ['Day 0', 'Day 30', 'Day 60', 'Day 90'],
                'actual_series': [79.0, None, None, None],
                'projected_series': [79.0, 77.5, 75.0, 72.5],
                'weight_series': [79.0, 77.5, 75.0, 72.5],
                'score_series': [74, 78, 82, 85],
                'bmi_series': [25.5, 25.0, 24.2, 23.4]
            }
        }

        # Generate Hindi PDF
        pdf_stream = generate_multilingual_fitness_pdf(
            soldier_features=soldier_features,
            prediction_result=pred_result,
            recommendations=recommendations,
            progression_data=progression,
            language='hi'
        )
        self.assertIsNotNone(pdf_stream)
        pdf_bytes = pdf_stream.getvalue()
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    def test_12_weekly_schedule_and_30d_roadmap(self):
        """Verify 30-day nutrition plan includes full Monday to Sunday weekly schedule and 4-week roadmap."""
        soldier = {'rank': 'Havildar', 'actual_weight_kg': 75, 'height_cm': 172, 'age': 30, 'bmi': 25.3}
        diet = generate_personalized_diet(soldier, goal='Overall Fitness', report_date='2026-09-10')

        # 1. Weekly schedule contains all 7 days Monday to Sunday
        self.assertIn('weekly_schedule', diet)
        self.assertIn('weekly_schedule_list', diet)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for d in days:
            self.assertIn(d, diet['weekly_schedule'])
            day_data = diet['weekly_schedule'][d]
            self.assertEqual(day_data['day'], d)
            self.assertIn('meals', day_data)
            self.assertIn('sample_menu', day_data)
            self.assertGreater(len(day_data['meals']), 0)
            self.assertGreater(len(day_data['sample_menu']), 0)

        # 2. 30-Day Tactical Roadmap has 4 weeks
        self.assertIn('roadmap_30d', diet)
        roadmap = diet['roadmap_30d']
        self.assertEqual(len(roadmap), 4)
        for w in roadmap:
            self.assertIn('week', w)
            self.assertIn('phase', w)
            self.assertIn('focus', w)
            self.assertIn('mess_strategy', w)
            self.assertIn('milestone', w)

        # 3. Structured report passes weekly schedule and roadmap
        pred = {'fitness_score': 82, 'category': 'FIT'}
        prog = {'milestones': []}
        report = build_structured_fitness_report(soldier, pred, {'diet': diet, 'exercise': {}}, prog)
        self.assertIn('weekly_schedule', report['nutrition'])
        self.assertIn('roadmap_30d', report['nutrition'])
        self.assertEqual(len(report['nutrition']['roadmap_30d']), 4)


if __name__ == '__main__':
    unittest.main()
