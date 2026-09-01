"""
Controlled Anti-Copy & Pattern Sensitivity Verification Test Suite.
Verifies that recommendation is driven by historical posting patterns and does not copy user checkboxes.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aiml.ai_new_joinee_recommendation.recommendation import recommend_placement, reset_model_cache


class TestPatternLearningAndAntiCopy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_model_cache()

    def test_case_1_signal_unit_predicts_comn_coy(self):
        """Signal Unit + Radio duty should learn strong historical affinity to COMN COY."""
        res = recommend_placement(
            units_history=[{
                "unit": "SIGNAL UNIT",
                "duty_performed": "Radio",
                "from_date": "2020-01-01",
                "to_date": "2023-01-01"
            }],
            is_fresh_joinee=False,
            army_number="TEST001A",
            name="SEP TEST"
        )
        self.assertEqual(res["recommended_company"], "COMN COY")
        self.assertEqual(res["recommended_section"], "COMMUNICATION / TECHNICAL")
        self.assertIn("Radio", res["recommended_position"])

    def test_case_2_admin_unit_predicts_hq_coy(self):
        """Admin Unit + Clerk duty should learn strong historical affinity to HQ COY."""
        res = recommend_placement(
            units_history=[{
                "unit": "ADMIN UNIT",
                "duty_performed": "Clerk",
                "from_date": "2020-01-01",
                "to_date": "2023-01-01"
            }],
            is_fresh_joinee=False,
            army_number="TEST002A",
            name="SEP TEST"
        )
        self.assertEqual(res["recommended_company"], "HQ COY")
        self.assertEqual(res["recommended_section"], "RHQ")

    def test_case_3_field_hq_predicts_3_coy(self):
        """Field HQ + Technician should learn strong historical affinity to 3 COY."""
        res = recommend_placement(
            units_history=[{
                "unit": "FIELD HQ",
                "duty_performed": "Technician",
                "from_date": "2020-01-01",
                "to_date": "2023-01-01"
            }],
            is_fresh_joinee=False,
            army_number="TEST003A",
            name="SEP TEST"
        )
        self.assertEqual(res["recommended_company"], "3 COY")
        self.assertEqual(res["recommended_section"], "TECHNICAL / CORPS HQ")

    def test_case_4_anti_copy_signal_unit_overrides_hq_selection(self):
        """User selects HQ COY checkbox, but history is Signal Unit -> Model must predict COMN COY."""
        res = recommend_placement(
            units_history=[{
                "unit": "SIGNAL UNIT",
                "duty_performed": "MCCS Exchange",
                "from_date": "2020-01-01",
                "to_date": "2023-01-01"
            }],
            is_fresh_joinee=False,
            selected_domains=[{
                "company": "HQ COY",
                "section": "CHQ",
                "appointment": "Mess Hav",
                "path": "HQ COY → CHQ → Mess Hav"
            }],
            army_number="TEST004A",
            name="SEP TEST"
        )
        # MUST NOT blindly return HQ COY
        self.assertEqual(res["recommended_company"], "COMN COY")
        print("Anti-Copy Case 4 Passed: Model predicted COMN COY despite HQ COY checkbox selected!")

    def test_case_5_anti_copy_admin_unit_overrides_comn_selection(self):
        """User selects COMN COY checkbox, but history is Admin Unit -> Model must predict HQ COY."""
        res = recommend_placement(
            units_history=[{
                "unit": "ADMIN UNIT",
                "duty_performed": "Adm NCO",
                "from_date": "2020-01-01",
                "to_date": "2023-01-01"
            }],
            is_fresh_joinee=False,
            selected_domains=[{
                "company": "COMN COY",
                "section": "COMMUNICATION / TECHNICAL",
                "appointment": "System",
                "path": "COMN COY → COMMUNICATION / TECHNICAL → System"
            }],
            army_number="TEST005A",
            name="SEP TEST"
        )
        # MUST NOT blindly return COMN COY
        self.assertEqual(res["recommended_company"], "HQ COY")
        print("Anti-Copy Case 5 Passed: Model predicted HQ COY despite COMN COY checkbox selected!")


if __name__ == "__main__":
    unittest.main()
