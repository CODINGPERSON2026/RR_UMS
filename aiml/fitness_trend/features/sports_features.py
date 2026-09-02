"""
Sports Feature Extraction Module for AI/ML Fitness Trend.
"""

from ..data.data_aggregator import aggregate_sports_for_personnel


def extract_sports_features(sports_rows):
    """
    Extracts numerical and categorical sports features for feature vector.
    
    Returns:
        dict with aggregated sports metrics.
    """
    agg = aggregate_sports_for_personnel(sports_rows)
    
    # Sports physical readiness bonus score (0 - 20 pts)
    # Rewards endurance, strength, team sports and multiple activities
    bonus = 0.0
    if agg['has_sport']:
        bonus += 5.0
        if agg['sport_count'] >= 2:
            bonus += 5.0
        if agg['endurance_sport_indicator'] or agg['water_sport_indicator']:
            bonus += 5.0
        if agg['strength_sport_indicator'] or agg['combat_sport_indicator']:
            bonus += 5.0
            
    agg['sports_readiness_score'] = min(20.0, bonus)
    return agg
