import unittest
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiml.ai_new_joinee_recommendation.position_mapping import (
    MASTER_HIERARCHY,
    CANONICAL_COMPANIES,
    get_all_companies,
    get_sections_for_company,
    get_positions_for_section,
    get_positions_for_company,
    get_section_for_position,
    is_valid_hierarchy,
    get_full_hierarchy_dict,
    rank_sections_and_positions_for_company
)
from aiml.ai_new_joinee_recommendation.preprocessing import (
    extract_features_from_dict,
    FEATURE_COLUMNS
)
from aiml.ai_new_joinee_recommendation.recommendation import (
    recommend_placement,
    load_model_artifacts
)


class TestAiRecommendationHierarchy(unittest.TestCase):
    """Test Suite 1: Canonical Master Hierarchy and Structure Validation."""

    def test_canonical_companies(self):
        """Verify the exact 3 canonical companies exist."""
        companies = get_all_companies()
        self.assertEqual(len(companies), 3)
        self.assertIn("HQ COY", companies)
        self.assertIn("COMN COY", companies)
        self.assertIn("3 COY", companies)

    def test_hq_coy_sections_and_positions(self):
        """Verify HQ COY sections and open positions."""
        sections = get_sections_for_company("HQ COY")
        expected_sections = ["QM", "RHQ", "RP", "TM", "MT", "LRW", "CHQ", "GENERAL DUTY"]
        for sec in expected_sections:
            self.assertIn(sec, sections)

        # Check RHQ positions
        rhq_positions = get_positions_for_section("HQ COY", "RHQ")
        for pos in ["O1", "O2", "O3", "TRG Clerk", "Clerk", "Warrant Clerk", "Part One Clerk", "Dispatcher Clerk", "A-Sigma Clerk", "PA"]:
            self.assertIn(pos, rhq_positions)

        # Check QM positions
        qm_positions = get_positions_for_section("HQ COY", "QM")
        for pos in ["Ration NCO", "Fresh NCO", "Clothing NCO", "MES NCO", "SKT"]:
            self.assertIn(pos, qm_positions)

        # Check RP positions
        rp_positions = get_positions_for_section("HQ COY", "RP")
        for pos in ["Adm NCO", "Strict Orderly", "Runner", "RP NCO", "Guest Room NCO"]:
            self.assertIn(pos, rp_positions)

        # Check GENERAL DUTY positions
        gd_positions = get_positions_for_section("HQ COY", "GENERAL DUTY")
        for pos in ["CHM", "CQMH", "RHM", "GD"]:
            self.assertIn(pos, gd_positions)

    def test_comn_coy_sections_and_positions(self):
        """Verify COMN COY technical communication establishment."""
        sections = get_sections_for_company("COMN COY")
        self.assertIn("COMMUNICATION / TECHNICAL", sections)

        positions = get_positions_for_section("COMN COY", "COMMUNICATION / TECHNICAL")
        expected_positions = [
            "Multimedia", "IT", "System", "Radio RR", "MCCS Exchange",
            "Communication Clerk", "Strip Clerk", "ICN", "NFS", "Server"
        ]
        for pos in expected_positions:
            self.assertIn(pos, positions)

    def test_3_coy_sections_and_positions(self):
        """Verify 3 COY technical and corps HQ establishment."""
        sections = get_sections_for_company("3 COY")
        self.assertIn("TECHNICAL / CORPS HQ", sections)

        positions = get_positions_for_section("3 COY", "TECHNICAL / CORPS HQ")
        expected_positions = ["VC", "Corps HQ", "System", "Branch"]
        for pos in expected_positions:
            self.assertIn(pos, positions)

    def test_hierarchy_validation_rules(self):
        """Verify is_valid_hierarchy accepts valid combos and rejects invalid combos."""
        # Valid combos
        self.assertTrue(is_valid_hierarchy("HQ COY", "RHQ", "Clerk"))
        self.assertTrue(is_valid_hierarchy("COMN COY", "COMMUNICATION / TECHNICAL", "Server"))
        self.assertTrue(is_valid_hierarchy("3 COY", "TECHNICAL / CORPS HQ", "VC"))
        self.assertTrue(is_valid_hierarchy("HQ COY", "QM", "Ration NCO"))

        # Invalid combos
        self.assertFalse(is_valid_hierarchy("HQ COY", "RHQ", "Server"))  # Server is in COMN COY
        self.assertFalse(is_valid_hierarchy("COMN COY", "QM", "Ration NCO"))  # QM is in HQ COY
        self.assertFalse(is_valid_hierarchy("3 COY", "RHQ", "Clerk"))  # RHQ is in HQ COY
        self.assertFalse(is_valid_hierarchy("HQ COY", "COMMUNICATION / TECHNICAL", "IT"))  # Comm is in COMN COY


