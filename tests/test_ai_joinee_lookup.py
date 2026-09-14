import sys
import os
import unittest

sys.path.insert(0, os.path.abspath('.'))
from flask import Flask
from aiml.ai_new_joinee_recommendation.routes import company_rec_bp

class TestAiNewJoineeLookup(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(company_rec_bp)
        self.client = self.app.test_client()

    def test_valid_army_number_with_units(self):
        """Test lookup with a valid army number that has units_served records"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel?army_number=15693005M')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('found'))
        p = data.get('data', {})
        self.assertEqual(p.get('army_number'), '15693005M')
        self.assertEqual(p.get('name'), 'sushil kumar singh')
        self.assertEqual(p.get('rank'), 'HAV')
        self.assertEqual(p.get('trade'), 'TTC')
        self.assertEqual(p.get('company'), 'COMN Company')
        self.assertIsInstance(p.get('units_served'), list)
        self.assertGreater(len(p['units_served']), 0)
        first_unit = p['units_served'][0]
        self.assertEqual(first_unit['unit'], '2CSR(A)')
        self.assertEqual(first_unit['from_date'], '03-03-2006')
        self.assertEqual(first_unit['to_date'], '03-04-2006')
        self.assertEqual(first_unit['duty_performed'], 'RR')

    def test_valid_army_number_case_insensitive(self):
        """Test lookup with lowercase army number"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel?army_number=15693005m')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('found'))
        self.assertEqual(data['data']['name'], 'sushil kumar singh')

    def test_lookup_by_name(self):
        """Test lookup by soldier name"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel?name=sushil%20kumar%20singh')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('found'))
        p = data.get('data', {})
        self.assertEqual(p.get('army_number'), '15693005M')
        self.assertEqual(p.get('name'), 'sushil kumar singh')
        self.assertGreater(len(p.get('units_served', [])), 0)

    def test_lookup_by_name_with_rank_prefix(self):
        """Test lookup by soldier name with military rank prefix (e.g. 'HAV sushil kumar singh')"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel?name=HAV%20sushil%20kumar%20singh')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('found'))
        self.assertEqual(data['data']['army_number'], '15693005M')

    def test_dues_in_lookup_by_name_and_previous_unit(self):
        """Test lookup of incoming new joinee from dues_in by name and verify previous unit is filled"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel?name=Amit%20Yonzone')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('found'))
        p = data.get('data', {})
        self.assertEqual(p.get('army_number'), '15680060K')
        self.assertEqual(p.get('name'), 'Amit Yonzone')
        self.assertEqual(p.get('rank'), 'Hav')
        self.assertIsInstance(p.get('units_served'), list)
        self.assertEqual(len(p['units_served']), 1)
        self.assertEqual(p['units_served'][0]['unit'], 'Delhi Area Sig Coy')

    def test_dues_in_lookup_by_name_with_rank_prefix(self):
        """Test dues_in lookup when user typed 'SEP AMIT YONZONE'"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel?name=SEP%20AMIT%20YONZONE')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('found'))
        self.assertEqual(data['data']['army_number'], '15680060K')
        self.assertEqual(data['data']['units_served'][0]['unit'], 'Delhi Area Sig Coy')

    def test_worked_unit_tenure_fallback_populates_previous_unit(self):
        """Test soldier with worked_unit_tenure fills previous unit when units_served has 0 rows"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel?name=Devnandan%20Yadav')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertTrue(data.get('found'))
        p = data.get('data', {})
        self.assertEqual(p.get('army_number'), '15687626P')
        self.assertIsInstance(p.get('units_served'), list)
        self.assertEqual(len(p['units_served']), 1)
        self.assertEqual(p['units_served'][0]['unit'], '52 NSR')

    def test_invalid_army_number(self):
        """Test lookup with non-existent army number"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel?army_number=NONEXISTENT999X')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertFalse(data.get('found'))
        self.assertIn('not found', data.get('message', '').lower())

    def test_missing_params(self):
        """Test lookup with empty query"""
        res = self.client.get('/api/ai/company-recommendation/lookup-personnel')
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get('success'))

    def test_search_personnel_amr(self):
        """Test search-personnel API for user request 'when i write in soldier man like amr'"""
        res = self.client.get('/api/ai/company-recommendation/search-personnel?q=amr')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertGreaterEqual(data.get('count', 0), 1)
        soldiers = data.get('data', [])
        self.assertTrue(any('AMRENDRA SHUKLA' in s.get('name', '').upper() for s in soldiers))
        amr = next(s for s in soldiers if 'AMRENDRA SHUKLA' in s.get('name', '').upper())
        self.assertEqual(amr.get('army_number'), '15744564F')
        self.assertEqual(amr.get('rank'), 'L NK')
        self.assertEqual(amr.get('trade'), 'TTC')
        self.assertGreaterEqual(len(amr.get('units_served', [])), 1)

    def test_search_personnel_dues_in(self):
        """Test search-personnel API finds dues_in incoming records by partial name"""
        res = self.client.get('/api/ai/company-recommendation/search-personnel?q=yonzone')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertGreaterEqual(data.get('count', 0), 1)
        soldiers = data.get('data', [])
        self.assertTrue(any('YONZONE' in s.get('name', '').upper() for s in soldiers))

if __name__ == '__main__':
    unittest.main()

