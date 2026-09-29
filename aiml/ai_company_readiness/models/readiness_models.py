"""
Data models, dataclasses, and configuration for AI Company Readiness.
Provides explicit, configurable dimension weights and structured representations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, date

# Explicit, documented configurable readiness dimension weights (Sum = 1.00)
# Weight justification:
# - Strength (20%): Foundation of military formation capacity.
# - Availability (20%): Ready soldiers present on ground vs onleave/detachment/TD.
# - Trade (15%): Technical operational role fulfillment.
# - Qualification (15%): Mandatory educational & technical standards.
# - Course (10%): Mission-critical military specialization courses.
# - Fitness (10%): Physical battle efficiency (BPET/PPT).
# - Medical (10%): SHAPE-1 compliance vs low medical categories.
DEFAULT_DIMENSION_WEIGHTS: Dict[str, float] = {
    "strength": 0.20,
    "availability": 0.20,
    "trade": 0.15,
    "qualification": 0.15,
    "course": 0.10,
    "fitness": 0.10,
    "medical": 0.10,
}


@dataclass
class DimensionScore:
    """Represents the score and breakdown of a specific readiness dimension."""
    dimension: str
    score: float
    weight: float
    weighted_score: float
    required_count: int
    available_count: int
    gap_count: int
    status: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GapItem:
    """Represents an identified operational gap in a company."""
    gap_type: str            # 'Strength', 'Trade', 'Qualification', 'Course', 'Fitness', 'Medical', 'Availability'
    name: str                # e.g., 'TTC CL I' or 'Total Personnel' or 'LMC Category'
    required: int
    available: int
    gap: int
    priority: str            # 'Critical', 'High', 'Medium', 'Low'
    percentage_met: float
    action_needed: str
    contributing_personnel_count: int = 0


@dataclass
class ContributingPersonnel:
    """Represents a soldier contributing to an identified gap."""
    army_number: str
    name: str
    rank: str
    trade: str
    company: str
    gap_category: str
    reason: str
    current_value: Optional[str] = None
    missing_value: Optional[str] = None
    restrictions: Optional[str] = None
    status_details: Optional[str] = None
    solution: Optional[str] = None


@dataclass
class RecommendationItem:
    """Actionable explainable recommendation derived from readiness analysis."""
    company: str
    issue_type: str
    priority: str
    title: str
    description: str
    action_steps: List[str]
    affected_trades: List[str] = field(default_factory=list)
    impact: str = "High"


@dataclass
class CompanyReadiness:
    """Complete readiness evaluation for a company."""
    company: str
    display_name: str
    overall_readiness: float
    status_badge: Dict[str, str]
    weights_used: Dict[str, float]
    dimensions: Dict[str, DimensionScore]
    main_gap: Optional[GapItem]
    all_gaps: List[GapItem]
    recommendations: List[RecommendationItem]
    insights: List[str]
    actual_strength: int
    required_strength: int
    effective_available_strength: int
    evaluation_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON APIs and templates."""
        return {
            "company": self.company,
            "display_name": self.display_name,
            "overall_readiness": round(self.overall_readiness, 1),
            "status_badge": self.status_badge,
            "weights_used": self.weights_used,
            "actual_strength": self.actual_strength,
            "required_strength": self.required_strength,
            "effective_available_strength": self.effective_available_strength,
            "main_gap": self.main_gap.__dict__ if self.main_gap else None,
            "all_gaps": [g.__dict__ for g in self.all_gaps],
            "dimensions": {k: v.__dict__ for k, v in self.dimensions.items()},
            "insights": self.insights,
            "recommendations": [r.__dict__ for r in self.recommendations],
            "evaluation_time": self.evaluation_time.strftime("%Y-%m-%d %H:%M:%S")
        }


@dataclass
class PredictionResult:
    """Output of ML prediction service with explainability factors."""
    company: str
    current_readiness: float
    predicted_readiness: Optional[float]
    prediction_period: str
    risk_level: str
    confidence: Optional[float]
    model_version: str
    status_code: str                     # 'AVAILABLE', 'UNDER_DEVELOPMENT', 'ERROR'
    status_message: str
    important_factors: List[Dict[str, Any]] = field(default_factory=list)
    mitigation_recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "current_readiness": round(self.current_readiness, 1),
            "predicted_readiness": round(self.predicted_readiness, 1) if self.predicted_readiness is not None else None,
            "prediction_period": self.prediction_period,
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 1) if self.confidence is not None else None,
            "model_version": self.model_version,
            "status_code": self.status_code,
            "status_message": self.status_message,
            "important_factors": self.important_factors,
            "mitigation_recommendations": self.mitigation_recommendations
        }
