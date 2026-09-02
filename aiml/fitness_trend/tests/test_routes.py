"""
Integration tests for Flask Blueprint Routes, API endpoints, and PDF generation.
"""

import unittest
import sys
import os
import json
import jwt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app import app
from middleware import JWT_SECRET, JWT_ALGO
from aiml.fitness_trend.reports.fitness_report import generate_fitness_pdf_report


class TestFitnessRoutes(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Create valid mock auth token
        payload = {
            'username': 'CO_TEST',
            'name': 'Commanding Officer',
            'role': 'CO',
            'company': 'COMN Company'
        }
        self.token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

    def test_fitness_dashboard_unauthorized_redirect(self):
        # Without token, should redirect to /admin_login
        response = self.client.get('/fitness/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin_login', response.headers.get('Location', ''))

    def test_fitness_dashboard_authorized(self):
        self.client.set_cookie('token', self.token)
        response = self.client.get('/fitness/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AI/ML Operational Readiness', response.data)

    def test_api_search_personnel(self):
        self.client.set_cookie('token', self.token)
        response = self.client.get('/fitness/api/personnel-list?q=')
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertTrue(json_data.get('success'))
        self.assertIsInstance(json_data.get('data'), list)

    def test_api_model_info(self):
        self.client.set_cookie('token', self.token)
        response = self.client.get('/fitness/api/model-info')
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertTrue(json_data.get('success'))
        self.assertTrue(json_data['data'].get('available'))

    def test_api_analyze_personnel_existing(self):
        self.client.set_cookie('token', self.token)
        # Search a real personnel to get an army number
        search_res = self.client.get('/fitness/api/personnel-list?limit=1')
        search_json = json.loads(search_res.data)
        if search_json.get('data') and len(search_json['data']) > 0:
            army_no = search_json['data'][0]['army_number']
            res = self.client.post('/fitness/api/analyze', json={
                'army_number': army_no,
                'goal': 'Overall Fitness'
            })
            self.assertEqual(res.status_code, 200)
            json_data = json.loads(res.data)
            self.assertTrue(json_data.get('success'))
            self.assertIn('soldier', json_data)
            self.assertIn('prediction', json_data)
            self.assertIn('recommendations', json_data)
            self.assertIn('progression', json_data)

    def test_api_analyze_non_existent_soldier(self):
        self.client.set_cookie('token', self.token)
        res = self.client.post('/fitness/api/analyze', json={
            'army_number': 'NON_EXISTENT_ARMY_NO_99999'
        })
        self.assertEqual(res.status_code, 404)
        json_data = json.loads(res.data)
        self.assertFalse(json_data.get('success'))

    def test_pdf_report_binary_compilation(self):
        mock_soldier = {
            'army_number': 'JC393919L',
            'name': 'HANSRAM GURJAR',
            'rank': 'Naib Subedar',
            'trade': 'jene',
            'company': 'COMN Company',
            'section': 'IT',
            'age': 33,
            'service_years': 13.5,
            'height_cm': 175.0,
            'actual_weight_kg': 73.0,
            'ideal_weight_kg': 67.0,
            'weight_difference_kg': 6.0,
            'weight_deviation_percent': 8.96,
            'weight_status': 'Authorized Limit (+8.96%)',
            'bmi': 23.84,
            'bmi_category': 'Normal (Ideal)',
            'bpet_grade': 'GOOD',
            'ppt_grade': 'GOOD',
            'sports_list': 'Volleyball',
            'sport_count': 1,
            'physical_activity_level': 'Moderate',
            'has_medical_restriction': 0
        }
        mock_pred = {
            'fitness_score': 82.5,
            'fitness_category': 'GOOD',
            'category_label': 'Good Fitness',
            'confidence_score': 88.0,
            'model_version': 'v1',
            'algorithm': 'GradientBoostingClassifier',
            'strengths': ['Solid BPET Performance', 'Optimal BMI'],
            'improvements': ['Minor weight adjustment towards ideal']
        }
        mock_rec = {
            'medical_notice': {'title': 'Medically Cleared (SHAPE-1)', 'message': 'Soldier cleared for tactical PT.'},
            'diet': {
                'target_calories': 2400,
                'strategy': 'Maintenance conditioning',
                'hydration_liters': 3.6,
                'macros': {'protein_grams': 120, 'carb_grams': 290, 'fat_grams': 60, 'protein_pct': 20, 'carb_pct': 55, 'fat_pct': 25}
            },
            'exercise': {
                'title': 'Tactical Regimen',
                'exercises': [{'exercise': '5km Interval Run', 'sets': 4, 'reps': '500m', 'duration': '30m', 'frequency': '3 days'}]
            }
        }
        mock_prog = {
            'milestones': [
                {'period': 'Current', 'weight_kg': 73.0, 'bmi': 23.84, 'fitness_score': 82.5},
                {'period': '30 Days', 'weight_kg': 72.0, 'bmi': 23.51, 'fitness_score': 86.0},
                {'period': '60 Days', 'weight_kg': 70.5, 'bmi': 23.02, 'fitness_score': 89.0},
                {'period': '90 Days', 'weight_kg': 69.0, 'bmi': 22.53, 'fitness_score': 92.0}
            ]
        }
        pdf_stream = generate_fitness_pdf_report(mock_soldier, mock_pred, mock_rec, mock_prog)
        self.assertIsNotNone(pdf_stream)
        pdf_bytes = pdf_stream.getvalue()
        self.assertTrue(len(pdf_bytes) > 500)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))


if __name__ == '__main__':
    unittest.main()
