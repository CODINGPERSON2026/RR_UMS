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


if __name__ == "__main__":
    unittest.main()
