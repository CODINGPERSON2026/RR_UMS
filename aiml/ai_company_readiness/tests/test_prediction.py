"""
Unit tests for ML Training Pipeline and Prediction Service.
Tests graceful fallback, no fake confidence, and model execution.
"""

import unittest
import numpy as np
import pandas as pd
from aiml.ai_company_readiness.prediction_service import ReadinessPredictionService
from aiml.ai_company_readiness.ai.model_training import ReadinessModelTrainer, MIN_TRAINING_SAMPLES
from aiml.ai_company_readiness.readiness_engine import ReadinessEngine
from aiml.ai_company_readiness.feature_engineering import FEATURE_COLUMNS


class TestPredictionService(unittest.TestCase):

    def setUp(self):
        self.predictor = ReadinessPredictionService()
        self.trainer = ReadinessModelTrainer()
        self.engine = ReadinessEngine()
        self.sample_requirements = [
            {"company": "3 COY", "requirement_type": "Strength", "requirement_name": "Total Personnel", "required_count": 95, "priority": "Critical"}
        ]
        self.personnel = [
            {"army_number": f"JC{i}", "name": f"Soldier {i}", "rank": "NK", "trade": "TTC", "company": "3 COY"}
            for i in range(90)
        ]

    def test_training_pipeline_insufficient_data(self):
        """Ensures trainer refuses to train on insufficient historical samples."""
        # 10 samples < MIN_TRAINING_SAMPLES (50)
        small_X = pd.DataFrame(np.random.rand(10, len(FEATURE_COLUMNS)), columns=FEATURE_COLUMNS)
        small_y = pd.Series(np.random.randint(0, 2, size=10))

        result = self.trainer.compare_and_train(small_X, small_y)
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertIn("under development", result["message"].lower())

    def test_prediction_under_development_fallback(self):
        """Verifies prediction returns honest fallback when model is not available."""
        readiness = self.engine.calculate_company_readiness("3 COY", self.sample_requirements, self.personnel, [], {})
        pred = self.predictor.get_prediction(readiness, self.personnel, {})

        if pred.status_code == "UNDER_DEVELOPMENT":
            self.assertIsNone(pred.predicted_readiness)
            self.assertIsNone(pred.confidence)
            self.assertEqual(pred.risk_level, "Under Evaluation")
            self.assertIn("under development", pred.status_message.lower())
            self.assertTrue(len(pred.important_factors) > 0)

    def test_no_fake_confidence(self):
        """Asserts that confidence is never fabricated without a valid model."""
        readiness = self.engine.calculate_company_readiness("3 COY", self.sample_requirements, self.personnel, [], {})
        pred = self.predictor.get_prediction(readiness, self.personnel, {})
        if pred.status_code == "UNDER_DEVELOPMENT":
            self.assertIsNone(pred.confidence, "Confidence must be None when model is under development")


    def test_extract_features_from_snapshot(self):
        """Verifies snapshot dictionary converts to all 19 feature columns."""
        from aiml.ai_company_readiness.feature_engineering import extract_features_from_snapshot
        snapshot = {
            "company": "HQ COY",
            "actual_strength": 100,
            "required_strength": 110,
            "onleave_count": 10,
            "detachment_count": 4,
            "td_count": 2,
            "oncourse_count": 3,
            "available_strength": 81,
            "unfit_count": 5,
            "trade_score": 90.0,
            "qualification_score": 85.0,
            "course_score": 80.0,
            "fitness_score": 88.0
        }
        feats = extract_features_from_snapshot(snapshot)
        for col in FEATURE_COLUMNS:
            self.assertIn(col, feats, f"Missing feature column: {col}")
        self.assertEqual(feats["company_hq"], 1.0)
        self.assertEqual(feats["company_comn"], 0.0)
        self.assertEqual(feats["company_3coy"], 0.0)
        self.assertAlmostEqual(feats["leave_rate"], 0.10)

    def test_training_pipeline_success(self):
        """Tests that compare_and_train completes successfully when sample count >= MIN_TRAINING_SAMPLES."""
        # 60 samples >= 50 MIN_TRAINING_SAMPLES
        X = pd.DataFrame(np.random.rand(60, len(FEATURE_COLUMNS)), columns=FEATURE_COLUMNS)
        y = pd.Series([1 if i % 2 == 0 else 0 for i in range(60)])

        result = self.trainer.compare_and_train(X, y, model_version="v_test")
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "TRAINED")
        self.assertIn(result["best_model"], ["Logistic Regression", "Random Forest", "Gradient Boosting"])
        self.assertIn("evaluation_metrics", result["metadata"])


if __name__ == "__main__":
    unittest.main()

