"""
Unit tests for Feature Engineering Pipeline and Data Leakage Prevention.
"""

import unittest
from datetime import date, timedelta
from aiml.ai_company_readiness.feature_engineering import (
    extract_features_from_readiness,
    to_feature_vector,
    to_feature_dataframe,
    FEATURE_COLUMNS
)
from aiml.ai_company_readiness.readiness_engine import ReadinessEngine


class TestFeatureEngineering(unittest.TestCase):

    def setUp(self):
        self.engine = ReadinessEngine()
        self.sample_requirements = [
            {"company": "HQ COY", "requirement_type": "Strength", "requirement_name": "Total Personnel", "required_count": 100, "priority": "Critical"},
            {"company": "HQ COY", "requirement_type": "Trade", "requirement_name": "TTC", "required_count": 40, "priority": "High"},
        ]
        self.personnel = [
            {
                "army_number": f"JC{i}",
                "name": f"Soldier {i}",
                "rank": "HAV",
                "trade": "TTC" if i < 30 else "GD",
                "civ_qualifications": "12th",
                "detailed_course": "None",
                "bpet_grading": "EX",
                "ppt_grading": "GOOD",
                "med_cat": "No",
                "onleave_status": 1 if i < 10 else 0,
                "detachment_status": 1 if 10 <= i < 15 else 0,
                "td_status": 0,
                "oncourse_status": 0,
                "next_recat_due": date.today() + timedelta(days=30) if i < 5 else None,
                "company": "HQ COY"
            }
            for i in range(100)
        ]

    def test_feature_generation(self):
        """Verifies feature extraction dictionary values."""
        readiness = self.engine.calculate_company_readiness(
            "HQ COY", self.sample_requirements, self.personnel, [], {}
        )
        features = extract_features_from_readiness(readiness, self.personnel, {})

        # Check all expected columns exist
        for col in FEATURE_COLUMNS:
            self.assertIn(col, features, f"Missing feature {col}")

        # Check calculated ratios
        self.assertEqual(features["company_hq"], 1.0)
        self.assertEqual(features["company_comn"], 0.0)
        self.assertEqual(features["company_3coy"], 0.0)
        self.assertEqual(features["actual_strength"], 100.0)
        self.assertEqual(features["authorized_strength"], 100.0)
        self.assertEqual(features["leave_rate"], 0.10)
        self.assertEqual(features["detachment_rate"], 0.05)
        self.assertEqual(features["availability_rate"], 0.85)

    def test_feature_vector_shape(self):
        """Verifies numpy vector dimensions."""
        readiness = self.engine.calculate_company_readiness(
            "HQ COY", self.sample_requirements, self.personnel, [], {}
        )
        features = extract_features_from_readiness(readiness, self.personnel, {})
        vec = to_feature_vector(features)
        
        self.assertEqual(len(vec.shape), 1)
        self.assertEqual(vec.shape[0], len(FEATURE_COLUMNS))

    def test_no_future_data_leakage(self):
        """Ensures features depend strictly on current state."""
        ref_today = date.today()
        # Modifying a future-dated attribute outside of 60-day window should not affect features
        modified_personnel = [p.copy() for p in self.personnel]
        modified_personnel[0]["next_recat_due"] = ref_today + timedelta(days=365)  # Far future

        readiness = self.engine.calculate_company_readiness("HQ COY", self.sample_requirements, modified_personnel, [], {})
        features = extract_features_from_readiness(readiness, modified_personnel, {}, as_of_date=ref_today)
        
        # JC0 should no longer count in <= 60-day window
        self.assertEqual(features["upcoming_recat_ratio"], 0.04)


if __name__ == "__main__":
    unittest.main()