class TestTradeExclusion(unittest.TestCase):
    """Test Suite 2: Strict Target and Feature Isolation Verification."""

    def test_feature_columns_do_not_contain_trade(self):
        """Ensure feature vector columns contain zero target leakage."""
        for col in FEATURE_COLUMNS:
            self.assertNotIn("clk_sd", col.lower())
            self.assertNotIn("ttc", col.lower())
            self.assertNotIn("lmn", col.lower())
            self.assertNotIn("artsn", col.lower())

    def test_feature_extraction_consistency(self):
        """Verify feature extraction is deterministic."""
        units = [
            {"unit": "17 REGM", "from_date": "2020-01-01", "to_date": "2022-01-01", "duty_performed": "SYSTEM"}
        ]
        vec1 = extract_features_from_dict(units_history=units)
        vec2 = extract_features_from_dict(units_history=units)
        self.assertEqual(vec1, vec2)

    def test_model_metadata_pattern_learning_flag(self):
        """Verify serialized model metadata specifies pattern-based training."""
        metadata_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'aiml', 'ai_new_joinee_recommendation', 'model', 'model_metadata.json'
        )
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            self.assertTrue(meta.get("pattern_based", False))
            self.assertTrue(meta.get("trade_excluded", False))


class TestHierarchicalPredictions(unittest.TestCase):
    """Test Suite 3: 3-Stage Hierarchical Recommendation Engine."""

    def test_hierarchical_recommendation_output_structure(self):
        """Verify recommendation output contains company, section, position, and probabilities."""
        rec = recommend_placement(
            units_history=[
                {"unit": "SIGNAL UNIT", "from_date": "2019-01-01", "to_date": "2023-01-01", "duty_performed": "Radio"}
            ]
        )
        self.assertIn("recommended_company", rec)
        self.assertIn("recommended_section", rec)
        self.assertIn("recommended_position", rec)
        self.assertIn("confidence_score", rec)
        self.assertIn("alternative_allocations", rec)
        self.assertIn("shap_explanation", rec)
        self.assertIn("match_reasons", rec)

        # Verify hierarchical validity of the top recommendation
        self.assertTrue(is_valid_hierarchy(
            rec["recommended_company"],
            rec["recommended_section"],
            rec["recommended_position"]
        ))

        # Verify all alternative allocations adhere strictly to master hierarchy
        for alt in rec["alternative_allocations"]:
            self.assertTrue(is_valid_hierarchy(
                alt["company"],
                alt["section"],
                alt["position"]
            ), f"Invalid hierarchy in alternative_allocations: {alt}")

    def test_fresh_joinee_routing(self):
        """Verify fresh joinees (0 previous postings) are routed with valid hierarchy."""
        rec = recommend_placement(
            units_history=[],
            is_fresh_joinee=True
        )
        self.assertTrue(is_valid_hierarchy(
            rec["recommended_company"],
            rec["recommended_section"],
            rec["recommended_position"]
        ))


class TestRestApiEndpoints(unittest.TestCase):
    """Test Suite 4: REST API Blueprint Endpoints."""

    @classmethod
    def setUpClass(cls):
        from app import app
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_api_hierarchy_endpoint(self):
        """Verify /api/ai/company-recommendation/hierarchy returns the master hierarchy."""
        res = self.client.get('/api/ai/company-recommendation/hierarchy')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("hierarchy", data)
        self.assertIn("HQ COY", data["hierarchy"])
        self.assertIn("COMN COY", data["hierarchy"])
        self.assertIn("3 COY", data["hierarchy"])

    def test_api_predict_endpoint(self):
        """Verify /api/ai/company-recommendation/predict works with unit history."""
        payload = {
            "army_number": "15678901A",
            "name": "SEP RAMESH KUMAR",
            "units_history": [
                {"unit": "LOGISTICS UNIT", "from_date": "2018-06-01", "to_date": "2022-06-01", "duty_performed": "SKT"}
            ]
        }
        res = self.client.post('/api/ai/company-recommendation/predict', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        rec = data.get("data", {})
        self.assertEqual(rec["recommended_company"], "HQ COY")
        self.assertEqual(rec["recommended_section"], "QM")
        self.assertTrue(is_valid_hierarchy(
            rec["recommended_company"],
            rec["recommended_section"],
            rec["recommended_position"]
        ))

    def test_api_probability_distributions_sum(self):
        """Verify company, section, and position probability distributions sum to ~1.0."""
        payload = {
            "units_history": [
                {"unit": "FIELD UNIT", "from_date": "2021-01-01", "to_date": "2024-01-01", "duty_performed": "GD"}
            ]
        }
        res = self.client.post('/api/ai/company-recommendation/predict', json=payload)
        self.assertEqual(res.status_code, 200)
        rec = res.get_json().get("data", {})

        coy_probs = [item["probability"] for item in rec.get("company_probabilities", [])]
        self.assertAlmostEqual(sum(coy_probs), 1.0, delta=0.05)

        sec_probs = [item["probability"] for item in rec.get("section_probabilities", [])]
        self.assertAlmostEqual(sum(sec_probs), 1.0, delta=0.05)

        pos_probs = [item["probability"] for item in rec.get("position_probabilities", [])]
        self.assertAlmostEqual(sum(pos_probs), 1.0, delta=0.05)


if __name__ == '__main__':
    unittest.main()
