import unittest
import os
import re
from app import app

class TestAiJoineeDomainAndReset(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'modals', 'ai_new_joinee_recommendation_modal.html')

    def test_lookup_15706814h_data(self):
        """Verify 15706814H is correctly looked up with trade ARTISH and 6 units."""
        response = self.app.get('/api/ai/company-recommendation/lookup-personnel?army_number=15706814H')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['found'])
        personnel = data['data']
        self.assertEqual(personnel['army_number'], '15706814H')
        self.assertEqual(personnel['trade'], 'ARTISH')
        self.assertEqual(personnel['rank'], 'LOC NK')
        self.assertIn('units_served', personnel)
        self.assertEqual(len(personnel['units_served']), 6)

    def test_modal_template_sync_notice_and_domain_mapping(self):
        """Verify template code has proper duty mapping and hideAiSyncNotice implementation."""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Verify aiMainFormSyncNotice starts with d-none and display: none !important
        self.assertIn('id="aiMainFormSyncNotice"', content)
        self.assertIn('class="p-2 mb-2.5 rounded border d-none justify-content-between align-items-center"', content)
        self.assertIn('display: none !important;', content)

        # 2. Verify showAiSyncNotice & hideAiSyncNotice functions exist
        self.assertIn('function showAiSyncNotice(', content)
        self.assertIn('function hideAiSyncNotice()', content)
        self.assertIn("syncNotice.classList.add('d-none')", content)
        self.assertIn("syncNotice.classList.remove('d-flex')", content)
        self.assertIn("syncNotice.style.setProperty('display', 'none', 'important')", content)

        # 3. Verify resetAiRecommendationModal calls hideAiSyncNotice
        self.assertIn('function resetAiRecommendationModal()', content)
        self.assertIn('hideAiSyncNotice();', content)

        # 4. Verify ARTISH / ARTSN is mapped to All Tradesmen
        self.assertIn("s.includes('ARTISH')", content)
        self.assertIn("matches.push('All Tradesmen')", content)

        # 5. Verify buildDutyCheckboxesHtml guarantees fallback to GD when no match
        self.assertIn('const hasTreeMatch = expanded.some(v => allTreeTrades.has(v.toUpperCase()));', content)
        self.assertIn("expanded.push('GD');", content)

        # 6. Verify addAiUnitRow has safeguard ONLY if initialDuty was explicitly provided
        self.assertIn('if (initialDuty && String(initialDuty).trim())', content)
        self.assertIn('const gdChk = tr.querySelector(\'.ai-duty-chk[value="GD"]\');', content)

        # 7. Verify empty duty leaves domain clean and unselected (Select Duty / Domain)
        self.assertIn('if (selValues.length > 0) {', content)
        self.assertIn("addAiUnitRow('');", content)

if __name__ == '__main__':
    unittest.main()
