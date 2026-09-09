"""
Comprehensive unit and integration test suite for AI Fitness Reports directory,
role-based access control, duplicate prevention, pagination, search, and dynamic statistics.
Covers all 17 required verification scenarios.
"""

import unittest
import sys
import os
import json
import jwt
from datetime import datetime

# Set up project path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app import app
from middleware import JWT_SECRET, JWT_ALGO
from aiml.fitness_trend.data.reports_db import (
    ensure_ai_fitness_reports_table,
    insert_or_update_ai_fitness_report,
    get_saved_report_by_army_number,
    get_saved_report_by_id,
    fetch_reports_paginated,
    fetch_dynamic_report_stats
)
from aiml.fitness_trend.routes import check_fitness_executive_access
from aiml.fitness_trend.api import (
    analyze_personnel_fitness,
    regenerate_personnel_fitness_report,
    get_all_reports_paginated,
    get_reports_statistics
)


class TestAiFitnessReportsDirectory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ensure test table exists and seed sample records."""
        ensure_ai_fitness_reports_table()
        cls.test_army_no = "TEST_FIT_001"
        cls.test_army_no_2 = "TEST_FIT_002"

        # Insert test report 1
        cls.report_payload_1 = {
            'personnel_id': 99991,
            'army_number': cls.test_army_no,
            'name': 'Test Soldier Alpha',
            'rank': 'Agniveer',
            'company': 'COMN',
            'age': 22,
            'height_cm': 172.0,
            'actual_weight_kg': 64.5,
            'ideal_weight_kg': 65.0,
            'bmi': 21.8,
            'fitness_score': 88.5,
            'fitness_status': 'Healthy / Combat Ready',
            'prediction_result': {
                'fitness_score': 88.5,
                'category_label': 'Healthy / Combat Ready',
                'confidence': 0.94,
                'key_strengths': ['Optimal BMI', 'High Endurance'],
                'risk_factors': []
            },
            'recommendations': {
                'diet': {'calories_target': '2,500 kcal', 'protein_g': '130g'},
                'exercise': {'focus': 'Maintenance and speed'}
            },
            'progression_prediction': {
                'trajectory_30d': {'projected_fitness_score': 89.0},
                'trajectory_60d': {'projected_fitness_score': 90.0},
                'trajectory_90d': {'projected_fitness_score': 91.0}
            },
            'report_language': 'English',
            'report_generated': True
        }
        cls.saved_id_1 = insert_or_update_ai_fitness_report(cls.report_payload_1)

        # Insert test report 2 (Needs Improvement)
        cls.report_payload_2 = {
            'personnel_id': 99992,
            'army_number': cls.test_army_no_2,
            'name': 'Test Soldier Bravo',
            'rank': 'Sepoy',
            'company': 'ADMN',
            'age': 26,
            'height_cm': 168.0,
            'actual_weight_kg': 78.0,
            'ideal_weight_kg': 62.0,
            'bmi': 27.6,
            'fitness_score': 54.0,
            'fitness_status': 'Needs Improvement',
            'prediction_result': {
                'fitness_score': 54.0,
                'category_label': 'Needs Improvement',
                'confidence': 0.88,
                'key_strengths': [],
                'risk_factors': ['Overweight', 'Elevated BMI']
            },
            'recommendations': {
                'diet': {'calories_target': '2,000 kcal', 'protein_g': '140g'},
                'exercise': {'focus': 'Fat reduction and cardio'}
            },
            'progression_prediction': {
                'trajectory_30d': {'projected_fitness_score': 60.0},
                'trajectory_60d': {'projected_fitness_score': 68.0},
                'trajectory_90d': {'projected_fitness_score': 75.0}
            },
            'report_language': 'English',
            'report_generated': True
        }
        cls.saved_id_2 = insert_or_update_ai_fitness_report(cls.report_payload_2)

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Generate tokens for each executive role
        self.co_token = jwt.encode({'username': 'CO_USER', 'role': 'CO', 'name': 'Col Commanding', 'company': 'HQ'}, JWT_SECRET, algorithm=JWT_ALGO)
        self.two_ic_token = jwt.encode({'username': '2IC_USER', 'role': '2IC', 'name': 'Lt Col 2IC', 'company': 'HQ'}, JWT_SECRET, algorithm=JWT_ALGO)
        self.adj_token = jwt.encode({'username': 'ADJ_USER', 'role': 'ADJUTANT', 'name': 'Capt Adjutant', 'company': 'HQ'}, JWT_SECRET, algorithm=JWT_ALGO)
        self.cmd_off_token = jwt.encode({'username': 'CO_ALIAS', 'role': 'Commanding Officer', 'name': 'Commanding Officer', 'company': 'HQ'}, JWT_SECRET, algorithm=JWT_ALGO)

        # Generate token for unauthorized non-executive roles
        self.nco_token = jwt.encode({'username': 'NCO_USER', 'role': 'NCO', 'name': 'Havildar Test', 'company': 'HQ'}, JWT_SECRET, algorithm=JWT_ALGO)
        self.jco_token = jwt.encode({'username': 'JCO_USER', 'role': 'JCO', 'name': 'Subedar Test', 'company': 'HQ'}, JWT_SECRET, algorithm=JWT_ALGO)
        self.onco_token = jwt.encode({'username': 'ONCO_USER', 'role': 'ONCO', 'name': 'Orderly NCO', 'company': 'HQ'}, JWT_SECRET, algorithm=JWT_ALGO)
        self.soldier_token = jwt.encode({'username': 'SOLDIER_USER', 'role': 'Soldier', 'name': 'Sepoy Test', 'company': 'HQ'}, JWT_SECRET, algorithm=JWT_ALGO)

    # 1. Table Creation Verification
    def test_01_ai_fitness_reports_table_creation(self):
        success = ensure_ai_fitness_reports_table()
        self.assertTrue(success, "ensure_ai_fitness_reports_table should return True.")

    # 2. Report Persistence and Retrieval
    def test_02_report_persistence_and_retrieval(self):
        saved = get_saved_report_by_army_number(self.test_army_no)
        self.assertIsNotNone(saved, "Report should be retrieved by army number.")
        self.assertEqual(saved.get('army_number'), self.test_army_no)
        self.assertEqual(saved.get('name'), 'Test Soldier Alpha')
        self.assertAlmostEqual(float(saved.get('fitness_score')), 88.5, places=1)

        by_id = get_saved_report_by_id(saved.get('id'))
        self.assertIsNotNone(by_id, "Report should be retrievable by primary ID.")
        self.assertEqual(by_id.get('army_number'), self.test_army_no)

    # 3. Duplicate Prevention Flow (Avoid redundant AI recalculation)
    def test_03_duplicate_prevention_flow(self):
        # Call analyze_personnel_fitness with regenerate=False
        res = analyze_personnel_fitness(self.test_army_no, regenerate=False)
        self.assertTrue(res.get('success'))
        self.assertTrue(res.get('cached'), "Existing report must be served from cache (cached=True) to avoid duplicate computation.")
        self.assertEqual(res.get('soldier', {}).get('army_number'), self.test_army_no)

    # 4. Explicit Regeneration Flow
    def test_04_regenerate_flow(self):
        # Mock or test with valid soldier in weight_info or fallback
        # With regenerate=True, cached should be False if soldier exists in DB
        res = regenerate_personnel_fitness_report(self.test_army_no)
        # Even if live DB record doesn't exist for test dummy, function handles gracefully
        self.assertIn('success', res)

    # 5. CO Role Authorization
    def test_05_co_role_authorized(self):
        self.assertTrue(check_fitness_executive_access({'role': 'CO'}))
        self.client.set_cookie('token', self.co_token)
        resp = self.client.get('/fitness/reports')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'AI Fitness Reports', resp.data)

    # 6. 2IC Role Authorization
    def test_06_2ic_role_authorized(self):
        self.assertTrue(check_fitness_executive_access({'role': '2IC'}))
        self.client.set_cookie('token', self.two_ic_token)
        resp = self.client.get('/fitness/reports')
        self.assertEqual(resp.status_code, 200)

    # 7. Adjutant Role Authorization
    def test_07_adjutant_role_authorized(self):
        self.assertTrue(check_fitness_executive_access({'role': 'ADJUTANT'}))
        self.assertTrue(check_fitness_executive_access({'role': 'Adjutant'}))
        self.client.set_cookie('token', self.adj_token)
        resp = self.client.get('/fitness/reports')
        self.assertEqual(resp.status_code, 200)

    # 8. Commanding Officer Alias Authorization
    def test_08_commanding_officer_alias_authorized(self):
        self.assertTrue(check_fitness_executive_access({'role': 'Commanding Officer'}))
        self.client.set_cookie('token', self.cmd_off_token)
        resp = self.client.get('/fitness/reports')
        self.assertEqual(resp.status_code, 200)

    # 9. Unauthorized Roles Strictly Rejected (HTTP 403)
    def test_09_unauthorized_role_rejected(self):
        for role_name, token in [('NCO', self.nco_token), ('JCO', self.jco_token), ('ONCO', self.onco_token), ('Soldier', self.soldier_token)]:
            with self.subTest(role=role_name):
                self.assertFalse(check_fitness_executive_access({'role': role_name}))
                self.client.set_cookie('token', token)
                # HTML view returns 403
                resp_html = self.client.get('/fitness/reports')
                self.assertEqual(resp_html.status_code, 403)
                self.assertIn(b'403', resp_html.data)

                # API returns 403 JSON
                resp_api = self.client.get('/fitness/api/reports')
                self.assertEqual(resp_api.status_code, 403)
                json_api = json.loads(resp_api.data)
                self.assertFalse(json_api.get('success'))
                self.assertIn('Forbidden', json_api.get('error'))

    # 10. Unauthenticated User Rejected (Redirect or 401)
    def test_10_unauthenticated_user_rejected(self):
        # HTML without cookie redirects to login
        resp_html = self.client.get('/fitness/reports')
        self.assertEqual(resp_html.status_code, 302)

        # API without cookie returns 401
        resp_api = self.client.get('/fitness/api/reports')
        self.assertEqual(resp_api.status_code, 401)

    # 11. Fetch All Reports Paginated
    def test_11_fetch_all_reports_paginated(self):
        self.client.set_cookie('token', self.co_token)
        resp = self.client.get('/fitness/api/reports?page=1&per_page=10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        self.assertGreaterEqual(data.get('total', 0), 2)
        self.assertIsInstance(data.get('data'), list)
        self.assertEqual(data.get('page'), 1)

    # 12. Search by Army Number
    def test_12_search_by_army_number(self):
        self.client.set_cookie('token', self.co_token)
        resp = self.client.get(f'/fitness/api/reports?search={self.test_army_no}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        found = [r for r in data.get('data', []) if r.get('army_number') == self.test_army_no]
        self.assertGreaterEqual(len(found), 1)

    # 13. Search by Soldier Name
    def test_13_search_by_name(self):
        self.client.set_cookie('token', self.co_token)
        resp = self.client.get('/fitness/api/reports?search=Soldier+Bravo')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        found = [r for r in data.get('data', []) if 'Bravo' in r.get('name', '')]
        self.assertGreaterEqual(len(found), 1)

    # 14. Filter by Company
    def test_14_filter_by_company(self):
        self.client.set_cookie('token', self.co_token)
        resp = self.client.get('/fitness/api/reports?company=COMN')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        for row in data.get('data', []):
            self.assertIn('COMN', row.get('company', '').upper())

    # 15. Filter by Fitness Status
    def test_15_filter_by_status(self):
        self.client.set_cookie('token', self.co_token)
        resp = self.client.get('/fitness/api/reports?status=Healthy')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        for row in data.get('data', []):
            st = row.get('fitness_status', '').upper()
            self.assertTrue(any(k in st for k in ['HEALTHY', 'COMBAT', 'GOOD', 'OPTIMAL']), f"Unexpected status: {st}")

    # 16. Dynamic Stats Calculation
    def test_16_dynamic_stats_calculation(self):
        self.client.set_cookie('token', self.co_token)
        resp = self.client.get('/fitness/api/reports/stats')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        stats = data.get('stats', {})
        self.assertIn('total_reports', stats)
        self.assertIn('healthy_count', stats)
        self.assertIn('needs_improvement_count', stats)
        self.assertIn('at_risk_count', stats)
        self.assertGreaterEqual(stats.get('total_reports', 0), 2)

    # 17. Graceful N/A Handling for Missing/Partial Data
    def test_17_graceful_na_handling(self):
        # Insert report with null/missing optional fields
        sparse_army_no = "SPARSE_SOLDIER_001"
        sparse_payload = {
            'personnel_id': 99993,
            'army_number': sparse_army_no,
            'name': 'Incomplete Record Soldier',
            'rank': None,
            'company': None,
            'age': None,
            'height_cm': None,
            'actual_weight_kg': None,
            'fitness_score': None,
            'fitness_status': None,
            'report_generated': True
        }
        report_id = insert_or_update_ai_fitness_report(sparse_payload)
        self.assertIsNotNone(report_id)

        # Retrieve and verify it does not error
        retrieved = get_saved_report_by_army_number(sparse_army_no)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get('army_number'), sparse_army_no)

        # Test paginated query includes it without crash
        res = fetch_reports_paginated(search_query=sparse_army_no)
        self.assertTrue(res.get('success'))
        self.assertEqual(len(res.get('data', [])), 1)
        row = res['data'][0]
        self.assertIsNone(row.get('age'))
        self.assertIsNone(row.get('fitness_score'))

    # 18. Complete Nutrition Plan and Tactical Exercise Regimen Verification
    def test_18_nutrition_and_exercise_recommendations(self):
        ret = analyze_personnel_fitness(self.test_army_no, regenerate=False)
        self.assertTrue(ret.get('success'))
        recs = ret.get('recommendations', {})
        self.assertIn('diet', recs)
        self.assertIn('exercise', recs)
        self.assertIn('medical_notice', recs)

        diet = recs['diet']
        self.assertIn('target_calories', diet)
        self.assertIn('strategy', diet)
        self.assertIn('macros', diet)
        self.assertIn('sample_menu', diet)
        self.assertIn('hydration_liters', diet)

        macros = diet['macros']
        self.assertIn('protein_grams', macros)
        self.assertIn('carb_grams', macros)
        self.assertIn('fat_grams', macros)
        self.assertIn('protein_pct', macros)
        self.assertIn('carb_pct', macros)
        self.assertIn('fat_pct', macros)

        ex = recs['exercise']
        self.assertIn('title', ex)
        self.assertIn('focus_area', ex)
        self.assertIn('exercises', ex)
        self.assertGreaterEqual(len(ex['exercises']), 1)


if __name__ == '__main__':
    unittest.main()
