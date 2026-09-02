"""
Unit tests for AI Prediction Engine, Confidence Scoring, and Explainability.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from aiml.fitness_trend.prediction.predictor import predict_soldier_fitness, get_model_info
from aiml.fitness_trend.prediction.confidence import extract_explainable_factors, compute_prediction_confidence


class TestPredictionEngine(unittest.TestCase):

    def setUp(self):
        self.mock_healthy_features = {
            'army_number': '15744604X',
            'name': 'Test Soldier 1',
            'rank': 'Signal Man',
            'company': 'COMN Company',
            'age': 28,
            'height_cm': 172.0,
            'actual_weight_kg': 66.0,
            'ideal_weight_kg': 65.0,
            'weight_difference_kg': 1.0,
            'weight_deviation_percent': 1.54,
            'weight_status': 'Ideal Weight',
            'bmi': 22.31,
            'bmi_category': 'Normal (Ideal)',
            'service_years': 6.0,
            'bpet_grade': 'EXCELLENT',
            'bpet_score': 100.0,
            'ppt_grade': 'EXCELLENT',
            'ppt_score': 100.0,
            'sport_count': 2,
            'has_sport': 1,
            'sports_list': 'Football, Volleyball',
            'primary_sport': 'Football',
            'team_sport_indicator': 1,
            'individual_sport_indicator': 0,
            'endurance_sport_indicator': 0,
            'strength_sport_indicator': 0,
            'combat_sport_indicator': 0,
            'water_sport_indicator': 0,
            'sports_readiness_score': 10.0,
            'has_medical_restriction': 0,
            'is_low_medical_category': 0,
            'medical_risk_penalty': 0.0,
            'contraindicated_categories': [],
            'contraindicated_exercises': [],
            'is_sufficient_for_prediction': True,
            'ground_truth_score': 95.0,
            'ground_truth_category': 'EXCELLENT'
        }

        self.mock_restricted_features = {
            'army_number': '15677440X',
            'name': 'Test Soldier 2',
            'rank': 'Havildar',
            'company': 'HQ company',
            'age': 42,
            'height_cm': 168.0,
            'actual_weight_kg': 84.0,
            'ideal_weight_kg': 66.0,
            'weight_difference_kg': 18.0,
            'weight_deviation_percent': 27.27,
            'weight_status': 'Significantly Overweight (+27.27%)',
            'bmi': 29.76,
            'bmi_category': 'Overweight',
            'service_years': 18.0,
            'bpet_grade': 'SATISFACTORY',
            'bpet_score': 60.0,
            'ppt_grade': 'SATISFACTORY',
            'ppt_score': 60.0,
            'sport_count': 0,
            'has_sport': 0,
            'sports_list': 'None',
            'primary_sport': 'None',
            'team_sport_indicator': 0,
            'individual_sport_indicator': 0,
            'endurance_sport_indicator': 0,
            'strength_sport_indicator': 0,
            'combat_sport_indicator': 0,
            'water_sport_indicator': 0,
            'sports_readiness_score': 0.0,
            'has_medical_restriction': 1,
            'is_low_medical_category': 1,
            'medical_risk_penalty': 20.0,
            'contraindicated_categories': ['spine_back'],
            'contraindicated_exercises': ['Heavy Deadlifts'],
            'is_sufficient_for_prediction': True,
            'ground_truth_score': 45.0,
            'ground_truth_category': 'NEEDS_IMPROVEMENT'
        }

    def test_predict_healthy_soldier(self):
        res = predict_soldier_fitness(self.mock_healthy_features)
        self.assertIn(res['prediction_status'], ['SUCCESS', 'RULE_BASED_BASELINE', 'FALLBACK_BASELINE'])
        self.assertGreaterEqual(res['fitness_score'], 80.0)
        self.assertIn(res['fitness_category'], ['EXCELLENT', 'GOOD'])
        self.assertGreaterEqual(res['confidence_score'], 70.0)
        self.assertTrue(len(res['strengths']) > 0)

    def test_predict_restricted_soldier(self):
        res = predict_soldier_fitness(self.mock_restricted_features)
        self.assertIn(res['prediction_status'], ['SUCCESS', 'RULE_BASED_BASELINE', 'FALLBACK_BASELINE'])
        self.assertLessEqual(res['fitness_score'], 75.0)
        self.assertTrue(len(res['improvements']) > 0)

    def test_insufficient_data_handling(self):
        insufficient = dict(self.mock_healthy_features)
        insufficient['is_sufficient_for_prediction'] = False
        res = predict_soldier_fitness(insufficient)
        self.assertEqual(res['prediction_status'], 'INSUFFICIENT_DATA')
        self.assertIsNone(res['fitness_score'])
        self.assertEqual(res['category_label'], 'Insufficient Data')

    def test_model_info_retrieval(self):
        info = get_model_info()
        self.assertIsInstance(info, dict)
        self.assertTrue(info.get('available'))


if __name__ == '__main__':
    unittest.main()
