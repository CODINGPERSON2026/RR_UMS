"""
Unified Recommendation Engine for AI/ML Fitness Trend.
Orchestrates medical clearance checks, personalized nutrition, and tactical exercise regimens.
"""

from .diet import generate_personalized_diet
from .exercise import generate_personalized_exercise_plan
from .safety import get_medical_clearance_notice


def generate_full_recommendations(soldier_features, goal="Overall Fitness"):
    """
    Produces complete personalized diet, exercise, and medical safety guidelines.
    
    Returns:
        dict: {
            'medical_notice': dict,
            'diet': dict,
            'exercise': dict,
            'goal_selected': str
        }
    """
    medical_notice = get_medical_clearance_notice(soldier_features)
    diet_plan = generate_personalized_diet(soldier_features, goal=goal)
    exercise_plan = generate_personalized_exercise_plan(soldier_features, goal=goal)
    
    return {
        'medical_notice': medical_notice,
        'diet': diet_plan,
        'exercise': exercise_plan,
        'goal_selected': goal
    }
