"""
Unit tests for deterministic Readiness Engine.
Tests all dimension calculations, gap detection, and weighted score synthesis.
"""

import unittest
from aiml.ai_company_readiness.readiness_engine import ReadinessEngine
from aiml.ai_company_readiness.models.readiness_models import DEFAULT_DIMENSION_WEIGHTS


class TestReadinessEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ReadinessEngine()
        self.sample_requirements = [
            {"company": "COMN COY", "requirement_type": "Strength", "requirement_name": "Total Personnel", "required_count": 100, "priority": "Critical"},
            {"company": "COMN COY", "requirement_type": "Trade", "requirement_name": "TTC", "required_count": 50, "priority": "High"},
            {"company": "COMN COY", "requirement_type": "Trade", "requirement_name": "LMN", "required_count": 20, "priority": "High"},
            {"company": "COMN COY", "requirement_type": "Qualification", "requirement_name": "12th", "required_count": 80, "priority": "Medium"},
            {"company": "COMN COY", "requirement_type": "Course", "requirement_name": "TTC CL I", "required_count": 10, "priority": "High"},
        ]

    def test_strength_gap(self):
        """Tests strength calculation and gap detection."""
        # 90 personnel against 100 required -> gap of 10, 90% score
        personnel = [{"id": i, "army_number": f"JC{i}", "company": "COMN COY"} for i in range(1, 91)]
        dim, gaps = self.engine.evaluate_strength(self.sample_requirements, personnel)
        
        self.assertEqual(dim.required_count, 100)
        self.assertEqual(dim.available_count, 90)
        self.assertEqual(dim.gap_count, 10)
        self.assertEqual(dim.score, 90.0)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].gap, 10)

    def test_trade_gap(self):
        """Tests technical trade distribution and deficits."""
        # 40 TTC (req 50) and 20 LMN (req 20) -> 60 available out of 70 required
        personnel = []
        for i in range(40):
            personnel.append({"army_number": f"JC{i}", "trade": "TTC", "company": "COMN COY"})
        for i in range(20):
            personnel.append({"army_number": f"JC{i+40}", "trade": "LMN", "company": "COMN COY"})

        dim, gaps = self.engine.evaluate_trade(self.sample_requirements, personnel)
        self.assertEqual(dim.required_count, 70)
        self.assertEqual(dim.available_count, 60)
        self.assertEqual(dim.gap_count, 10)
        self.assertEqual(len(gaps), 1)  # Only TTC has gap
        self.assertEqual(gaps[0].name, "TTC")
        self.assertEqual(gaps[0].gap, 10)

    def test_qualification_gap(self):
        """Tests educational qualification compliance."""
        # 60 out of 80 have 12th
        personnel = []
        for i in range(60):
            personnel.append({"army_number": f"JC{i}", "civ_qualifications": "12th Standard Passed"})
        for i in range(20):
            personnel.append({"army_number": f"JC{i+60}", "civ_qualifications": "10th Matriculation"})

        dim, gaps = self.engine.evaluate_qualification(self.sample_requirements, personnel)
        self.assertEqual(dim.required_count, 80)
        self.assertEqual(dim.available_count, 60)
        self.assertEqual(dim.gap_count, 20)
        self.assertEqual(dim.score, 75.0)

    def test_course_gap(self):
        """Tests military specialization course fulfillment."""
        # 5 out of 10 have TTC CL I
        personnel = [{"army_number": f"JC{i}", "detailed_course": "TTC CL I"} for i in range(5)]
        courses = []
        dim, gaps = self.engine.evaluate_course(self.sample_requirements, personnel, courses)
        self.assertEqual(dim.required_count, 10)
        self.assertEqual(dim.available_count, 5)
        self.assertEqual(dim.gap_count, 5)
        self.assertEqual(dim.score, 50.0)

    def test_availability_gap(self):
        """Tests ground presence against absence flags."""
        personnel = [
            {"army_number": "JC1", "onleave_status": 1, "detachment_status": 0, "td_status": 0, "oncourse_status": 0},
            {"army_number": "JC2", "onleave_status": 0, "detachment_status": 1, "td_status": 0, "oncourse_status": 0},
            {"army_number": "JC3", "onleave_status": 0, "detachment_status": 0, "td_status": 0, "oncourse_status": 0},
            {"army_number": "JC4", "onleave_status": 0, "detachment_status": 0, "td_status": 0, "oncourse_status": 0},
        ]
        dim, gaps = self.engine.evaluate_availability(personnel)
        self.assertEqual(dim.available_count, 2)
        self.assertEqual(dim.gap_count, 2)
        self.assertEqual(dim.score, 50.0)

    def test_readiness_score(self):
        """Tests full orchestration and weighted score summation."""
        personnel = [
            {
                "army_number": f"JC{i}",
                "name": f"Soldier {i}",
                "rank": "NK",
                "trade": "TTC" if i < 70 else "LMN",
                "civ_qualifications": "12th Passed",
                "detailed_course": "TTC CL I",
                "bpet_grading": "EX",
                "ppt_grading": "EX",
                "med_cat": "No",
                "onleave_status": 0,
                "detachment_status": 0,
                "td_status": 0,
                "oncourse_status": 0,
                "company": "COMN COY"
            }
            for i in range(100)
        ]
        res = self.engine.calculate_company_readiness(
            canonical_company="COMN COY",
            requirements=self.sample_requirements,
            personnel=personnel,
            courses=[],
            weight_info={}
        )
        # Res should be 100% since all 100 personnel meet all criteria
        self.assertEqual(res.overall_readiness, 100.0)
        self.assertEqual(res.status_badge["level"], "Optimal")
        self.assertEqual(len(res.all_gaps), 0)


if __name__ == "__main__":
    unittest.main()
