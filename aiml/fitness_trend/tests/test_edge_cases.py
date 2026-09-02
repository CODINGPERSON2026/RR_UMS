"""
Unit tests for Dirty Data, Edge Cases, Multi-Sport Aggregation, and Safety Blocking.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from aiml.fitness_trend.data.data_validator import validate_and_clean_soldier_data, clean_bpet_ppt_grading, calculate_age_from_dob
from aiml.fitness_trend.data.data_aggregator import aggregate_sports_for_personnel
from aiml.fitness_trend.recommendations.safety import filter_unsafe_exercises


class TestEdgeCasesAndDirtyData(unittest.TestCase):

    def test_dirty_bpet_ppt_variations(self):
        grade, score = clean_bpet_ppt_grading("EX")
        self.assertEqual(grade, "EXCELLENT")
        self.assertEqual(score, 100)

        grade, score = clean_bpet_ppt_grading("EXELENT")
        self.assertEqual(grade, "EXCELLENT")

        grade, score = clean_bpet_ppt_grading("GOOD")
        self.assertEqual(grade, "GOOD")
        self.assertEqual(score, 80)

        grade, score = clean_bpet_ppt_grading("G0OOD")
        self.assertEqual(grade, "GOOD")

        grade, score = clean_bpet_ppt_grading("SAT")
        self.assertEqual(grade, "SATISFACTORY")
        self.assertEqual(score, 60)

        grade, score = clean_bpet_ppt_grading("LMC")
        self.assertEqual(grade, "LMC")
        self.assertEqual(score, 40)

        grade, score = clean_bpet_ppt_grading("NA")
        self.assertIsNone(grade)
        self.assertIsNone(score)

    def test_dob_edge_cases(self):
        # Normal DOB (1995-05-15) -> valid integer age
        age = calculate_age_from_dob("1995-05-15")
        self.assertIsNotNone(age)
        self.assertTrue(25 <= age <= 40)

        # Future DOB -> None
        self.assertIsNone(calculate_age_from_dob("2035-01-01"))
        # Invalid string -> None
        self.assertIsNone(calculate_age_from_dob("not-a-date"))
        self.assertIsNone(calculate_age_from_dob(None))

    def test_source_priority_rule_and_dirty_values(self):
        # Case 1: weight_info has valid height & weight, personnel has typo (22.0)
        p_row = {
            'army_number': '15700000A',
            'height': 22.0,  # Typo in personnel
            'weight': 173.0, # Typo in personnel
            'date_of_birth': '1996-01-01'
        }
        w_row = {
            'army_number': '15700000A',
            'height': 173.0,
            'actual_weight': 73.0,
            'age': 30
        }
        res = validate_and_clean_soldier_data(p_row, w_row)
        self.assertEqual(res['height_cm'], 173.0)
        self.assertEqual(res['actual_weight_kg'], 73.0)
        self.assertTrue(res['is_sufficient_for_prediction'])

        # Case 2: weight_info is missing, fallback to valid personnel values
        p_row2 = {
            'army_number': '15700001B',
            'height': 170.0,
            'weight': 68.0,
            'date_of_birth': '1998-05-20'
        }
        w_row2 = None
        res2 = validate_and_clean_soldier_data(p_row2, w_row2)
        self.assertEqual(res2['height_cm'], 170.0)
        self.assertEqual(res2['actual_weight_kg'], 68.0)

    def test_multi_sports_aggregation_single_row(self):
        # Soldier with 4 sports records across different categories
        sports_rows = [
            {'sport_name': 'Football', 'sport_type': 'Football'},
            {'sport_name': 'Volleyball', 'sport_type': 'Volleyball'},
            {'sport_name': 'Swimming', 'sport_type': 'Other'},
            {'sport_name': 'Boxing', 'sport_type': 'Other'}
        ]
        agg = aggregate_sports_for_personnel(sports_rows)
        self.assertEqual(agg['sport_count'], 4)
        self.assertEqual(agg['has_sport'], 1)
        self.assertEqual(agg['team_sport_indicator'], 1)
        self.assertEqual(agg['water_sport_indicator'], 1)
        self.assertEqual(agg['combat_sport_indicator'], 1)
        self.assertEqual(agg['physical_activity_level'], 'High')

    def test_safety_filter_blocks_unsafe_exercises(self):
        soldier_features = {
            'has_medical_restriction': 1,
            'is_low_medical_category': 1,
            'contraindicated_categories': ['spine_back', 'knee_lower_limb'],
            'contraindicated_exercises': ['Heavy Deadlifts', 'Deep Barbell Squats']
        }
        candidate_exercises = [
            {'exercise': 'Heavy Deadlifts', 'type': 'heavy_lifting', 'sets': 3},
            {'exercise': 'Deep Barbell Squats', 'type': 'deep_squat', 'sets': 3},
            {'exercise': 'Standard Push-Ups', 'type': 'upper_push', 'sets': 3, 'intensity': 'Moderate'}
        ]
        safe_list, blocked_list = filter_unsafe_exercises(candidate_exercises, soldier_features)
        
        # Deadlifts and Squats must be in blocked list
        blocked_names = [b['exercise'] for b in blocked_list]
        self.assertIn('Heavy Deadlifts', blocked_names)
        self.assertIn('Deep Barbell Squats', blocked_names)

        # Safe list must contain Push-ups and injected spine-safe rehab routines
        safe_names = [s['exercise'] for s in safe_list]
        self.assertIn('Standard Push-Ups', safe_names)
        self.assertTrue(any('Bird-Dog' in name for name in safe_names))


if __name__ == '__main__':
    unittest.main()
