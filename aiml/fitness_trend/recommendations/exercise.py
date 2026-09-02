"""
Personalized Exercise Plan Generator.
Builds structured tactical physical training routines tailored to soldier category, test weaknesses, and fitness goals.
"""

from .safety import filter_unsafe_exercises


def generate_personalized_exercise_plan(soldier_features, goal="Overall Fitness"):
    """
    Generates a structured weekly workout regimen.
    
    Returns:
        dict containing workout schedule, exercise table, and weekly structure.
    """
    category = soldier_features.get('ground_truth_category', 'AVERAGE')
    bpet_score = soldier_features.get('bpet_score') or 70
    ppt_score = soldier_features.get('ppt_score') or 70
    dev_pct = soldier_features.get('weight_deviation_percent') or 0.0
    
    # Base candidate exercises based on goals
    candidate_exercises = []
    
    if goal == 'BPET Improvement' or (bpet_score < 75 and goal == 'Overall Fitness'):
        regimen_title = "Tactical Endurance & BPET Mastery Routine"
        focus_area = "Cardiovascular capacity, 5km pacing, horizontal rope endurance, and sprint stamina."
        candidate_exercises = [
            {
                'exercise': '5km Interval Progression Run (300m sprint / 200m jog)',
                'type': 'endurance_run',
                'sets': 6,
                'reps': '500m per cycle',
                'duration': '35 mins',
                'frequency': '3 days/week',
                'rest': '90 sec',
                'intensity': 'High',
                'notes': 'Builds aerobic threshold for sub-22 min 5km BPET target.'
            },
            {
                'exercise': 'Horizontal Rope Traverse & Hanging Pulls',
                'type': 'tactical_rope',
                'sets': 4,
                'reps': '15-20 meters / 8 pulls',
                'duration': '15 mins',
                'frequency': '3 days/week',
                'rest': '60 sec',
                'intensity': 'Moderate - High',
                'notes': 'Increases grip endurance and shoulder girdle stamina.'
            },
            {
                'exercise': 'Burpees to Sprint Accelerations (20m shuttle)',
                'type': 'high_intensity_shuttle',
                'sets': 5,
                'reps': '10 burpees + 20m sprint',
                'duration': '12 mins',
                'frequency': '3 days/week',
                'rest': '60 sec',
                'intensity': 'High',
                'notes': 'Simulates rapid obstacle recovery and anaerobic power.'
            },
            {
                'exercise': 'Plank Hold & Side Bridge Circuit',
                'type': 'core_stabilization',
                'sets': 3,
                'reps': '60 sec front + 45 sec sides',
                'duration': '10 mins',
                'frequency': '4 days/week',
                'rest': '45 sec',
                'intensity': 'Moderate',
                'notes': 'Maintains torso rigidity with combat load.'
            }
        ]
    elif goal == 'PPT Improvement' or (ppt_score < 75 and goal == 'Overall Fitness'):
        regimen_title = "PPT Calisthenics & Functional Power Regimen"
        focus_area = "Chin-ups, 2.4km timing, sit-ups, push-ups, and sprint acceleration."
        candidate_exercises = [
            {
                'exercise': 'Standard Military Chin-Ups / Pull-Ups',
                'type': 'upper_pull',
                'sets': 4,
                'reps': '8 - 12 reps (or max to failure)',
                'duration': '15 mins',
                'frequency': '4 days/week',
                'rest': '90 sec',
                'intensity': 'High',
                'notes': 'Target: 10+ strict continuous repetitions for PPT Excellent.'
            },
            {
                'exercise': 'Military Push-Ups (Chest to Ground)',
                'type': 'upper_push',
                'sets': 4,
                'reps': '25 - 35 reps',
                'duration': '12 mins',
                'frequency': '4 days/week',
                'rest': '60 sec',
                'intensity': 'Moderate - High',
                'notes': 'Strict cadence with elbows at 45 degrees.'
            },
            {
                'exercise': '2.4km Speed Time Trial (PPT Baseline)',
                'type': 'speed_run',
                'sets': 1,
                'reps': '2.4 km continuous',
                'duration': '12 - 15 mins',
                'frequency': '2 days/week',
                'rest': 'Cool-down walk',
                'intensity': 'High',
                'notes': 'Target: under 9 mins 30 secs for top grading.'
            },
            {
                'exercise': 'Bent-Knee Sit-Ups (Strict 2-minute test pace)',
                'type': 'abdominal_endurance',
                'sets': 4,
                'reps': '40 - 50 reps in 2 mins',
                'duration': '10 mins',
                'frequency': '4 days/week',
                'rest': '60 sec',
                'intensity': 'Moderate',
                'notes': 'Core stamina for high PPT count.'
            }
        ]
    elif goal == 'Weight Loss' or dev_pct > 10.0:
        regimen_title = "Fat Burn & Metabolic Conditioning Circuit"
        focus_area = "Caloric expenditure, body fat reduction, and lean muscle preservation."
        candidate_exercises = [
            {
                'exercise': 'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)',
                'type': 'aerobic_run',
                'sets': 1,
                'reps': 'Continuous steady state',
                'duration': '35 - 40 mins',
                'frequency': '4 days/week',
                'rest': 'Stretch cool-down',
                'intensity': 'Moderate',
                'notes': 'Optimal fat oxidation zone (65-75% max HR).'
            },
            {
                'exercise': 'Bodyweight Full-Body Circuit (Jumping jacks, mountain climbers, bodyweight squats, lunges)',
                'type': 'metabolic_circuit',
                'sets': 4,
                'reps': '45 sec work / 15 sec rest per station',
                'duration': '20 mins',
                'frequency': '3 days/week',
                'rest': '90 sec between sets',
                'intensity': 'High',
                'notes': 'Elevates post-exercise oxygen consumption (EPOC).'
            },
            {
                'exercise': 'Stair Climbing & Hill Sprints',
                'type': 'incline_power',
                'sets': 6,
                'reps': '40 meters incline / walk down',
                'duration': '15 mins',
                'frequency': '2 days/week',
                'rest': '60 sec',
                'intensity': 'High',
                'notes': 'Intense lower body conditioning with high calorie burn.'
            },
            {
                'exercise': 'Core Russian Twists & Leg Raises',
                'type': 'core_circuit',
                'sets': 3,
                'reps': '20 reps each',
                'duration': '10 mins',
                'frequency': '4 days/week',
                'rest': '45 sec',
                'intensity': 'Moderate',
                'notes': 'Strengthens obliques and lower abdominal wall.'
            }
        ]
    else:
        regimen_title = "Complete Tactical Physical Readiness Regimen"
        focus_area = "Holistic physical readiness, balanced strength, stamina, and SHAPE-1 maintenance."
        candidate_exercises = [
            {
                'exercise': '5km Base Endurance Run',
                'type': 'endurance_run',
                'sets': 1,
                'reps': 'Continuous 5 km',
                'duration': '25 - 30 mins',
                'frequency': '3 days/week',
                'rest': '5 mins walk',
                'intensity': 'Moderate - High',
                'notes': 'Steady-state aerobic endurance maintenance.'
            },
            {
                'exercise': 'Upper Body Calisthenics (Pull-ups, Dips, Push-ups)',
                'type': 'upper_push_pull',
                'sets': 4,
                'reps': '10 pull-ups / 15 dips / 30 push-ups',
                'duration': '20 mins',
                'frequency': '3 days/week',
                'rest': '60 sec',
                'intensity': 'Moderate - High',
                'notes': 'Upper-body functional strength for battle obstacle courses.'
            },
            {
                'exercise': 'Unit Team Sports (Volleyball / Football / Basketball)',
                'type': 'team_sports',
                'sets': 1,
                'reps': 'Match play',
                'duration': '45 - 60 mins',
                'frequency': '3 days/week',
                'rest': 'As per game',
                'intensity': 'Moderate - High',
                'notes': 'Agility, hand-eye coordination, and tactical team cohesion.'
            },
            {
                'exercise': 'Dynamic Flexibility & Mobility Cool-Down',
                'type': 'flexibility',
                'sets': 1,
                'reps': 'Full-body stretches',
                'duration': '15 mins',
                'frequency': 'Daily after PT',
                'rest': 'N/A',
                'intensity': 'Low',
                'notes': 'Prevents muscle tightness, cramps, and joint stiffness.'
            }
        ]
        
    # Apply Medical Safety Filter
    safe_exercises, blocked_exercises = filter_unsafe_exercises(candidate_exercises, soldier_features)
    
    weekly_structure = [
        {"day": "Monday", "focus": "Cardiovascular Endurance & 5km Run", "session": "Morning Outdoor PT (06:00 - 07:15)"},
        {"day": "Tuesday", "focus": "Calisthenics & Strength Circuit", "session": "Unit PT Ground (06:00 - 07:00)"},
        {"day": "Wednesday", "focus": "Tactical Obstacle Course & Rope Work", "session": "Morning Obstacle Track (06:00 - 07:15)"},
        {"day": "Thursday", "focus": "Core Conditioning & High-Tempo Shuttle Runs", "session": "Morning PT (06:00 - 07:00)"},
        {"day": "Friday", "focus": "2.4km / 5km Speed Assessment", "session": "Timed Speed Run (06:00 - 07:15)"},
        {"day": "Saturday", "focus": "Unit Team Sports & Active Recreation", "session": "Evening Sports (16:30 - 18:00)"},
        {"day": "Sunday", "focus": "Active Recovery & Mobility Stretching", "session": "Rest & Foam Rolling"}
    ]
    
    return {
        'title': regimen_title,
        'focus_area': focus_area,
        'goal': goal,
        'exercises': safe_exercises,
        'blocked_exercises': blocked_exercises,
        'weekly_structure': weekly_structure
    }
