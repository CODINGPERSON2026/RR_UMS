"""
Personalized Tactical Physical Training & Exercise Drill Generator.
Builds structured physical training routines personalized to the soldier's fitness score,
BPET/PPT testing results, body composition, medical safety clearance, and operational goals.
"""

from .safety import filter_unsafe_exercises


def generate_personalized_exercise_plan(soldier_features, goal="Overall Fitness"):
    """
    Generates a structured weekly workout regimen with personalized drills,
    sets, repetitions, duration, frequency, rest intervals, and progression notes.
    
    Args:
        soldier_features (dict): Soldier metrics (weight, height, age, scores, restrictions)
        goal (str): Selected fitness goal
        
    Returns:
        dict: Complete personalized physical training plan.
    """
    bpet_score = soldier_features.get('bpet_score') or 70
    ppt_score = soldier_features.get('ppt_score') or 70
    dev_pct = float(soldier_features.get('weight_deviation_percent') or 0.0)
    fit_status = str(soldier_features.get('fitness_status') or '').strip().lower()
    fit_score = float(soldier_features.get('fitness_score') or 75.0)

    is_unfit_or_overweight = (
        'risk' in fit_status or 'unfit' in fit_status or 'needs' in fit_status or
        'poor' in fit_status or fit_score < 60.0 or dev_pct > 10.0 or goal == 'Weight Loss'
    )
    is_underweight = (dev_pct < -8.0)

    candidate_exercises = []

    # 1. Unfit / Overweight / Needs Improvement Regimen
    if is_unfit_or_overweight:
        regimen_title = "Corrective Conditioning & Caloric Expenditure Regimen"
        focus_area = "Cardiovascular capacity, joint-safe fat oxidation, muscular endurance, and progressive load adaptation."
        candidate_exercises = [
            {
                'exercise': 'Low-Impact Aerobic Conditioning (Brisk Walk & Interval Jogging)',
                'type': 'aerobic_run',
                'sets': 1,
                'reps': '3.5 - 5.0 km continuous',
                'duration': '30 - 35 mins',
                'frequency': '5 days / week',
                'rest': '5 mins stretch cool-down',
                'intensity': 'Moderate',
                'progression': 'Increase duration by 5 minutes every 2 weeks toward 45 mins.',
                'notes': 'Sustains optimal fat oxidation heart rate zone (60-70% max HR) without excessive joint impact.'
            },
            {
                'exercise': 'Bodyweight Squats & Alternating Lunges',
                'type': 'lower_body_strength',
                'sets': 3,
                'reps': '12 - 15 reps per set',
                'duration': '12 mins',
                'frequency': '3 days / week',
                'rest': '60 sec',
                'intensity': 'Moderate',
                'progression': 'Increase reps by 2 every 2 weeks up to 20 reps.',
                'notes': 'Develops knee joint stability, quad endurance, and lower-body load carriage support.'
            },
            {
                'exercise': 'Cadence Push-Ups (Strict Form / Incline if Required)',
                'type': 'upper_push',
                'sets': 3,
                'reps': '10 - 15 strict reps',
                'duration': '10 mins',
                'frequency': '4 days / week',
                'rest': '60 sec',
                'intensity': 'Moderate',
                'progression': 'Advance by 2 reps weekly toward standard 25-rep benchmark.',
                'notes': 'Maintain neutral spine and 45-degree elbow tuck for shoulder preservation.'
            },
            {
                'exercise': 'Prone Plank Hold & Side Bridge Core Circuit',
                'type': 'core_stabilization',
                'sets': 3,
                'reps': '30 - 45 sec front + 25 sec each side',
                'duration': '8 mins',
                'frequency': '4 days / week',
                'rest': '45 sec',
                'intensity': 'Moderate',
                'progression': 'Increase hold time by 5 seconds every week toward 60 seconds.',
                'notes': 'Strengthens abdominal wall, transverse abdominis, and protects lumbar spine.'
            },
            {
                'exercise': 'Dynamic Joint Mobility & Flexibility Cool-Down',
                'type': 'flexibility',
                'sets': 1,
                'reps': 'Full-body static & dynamic stretches',
                'duration': '15 mins',
                'frequency': 'Daily after PT',
                'rest': 'N/A',
                'intensity': 'Low',
                'progression': 'Maintain full range of motion across ankles, hips, and shoulders.',
                'notes': 'Prevents post-drill muscle soreness, stiffness, and joint fatigue.'
            }
        ]

    # 2. BPET Improvement Regimen
    elif goal == 'BPET Improvement' or (bpet_score < 75 and goal == 'Overall Fitness'):
        regimen_title = "Tactical Endurance & BPET Mastery Routine"
        focus_area = "5km military pacing, horizontal rope traverse, sprint shuttles, and battle load stamina."
        candidate_exercises = [
            {
                'exercise': '5km Interval Progression Run (400m fast pace / 200m recovery jog)',
                'type': 'endurance_run',
                'sets': 6,
                'reps': '600m cycle (3.6 km total)',
                'duration': '30 mins',
                'frequency': '3 days / week',
                'rest': '90 sec jog recovery',
                'intensity': 'High',
                'progression': 'Target sub-22 minute 5km timing with progressive lap pacing.',
                'notes': 'Builds peak aerobic capacity (VO2 max) for BPET Excellent classification.'
            },
            {
                'exercise': 'Horizontal Rope Traverse & Static Hanging Pulls',
                'type': 'tactical_rope',
                'sets': 4,
                'reps': '15 - 20 meters / 8 strict pulls',
                'duration': '15 mins',
                'frequency': '3 days / week',
                'rest': '60 sec',
                'intensity': 'Moderate - High',
                'progression': 'Increase traverse speed and add 2 hanging pulls bi-weekly.',
                'notes': 'Builds grip endurance and latissimus dorsi power for obstacle negotiation.'
            },
            {
                'exercise': 'Sprint Shuttle Accelerations (10 x 20m shuttles)',
                'type': 'high_intensity_shuttle',
                'sets': 4,
                'reps': '10 shuttles per set',
                'duration': '12 mins',
                'frequency': '3 days / week',
                'rest': '60 sec',
                'intensity': 'High',
                'progression': 'Reduce total set time by 2 seconds weekly.',
                'notes': 'Enhances anaerobic recovery and rapid change-of-direction acceleration.'
            },
            {
                'exercise': 'Weighted Load March Conditioning (10kg battle pack)',
                'type': 'tactical_march',
                'sets': 1,
                'reps': '5 - 8 km road march',
                'duration': '45 - 60 mins',
                'frequency': '1 day / week',
                'rest': 'Continuous marching',
                'intensity': 'High',
                'progression': 'Gradually increase march distance from 5km to 8km.',
                'notes': 'Tactical load carriage resilience and tendon conditioning.'
            }
        ]

    # 3. PPT Improvement Regimen
    elif goal == 'PPT Improvement' or (ppt_score < 75 and goal == 'Overall Fitness'):
        regimen_title = "PPT Calisthenics & Functional Power Regimen"
        focus_area = "Chin-ups, 2.4km speed timing, bent-knee sit-ups, and sprint endurance."
        candidate_exercises = [
            {
                'exercise': 'Strict Military Chin-Ups / Pull-Ups',
                'type': 'upper_pull',
                'sets': 4,
                'reps': '8 - 12 strict continuous reps',
                'duration': '12 mins',
                'frequency': '4 days / week',
                'rest': '90 sec',
                'intensity': 'High',
                'progression': 'Target 10+ consecutive repetitions for PPT Excellent standard.',
                'notes': 'Full dead-hang extension at bottom; chin clearly over bar at top.'
            },
            {
                'exercise': 'Standard Military Push-Ups (Chest to Ground)',
                'type': 'upper_push',
                'sets': 4,
                'reps': '25 - 35 continuous reps',
                'duration': '12 mins',
                'frequency': '4 days / week',
                'rest': '60 sec',
                'intensity': 'Moderate - High',
                'progression': 'Add 3 reps per set every 10 days.',
                'notes': 'Strict military cadence with complete elbow lockout at apex.'
            },
            {
                'exercise': '2.4km Speed Time Trial (PPT Baseline)',
                'type': 'speed_run',
                'sets': 1,
                'reps': '2.4 km continuous timed effort',
                'duration': '10 - 13 mins',
                'frequency': '2 days / week',
                'rest': 'Cool-down walk',
                'intensity': 'High',
                'progression': 'Target completion time under 9 mins 30 secs.',
                'notes': 'Paced speed endurance test simulation.'
            },
            {
                'exercise': 'Bent-Knee Military Sit-Ups (Timed 2-Minute Cadence)',
                'type': 'abdominal_endurance',
                'sets': 4,
                'reps': '35 - 45 reps in 2 minutes',
                'duration': '10 mins',
                'frequency': '4 days / week',
                'rest': '60 sec',
                'intensity': 'Moderate - High',
                'progression': 'Increase count by 4 reps every 2 weeks.',
                'notes': 'Elbows touch knees; shoulder blades touch ground on descent.'
            }
        ]

    # 4. Standard Operational Conditioning (Fit / Combat Ready)
    else:
        regimen_title = "Operational Combat Readiness & Physical Mastery Regimen"
        focus_area = "Aerobic endurance, functional calisthenics, agility, and SHAPE-1 military performance."
        candidate_exercises = [
            {
                'exercise': '5km Continuous Baseline Aerobic Run',
                'type': 'endurance_run',
                'sets': 1,
                'reps': 'Continuous 5 km',
                'duration': '25 - 28 mins',
                'frequency': '3 days / week',
                'rest': 'Stretch cool-down',
                'intensity': 'Moderate - High',
                'progression': 'Maintain steady sub-25 min pacing across varying terrain.',
                'notes': 'Preserves aerobic conditioning and tactical physical endurance.'
            },
            {
                'exercise': 'Upper-Body Calisthenics Circuit (Chin-ups, Push-ups, Dips)',
                'type': 'upper_push_pull',
                'sets': 4,
                'reps': '10 pull-ups / 30 push-ups / 15 parallel dips',
                'duration': '20 mins',
                'frequency': '3 days / week',
                'rest': '60 sec between circuits',
                'intensity': 'High',
                'progression': 'Increase repetitions by 10% monthly.',
                'notes': 'Functional upper-body pushing and pulling power for military tasks.'
            },
            {
                'exercise': 'Battalion Sports (Volleyball / Football / Basketball / Cross-Country)',
                'type': 'team_sports',
                'sets': 1,
                'reps': 'Full match play',
                'duration': '45 - 60 mins',
                'frequency': '3 days / week',
                'rest': 'As per game',
                'intensity': 'Moderate - High',
                'progression': 'Actively participate in unit intramural and athletic tournaments.',
                'notes': 'Builds tactical team cohesion, rapid reaction time, and spatial agility.'
            },
            {
                'exercise': 'Core Stability Circuit & Isometric Plank Matrix',
                'type': 'core_circuit',
                'sets': 3,
                'reps': '60 sec front plank + 45 sec side planks',
                'duration': '10 mins',
                'frequency': '4 days / week',
                'rest': '45 sec',
                'intensity': 'Moderate',
                'progression': 'Integrate single-leg planks and dynamic leg raises.',
                'notes': 'Stabilizes spinal column under tactical gear and body armor.'
            },
            {
                'exercise': 'Dynamic Flexibility & Myofascial Recovery',
                'type': 'flexibility',
                'sets': 1,
                'reps': 'Full-body stretches and foam rolling',
                'duration': '15 mins',
                'frequency': 'Daily after PT',
                'rest': 'N/A',
                'intensity': 'Low',
                'progression': 'Sustain full joint mobility and muscle elasticity.',
                'notes': 'Mitigates injury risk, joint stiffness, and chronic muscle tightness.'
            }
        ]

    # Apply Medical Safety Filter for restricted / LMC soldiers
    safe_exercises, blocked_exercises = filter_unsafe_exercises(candidate_exercises, soldier_features)

    for ex in safe_exercises:
        if 'progression' in ex and 'progression_note' not in ex:
            ex['progression_note'] = ex['progression']
        elif 'progression_note' in ex and 'progression' not in ex:
            ex['progression'] = ex['progression_note']

    weekly_structure = [
        {"day": "Monday", "focus": "Cardiovascular Endurance & 5km Road Run", "session": "Morning Outdoor PT (06:00 - 07:15)"},
        {"day": "Tuesday", "focus": "Calisthenics & Strength Conditioning", "session": "Unit PT Ground (06:00 - 07:00)"},
        {"day": "Wednesday", "focus": "Tactical Obstacle Course & Rope Work", "session": "Morning Obstacle Track (06:00 - 07:15)"},
        {"day": "Thursday", "focus": "Core Stabilization & High-Tempo Sprint Shuttles", "session": "Morning PT (06:00 - 07:00)"},
        {"day": "Friday", "focus": "2.4km / 5km Speed Assessment Drill", "session": "Timed Speed Track (06:00 - 07:15)"},
        {"day": "Saturday", "focus": "Unit Team Sports & Active Recreation", "session": "Evening Sports (16:30 - 18:00)"},
        {"day": "Sunday", "focus": "Active Recovery & Dynamic Mobility Stretching", "session": "Rest & Foam Rolling"}
    ]

    return {
        'title': regimen_title,
        'focus_area': focus_area,
        'goal': goal,
        'exercises': safe_exercises,
        'blocked_exercises': blocked_exercises,
        'weekly_structure': weekly_structure
    }
