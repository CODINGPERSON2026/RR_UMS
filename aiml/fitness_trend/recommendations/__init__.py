"""
Personalized Recommendations and Safety Filter for AI/ML Fitness Trend.
"""

from .safety import filter_unsafe_exercises, get_medical_clearance_notice
from .diet import generate_personalized_diet
from .exercise import generate_personalized_exercise_plan
from .recommendation_engine import generate_full_recommendations

__all__ = [
    'filter_unsafe_exercises',
    'get_medical_clearance_notice',
    'generate_personalized_diet',
    'generate_personalized_exercise_plan',
    'generate_full_recommendations'
]
