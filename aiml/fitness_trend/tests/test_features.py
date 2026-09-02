"""
Unit tests for Feature Engineering, BMI, Ideal Weight, Sports, and Medical modules.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from aiml.fitness_trend.features.bmi import calculate_bmi, get_bmi_category
from aiml.fitness_trend.features.ideal_weight import calculate_ideal_weight_and_deviation, parse_age_range, get_ideal_weight_from_table
from aiml.fitness_trend.features.sports_features import extract_sports_features
from aiml.fitness_trend.features.medical_features import extract_medical_features
from aiml.fitness_trend.features.feature_engineering import generate_features_for_soldier, score_to_fitness_category


class TestFeatureEngineering(unittest.TestCase):

    def setUp(self):
        self.mock_ideal_weights = [
            {'id': 1, 'height_cm': 168, 'age_range': '18-22', 'ideal_weight_kg': 58.0},
            {'id': 2, 'height_cm': 170, 'age_range': '18-22', 'ideal_weight_kg': 60.0},
            {'id': 3, 'height_cm': 172, 'age_range': '18-22', 'ideal_weight_kg': 62.0},
            {'id': 4, 'height_cm': 170, 'age_range': '23-27', 'ideal_weight_kg': 63.0},
            {'id': 5, 'height_cm': 172, 'age_range': '23-27', 'ideal_weight_kg': 65.0},
            {'id': 6, 'height_cm': 170, 'age_range': '28-32', 'ideal_weight_kg': 65.0},
            {'id': 7, 'height_cm': 172, 'age_range': '28-32', 'ideal_weight_kg': 67.0},
        ]

    def test_bmi_calculation_valid(self):
        # 70 kg, 175 cm -> 70 / (1.75^2) = 22.86
        bmi = calculate_bmi(70.0, 175.0)
        self.assertIsNotNone(bmi)
        self.assertEqual(bmi, 22.86)
        cat, color, badge = get_bmi_category(bmi)
        self.assertEqual(cat, "Normal (Ideal)")
        self.assertEqual(badge, "success")

    def test_bmi_division_by_zero_and_none(self):
        self.assertIsNone(calculate_bmi(None, 175.0))
        self.assertIsNone(calculate_bmi(70.0, None))
        self.assertIsNone(calculate_bmi(0.0, 175.0))
        self.assertIsNone(calculate_bmi(70.0, 0.0))
        self.assertIsNone(calculate_bmi(-70.0, 175.0))
        self.assertIsNone(calculate_bmi(70.0, -175.0))

    def test_bmi_unrealistic_bounds(self):
        # Stature 22 cm is invalid
        self.assertIsNone(calculate_bmi(70.0, 22.0))
        # Weight 200 kg is invalid
        self.assertIsNone(calculate_bmi(200.0, 175.0))

    def test_age_range_parser(self):
        min_a, max_a = parse_age_range('18-22')
        self.assertEqual(min_a, 18)
        self.assertEqual(max_a, 22)
        
        min_a2, max_a2 = parse_age_range('48-70')
        self.assertEqual(min_a2, 48)
        self.assertEqual(max_a2, 70)

    def test_ideal_weight_exact_match(self):
        # 170 cm, 25 yrs (in 23-27 range) -> 63.0 kg
        iw = get_ideal_weight_from_table(170.0, 25, self.mock_ideal_weights)
        self.assertEqual(iw, 63.0)

    def test_ideal_weight_closest_height(self):
        # 171 cm (closest to 170 / 172), 24 yrs -> closest in 23-27
        iw = get_ideal_weight_from_table(171.0, 24, self.mock_ideal_weights)
        self.assertIn(iw, [63.0, 65.0])

    def test_ideal_weight_deviation(self):
        # 70 kg actual, 63.0 kg ideal -> +7.0 kg (+11.11% Overweight)
        res = calculate_ideal_weight_and_deviation(170.0, 70.0, 25, self.mock_ideal_weights)
        self.assertEqual(res['ideal_weight_kg'], 63.0)
        self.assertEqual(res['weight_difference_kg'], 7.0)
        self.assertEqual(res['weight_deviation_percent'], 11.11)
        self.assertIn('Overweight', res['weight_status'])

    def test_sports_feature_extraction(self):
        mock_sports = [
            {'sport_name': 'Football', 'sport_type': 'Football'},
            {'sport_name': 'Volleyball', 'sport_type': 'Volleyball'},
            {'sport_name': 'Swimming', 'sport_type': 'Other'}
        ]
        res = extract_sports_features(mock_sports)
        self.assertEqual(res['sport_count'], 3)
        self.assertEqual(res['has_sport'], 1)
        self.assertEqual(res['team_sport_indicator'], 1)
        self.assertEqual(res['water_sport_indicator'], 1)
        self.assertGreaterEqual(res['sports_readiness_score'], 10.0)

    def test_medical_features_spine_detection(self):
        soldier_data = {
            'is_lmc': True,
            'medical_problem': 'PIVD L4-L5 Disc herniation',
            'restrictions': 'Forward Bending PPG, Heavy Weight Lifting'
        }
        res = extract_medical_features(soldier_data)
        self.assertEqual(res['has_medical_restriction'], 1)
        self.assertEqual(res['is_low_medical_category'], 1)
        self.assertIn('spine_back', res['contraindicated_categories'])
        self.assertTrue(len(res['contraindicated_exercises']) > 0)
        self.assertEqual(res['clearance_status'], 'Conditional / Restricted')

    def test_score_to_fitness_category(self):
        self.assertEqual(score_to_fitness_category(92.0), "EXCELLENT")
        self.assertEqual(score_to_fitness_category(76.0), "GOOD")
        self.assertEqual(score_to_fitness_category(62.0), "AVERAGE")
        self.assertEqual(score_to_fitness_category(42.0), "NEEDS_IMPROVEMENT")


if __name__ == '__main__':
    unittest.main()
