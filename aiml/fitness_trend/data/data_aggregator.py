"""
Sports Aggregator for AI/ML Fitness Trend.
Aggregates multiple sports entries per soldier into a single record without row duplication.
"""

from ..config import SPORTS_CATEGORY_MAP


def classify_sport(sport_name, sport_type=None):
    """
    Classifies a raw sport string into standard physical activity categories:
    ['team', 'individual', 'endurance', 'strength', 'combat', 'water_endurance', 'other']
    """
    tokens = []
    if sport_name:
        tokens.extend(str(sport_name).strip().lower().replace('-', ' ').replace('/', ' ').split())
    if sport_type:
        tokens.extend(str(sport_type).strip().lower().replace('-', ' ').replace('/', ' ').split())
        
    full_str = f"{sport_name or ''} {sport_type or ''}".lower()
    
    # Check direct dictionary lookups
    for token in tokens:
        if token in SPORTS_CATEGORY_MAP:
            return SPORTS_CATEGORY_MAP[token]
            
    # Substring matches
    for key, cat in SPORTS_CATEGORY_MAP.items():
        if key in full_str:
            return cat
            
    return 'other'


def aggregate_sports_for_personnel(sports_rows):
    """
    Aggregates a list of sports records for a single soldier.
    
    Returns:
        dict: {
            'sport_count': int,
            'has_sport': int (0 or 1),
            'sports_list': str (comma-separated),
            'primary_sport': str or 'None',
            'team_sport_indicator': int,
            'individual_sport_indicator': int,
            'endurance_sport_indicator': int,
            'strength_sport_indicator': int,
            'combat_sport_indicator': int,
            'water_sport_indicator': int,
            'physical_activity_level': str ('High', 'Moderate', 'Low', 'Sedentary')
        }
    """
    if not sports_rows:
        return {
            'sport_count': 0,
            'has_sport': 0,
            'sports_list': 'None',
            'primary_sport': 'None',
            'team_sport_indicator': 0,
            'individual_sport_indicator': 0,
            'endurance_sport_indicator': 0,
            'strength_sport_indicator': 0,
            'combat_sport_indicator': 0,
            'water_sport_indicator': 0,
            'physical_activity_level': 'Low'
        }
    
    unique_sports = []
    categories = set()
    
    for row in sports_rows:
        s_name = (row.get('sport_name') or row.get('sport_type') or '').strip()
        s_type = (row.get('sport_type') or '').strip()
        if s_name and s_name.upper() not in ['NONE', 'NIL', 'NA', '-']:
            if s_name.title() not in unique_sports:
                unique_sports.append(s_name.title())
            cat = classify_sport(s_name, s_type)
            categories.add(cat)
            
    sport_count = len(unique_sports)
    has_sport = 1 if sport_count > 0 else 0
    primary_sport = unique_sports[0] if unique_sports else 'None'
    sports_list = ", ".join(unique_sports) if unique_sports else 'None'
    
    team_ind = 1 if 'team' in categories else 0
    indiv_ind = 1 if 'individual' in categories else 0
    endur_ind = 1 if ('endurance' in categories or 'water_endurance' in categories) else 0
    streng_ind = 1 if 'strength' in categories else 0
    combat_ind = 1 if 'combat' in categories else 0
    water_ind = 1 if 'water_endurance' in categories else 0
    
    # Estimate activity level based on sport participation
    if sport_count >= 2 or endur_ind or combat_ind:
        act_level = 'High'
    elif sport_count == 1:
        act_level = 'Moderate'
    else:
        act_level = 'Low'
        
    return {
        'sport_count': sport_count,
        'has_sport': has_sport,
        'sports_list': sports_list,
        'primary_sport': primary_sport,
        'team_sport_indicator': team_ind,
        'individual_sport_indicator': indiv_ind,
        'endurance_sport_indicator': endur_ind,
        'strength_sport_indicator': streng_ind,
        'combat_sport_indicator': combat_ind,
        'water_sport_indicator': water_ind,
        'physical_activity_level': act_level
    }


def aggregate_all_sports(all_sports_rows):
    """
    Aggregates all sports rows grouped by army_number.
    Returns:
        dict mapping army_number -> aggregated sports dict
    """
    grouped = {}
    for r in all_sports_rows:
        army_no = (r.get('army_number') or '').strip()
        if not army_no:
            continue
        if army_no not in grouped:
            grouped[army_no] = []
        grouped[army_no].append(r)
        
    result = {}
    for army_no, s_rows in grouped.items():
        result[army_no] = aggregate_sports_for_personnel(s_rows)
    return result
