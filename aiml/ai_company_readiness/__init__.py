"""
AI Company Readiness Module (AIML Branch).
Provides deterministic readiness calculations, operational gap identification,
personnel drill-down, ML predictions, and explainable recommendations.
"""

from .routes import ai_company_readiness_bp
from .services import CompanyReadinessService
from .readiness_engine import ReadinessEngine

__all__ = [
    "ai_company_readiness_bp",
    "CompanyReadinessService",
    "ReadinessEngine"
]
