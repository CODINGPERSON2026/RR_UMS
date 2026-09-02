"""
AI/ML Individual Fitness Prediction & Personalized Fitness Report Module for UMS.
Isolated package containing complete data pipelines, ML models, rules, report builders, templates, and UI.
"""

from .routes import fitness_trend_bp

__all__ = ["fitness_trend_bp"]
