"""
Professional Individual Fitness Report Generator.
Renders HTML and converts to PDF using xhtml2pdf / pisa with military styling,
and overlays an official diagonal watermark with 'UNIT MANAGEMENT SYSTEM', IP address, and timestamp.
"""

import os
import io
import base64
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from ..config import TEMPLATES_DIR, DEFAULT_MODEL_VERSION

logger = logging.getLogger("fitness_trend.reports")


def get_jinja_env():
    """
    Returns configured Jinja2 environment pointing to the fitness templates folder.
    """
    return Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)


def get_certificate_logos():
    """
    Returns absolute file paths for RT and Chinar logos matching the navbar layout.
    Creates rounded Chinar logo if it doesn't already exist.
    Left: RT logo (15 CESR)
    Right: Chinar logo (15 Corps)
    """
    try:
        from PIL import Image, ImageDraw
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        static_dir = os.path.join(base_dir, "static")

        chinar_logo_path = os.path.abspath(os.path.join(static_dir, "image_for_login_page", "chinar.jpg"))
        rt_logo_path = os.path.abspath(os.path.join(static_dir, "image_for_login_page", "rt.jpg"))
        chinar_rounded_path = os.path.abspath(os.path.join(static_dir, "image_for_login_page", "chinar_rounded.jpg"))

        if not os.path.exists(chinar_rounded_path) and os.path.exists(chinar_logo_path):
            try:
                img = Image.open(chinar_logo_path).convert("RGBA")
                min_dim = min(img.size)
                left = (img.width - min_dim) / 2
                top = (img.height - min_dim) / 2
                right = (img.width + min_dim) / 2
                bottom = (img.height + min_dim) / 2
                img = img.crop((left, top, right, bottom))
                
                mask = Image.new("L", img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, min_dim, min_dim), fill=255)
                
                white_bg = Image.new("RGB", img.size, (255, 255, 255))
                white_bg.paste(img, mask=mask)
                white_bg.save(chinar_rounded_path, "JPEG")
            except Exception as e:
                logger.warning(f"Error cropping rounded chinar logo: {e}")
                chinar_rounded_path = chinar_logo_path
        elif not os.path.exists(chinar_logo_path):
            chinar_rounded_path = chinar_logo_path

        def to_base64_uri(file_path):
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as img_f:
                        b64_str = base64.b64encode(img_f.read()).decode("utf-8")
                        ext = file_path.rsplit(".", 1)[-1].lower()
                        mime = "image/png" if ext == "png" else "image/jpeg"
                        return f"data:{mime};base64,{b64_str}"
                except Exception:
                    return file_path
            return file_path

        return to_base64_uri(rt_logo_path), to_base64_uri(chinar_rounded_path)
    except Exception as e:
        logger.warning(f"Failed to get certificate logos: {e}")
        return "", ""


def get_regiment_banner_uri():
    """
    Generates and returns a high-resolution, military-grade header banner identical
    to the top application navigation banner:
    - 135-degree diagonal purple-to-indigo gradient (#3c425c to #764ba2)
    - Anti-aliased rounded corners
    - Left logo: 15 CESR insignia (rt.jpg) inside frosted rounded frame
    - Right logo: 15 Corps insignia (chinar.jpg) inside frosted rounded frame
    - Center Regiment Title: '15 CORPS ENGINEERING SIGNAL REGIMENT'
    - Frosted Pill: 'AI/ML INDIVIDUAL FITNESS PREDICTION & READINESS REPORT'
    - Subscript: 'UNIT MANAGEMENT SYSTEM • OFFICIAL MILITARY RECORD • CONFIDENTIAL'
    Caches the generated PNG to static assets for rapid reuse.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import json

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        static_dir = os.path.join(base_dir, "static")
        banner_cache_path = os.path.join(static_dir, "image_for_login_page", "pdf_header_banner.png")

        # Check navbar config for dynamic overrides
        navbar_cfg_file = os.path.join(static_dir, "uploads", "navbar", "config.json")
        header_text = "15 CORPS UNIT MANAGEMENT SYSTEM"
        left_logo_file = os.path.join(static_dir, "image_for_login_page", "rt.jpg")
        right_logo_file = os.path.join(static_dir, "image_for_login_page", "chinar.jpg")

        if os.path.exists(navbar_cfg_file):
            try:
                with open(navbar_cfg_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("header_text"):
                        header_text = cfg["header_text"].strip()
                    if cfg.get("left_logo"):
                        custom_left = os.path.abspath(os.path.join(base_dir, cfg["left_logo"].lstrip("/\\")))
                        if os.path.exists(custom_left):
                            left_logo_file = custom_left
                    if cfg.get("right_logo"):
                        custom_right = os.path.abspath(os.path.join(base_dir, cfg["right_logo"].lstrip("/\\")))
                        if os.path.exists(custom_right):
                            right_logo_file = custom_right
            except Exception as e:
                logger.debug(f"Error reading navbar config for banner: {e}")

        # If cache exists and is newer than logos and config, return cached URI
        cache_valid = False
        if os.path.exists(banner_cache_path):
            banner_mtime = os.path.getmtime(banner_cache_path)
            sources = [left_logo_file, right_logo_file]
            if os.path.exists(navbar_cfg_file):
                sources.append(navbar_cfg_file)
            if all(os.path.exists(s) and banner_mtime > os.path.getmtime(s) for s in sources):
                cache_valid = True

        if not cache_valid:
            width, height = 1600, 260
            radius = 32

            # Create true 135-degree diagonal gradient
            banner = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            grad = Image.new("RGBA", (width, height))
            r1, g1, b1 = 60, 66, 92      # #3c425c
            r2, g2, b2 = 118, 75, 162    # #764ba2

            for y in range(height):
                for x in range(width):
                    factor = ((x / float(width)) * 0.75 + (y / float(height)) * 0.25)
                    r = int(r1 + (r2 - r1) * factor)
                    g = int(g1 + (g2 - g1) * factor)
                    b = int(b1 + (b2 - b1) * factor)
                    grad.putpixel((x, y), (r, g, b, 255))

            # Apply rounded corner mask
            mask = Image.new("L", (width, height), 0)
            draw_m = ImageDraw.Draw(mask)
            draw_m.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=255)
            banner.paste(grad, (0, 0), mask=mask)

            draw_b = ImageDraw.Draw(banner)
            # Subtle outer frosted border
            draw_b.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, outline=(255, 255, 255, 45), width=2)

            def create_badge(img_path, size=(190, 190), badge_radius=36):
                orig = Image.open(img_path).convert("RGBA")
                badge = Image.new("RGBA", size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(badge)
                draw.rounded_rectangle(
                    [0, 0, size[0] - 1, size[1] - 1],
                    radius=badge_radius,
                    fill=(255, 255, 255, 45),
                    outline=(255, 255, 255, 90),
                    width=2
                )
                pad = 16
                inner_w = size[0] - pad * 2
                inner_h = size[1] - pad * 2
                orig.thumbnail((inner_w, inner_h), Image.Resampling.LANCZOS)
                pos_x = (size[0] - orig.width) // 2
                pos_y = (size[1] - orig.height) // 2
                inner_mask = Image.new("L", orig.size, 0)
                inner_draw = ImageDraw.Draw(inner_mask)
                inner_draw.rounded_rectangle(
                    [0, 0, orig.width - 1, orig.height - 1],
                    radius=max(6, badge_radius - pad // 2),
                    fill=255
                )
                badge.paste(orig, (pos_x, pos_y), mask=inner_mask)
                return badge

            # Left logo (15 CESR)
            if os.path.exists(left_logo_file):
                left_badge = create_badge(left_logo_file, size=(190, 190), badge_radius=36)
                banner.paste(left_badge, (35, (height - 190) // 2), mask=left_badge)

            # Right logo (15 Corps)
            if os.path.exists(right_logo_file):
                right_badge = create_badge(right_logo_file, size=(190, 190), badge_radius=36)
                banner.paste(right_badge, (width - 225, (height - 190) // 2), mask=right_badge)

            # Fonts
            font_path_bold = "C:/Windows/Fonts/arialbd.ttf"
            font_path_reg = "C:/Windows/Fonts/arial.ttf"
            if not os.path.exists(font_path_bold):
                font_path_bold = font_path_reg = "arial.ttf"

            try:
                title_font = ImageFont.truetype(font_path_bold, 44)
                sub_font = ImageFont.truetype(font_path_bold, 24)
                meta_font = ImageFont.truetype(font_path_reg, 19)
            except Exception:
                title_font = ImageFont.load_default()
                sub_font = ImageFont.load_default()
                meta_font = ImageFont.load_default()

            sub_text = "PERSONAL FITNESS REPORT"
            meta_text = "15 CORPS UNIT MANAGEMENT SYSTEM • OFFICIAL MILITARY RECORD • CONFIDENTIAL"

            # Draw Title
            t_box = draw_b.textbbox((0, 0), header_text, font=title_font)
            t_w = t_box[2] - t_box[0]
            draw_b.text(((width - t_w) // 2, 42), header_text, fill=(255, 255, 255, 255), font=title_font)

            # Draw Subtitle Pill
            s_box = draw_b.textbbox((0, 0), sub_text, font=sub_font)
            s_w = s_box[2] - s_box[0]
            pill_pad_x = 22
            pill_pad_y = 6
            pill_x0 = (width - s_w) // 2 - pill_pad_x
            pill_y0 = 118 - pill_pad_y
            pill_x1 = (width + s_w) // 2 + pill_pad_x
            pill_y1 = 118 + (s_box[3] - s_box[1]) + pill_pad_y
            draw_b.rounded_rectangle(
                [pill_x0, pill_y0, pill_x1, pill_y1],
                radius=18,
                fill=(15, 23, 42, 115),
                outline=(255, 255, 255, 60),
                width=1
            )
            draw_b.text(((width - s_w) // 2, 118), sub_text, fill=(255, 255, 255, 245), font=sub_font)

            # Draw Meta
            m_box = draw_b.textbbox((0, 0), meta_text, font=meta_font)
            m_w = m_box[2] - m_box[0]
            draw_b.text(((width - m_w) // 2, 185), meta_text, fill=(203, 213, 225, 210), font=meta_font)

            os.makedirs(os.path.dirname(banner_cache_path), exist_ok=True)
            banner.save(banner_cache_path, "PNG")

        with open(banner_cache_path, "rb") as bf:
            b64_str = base64.b64encode(bf.read()).decode("utf-8")
            return f"data:image/png;base64,{b64_str}"
    except Exception as err:
        logger.warning(f"Failed to generate regiment banner: {err}")
        return ""


def build_structured_fitness_report(soldier_features, prediction_result, recommendations, progression_data, client_ip="127.0.0.1", language="en"):
    """
    Constructs a comprehensive, standardized 16-section fitness report data payload.
    Ensures full compatibility across all 13 supported languages and maintains
    strict numeric immutability.
    """
    raw_army = str(soldier_features.get('army_number') or 'RECORD').strip()
    safe_army_no = "".join(c for c in raw_army if c.isalnum() or c in ("-", "_"))
    date_str = datetime.now().strftime("%Y%m%d")
    report_id = f"UMS-FIT-{date_str}-{safe_army_no}"
    timestamp_str = datetime.now().strftime("%d/%m/%Y, %I:%M %p")
    lang_code = (language or "en").lower().strip()

    # Section 1: Header / Cover
    header = {
        "title": "15 CORPS UNIT MANAGEMENT SYSTEM",
        "report_title": "PERSONAL FITNESS REPORT",
        "report_id": report_id,
        "date": timestamp_str,
        "army_number": soldier_features.get("army_number", ""),
        "name": soldier_features.get("name", ""),
        "rank": soldier_features.get("rank", ""),
        "company": soldier_features.get("company", ""),
        "language": lang_code.upper(),
        "confidential": "CONFIDENTIAL"
    }

    # Section 2: Personal & Fitness Profile
    profile = {
        "army_number": soldier_features.get("army_number", ""),
        "name": soldier_features.get("name", ""),
        "rank": soldier_features.get("rank", ""),
        "trade": soldier_features.get("trade", ""),
        "company": soldier_features.get("company", ""),
        "section": soldier_features.get("section", "N/A"),
        "age": soldier_features.get("age", "N/A"),
        "service_years": soldier_features.get("service_years", 0),
        "medical_status": "LMC" if soldier_features.get("has_medical_restriction") else "SHAPE-1"
    }

    # Section 3: Current Fitness Analysis
    height_cm = soldier_features.get("height_cm", 0)
    weight_kg = soldier_features.get("actual_weight_kg", 0)
    ideal_kg = soldier_features.get("ideal_weight_kg", "N/A")
    weight_diff = soldier_features.get("weight_difference_kg", 0)
    weight_dev = soldier_features.get("weight_deviation_percent", 0)
    bmi = soldier_features.get("bmi", 0)
    bmi_cat = soldier_features.get("bmi_category", "Normal")
    weight_stat = soldier_features.get("weight_status", "Normal")
    bpet = soldier_features.get("bpet_grade", "Untested")
    ppt = soldier_features.get("ppt_grade", "Untested")
    sports = soldier_features.get("sports_list", "None")
    sport_count = soldier_features.get("sport_count", 0)
    activity = soldier_features.get("physical_activity_level", "Moderate")

    analysis = {
        "height_cm": height_cm,
        "actual_weight_kg": weight_kg,
        "ideal_weight_kg": ideal_kg,
        "weight_status": weight_stat,
        "weight_difference_kg": weight_diff,
        "weight_deviation_percent": weight_dev,
        "bmi": bmi,
        "bmi_category": bmi_cat,
        "medical_status": "LMC" if soldier_features.get("has_medical_restriction") else "SHAPE-1",
        "bpet_grade": bpet,
        "ppt_grade": ppt,
        "sports_list": sports,
        "sport_count": sport_count,
        "activity_level": activity,
        "condition_summary": f"Current BMI of {bmi} classified as {bmi_cat} with {str(weight_stat).lower()} weight status."
    }

    # Section 4: AI Fitness Assessment
    fit_score = prediction_result.get("fitness_score", 75)
    cat_label = prediction_result.get("category_label", "Good")
    conf_score = prediction_result.get("confidence_score", 85)
    tier = "Tier 1 Combat Ready" if fit_score >= 80 else ("Tier 2 Deployable" if fit_score >= 60 else "Tier 3 Monitored Conditioning")
    assessment = {
        "fitness_score": fit_score,
        "category_label": cat_label,
        "confidence_score": conf_score,
        "readiness_tier": tier
    }

    # Section 5: AI Fitness Prediction
    prediction = {
        "fitness_score": fit_score,
        "category_label": cat_label,
        "confidence_score": conf_score,
        "algorithm": prediction_result.get("algorithm", "GradientBoosting Classifier"),
        "model_version": prediction_result.get("model_version", DEFAULT_MODEL_VERSION),
        "predicted_status": prediction_result.get("predicted_status", cat_label),
        "strengths": prediction_result.get("strengths", ["Consistent aerobic stamina", "Optimal BMI range"]),
        "improvements": prediction_result.get("improvements", ["Increase core endurance repetitions", "Sustain structured hydration routine"])
    }

    # Section 6: Weight / Fitness Trend
    trend = {
        "baseline_weight": weight_kg,
        "target_weight": ideal_kg,
        "current_bmi": bmi,
        "notice": "Historical trend data unavailable for this record. Baseline weight and ideal target benchmarks are established for continuous tracking."
    }

    # Section 7: Fitness Progression
    progression_milestones = progression_data.get("milestones") if isinstance(progression_data, dict) else None
    if not progression_milestones:
        progression_milestones = [
            {"period": "Current Baseline", "weight_kg": weight_kg, "bmi": bmi, "fitness_score": fit_score},
            {"period": "30 Days Milestone", "weight_kg": round(float(weight_kg) * 0.99, 1) if weight_kg else 0, "bmi": round(float(bmi) * 0.99, 1) if bmi else 0, "fitness_score": min(100, fit_score + 4)},
            {"period": "60 Days Milestone", "weight_kg": round(float(weight_kg) * 0.98, 1) if weight_kg else 0, "bmi": round(float(bmi) * 0.98, 1) if bmi else 0, "fitness_score": min(100, fit_score + 8)},
            {"period": "90 Days Milestone", "weight_kg": round(float(weight_kg) * 0.97, 1) if weight_kg else 0, "bmi": round(float(bmi) * 0.97, 1) if bmi else 0, "fitness_score": min(100, fit_score + 12)}
        ]
    progression = {
        "milestones": progression_milestones,
        "chart_data": progression_data.get("chart_data", {}) if isinstance(progression_data, dict) else {}
    }

    # Section 8: Personalized Exercise Plan
    rec_ex = recommendations.get("exercise", {}) if isinstance(recommendations, dict) else {}
    exercises_list = rec_ex.get("exercises", [])
    if not exercises_list:
        exercises_list = [
            {"exercise": "5 km Endurance Run", "sets": 1, "reps": "Continuous 5 km", "duration": "25-30 mins", "frequency": "3 days / week", "rest": "5 mins walk", "intensity": "Moderate - High", "progression": "Target steady sub-25 min pace."},
            {"exercise": "Military Push-ups", "sets": 3, "reps": "20-25 reps", "duration": "10 mins", "frequency": "4 days / week", "rest": "60 sec", "intensity": "Moderate - High", "progression": "Add 2 reps weekly."},
            {"exercise": "Military Sit-ups", "sets": 3, "reps": "25-30 reps", "duration": "10 mins", "frequency": "4 days / week", "rest": "60 sec", "intensity": "Moderate", "progression": "Target 40 reps in 2 mins."},
            {"exercise": "Strict Chin-ups", "sets": 3, "reps": "6-10 reps", "duration": "8 mins", "frequency": "3 days / week", "rest": "90 sec", "intensity": "High", "progression": "Target 10+ consecutive reps."},
            {"exercise": "Core Rigidity Plank", "sets": 3, "reps": "60 sec hold", "duration": "8 mins", "frequency": "Daily", "rest": "45 sec", "intensity": "Moderate", "progression": "Increase hold time by 5s weekly."}
        ]
    exercise_plan = {
        "title": rec_ex.get("title") or rec_ex.get("plan_name", "Tactical Operational Conditioning"),
        "focus_area": rec_ex.get("focus_area", "Cardiorespiratory Stamina & Muscular Endurance"),
        "exercises": exercises_list,
        "weekly_structure": rec_ex.get("weekly_structure", [])
    }

    # Section 9: Personalized Nutrition Recommendations (Mess Menu Constrained)
    rec_diet = recommendations.get("diet", {}) if isinstance(recommendations, dict) else {}
    nutrition = {
        "mess_category": rec_diet.get("mess_category", "OR MESS"),
        "day_of_week": rec_diet.get("day_of_week", datetime.now().strftime('%A')),
        "target_calories": rec_diet.get("target_calories", 2500),
        "hydration_liters": rec_diet.get("hydration_liters", 3.5),
        "strategy": rec_diet.get("strategy", "High Protein Balanced Active Military Diet"),
        "macros": rec_diet.get("macros", {
            "protein_grams": 130, "protein_pct": 25,
            "carb_grams": 300, "carb_pct": 55,
            "fat_grams": 55, "fat_pct": 20,
            "fiber_grams": 35
        }),
        "daily_targets": rec_diet.get("daily_targets", {
            "calories": rec_diet.get("target_calories", 2500),
            "protein": 130,
            "carbs": 300,
            "fat": 55,
            "fiber": 35,
            "hydration": rec_diet.get("hydration_liters", 3.5)
        }),
        "estimated_intake": rec_diet.get("estimated_intake", {
            "calories": rec_diet.get("target_calories", 2500),
            "protein": 125,
            "carbs": 295,
            "fat": 52,
            "fiber": 34
        }),
        "mess_nutrition_plan": rec_diet.get("mess_nutrition_plan", {}),
        "weekly_schedule": rec_diet.get("weekly_schedule", {}),
        "weekly_schedule_list": rec_diet.get("weekly_schedule_list", []),
        "roadmap_30d": rec_diet.get("roadmap_30d", []),
        "optional_diet_plan": rec_diet.get("optional_diet_plan", [
            {"item": "Hydration Fluid", "recommendation": "Minimum 3.5 Liters of clean water daily, paced across training sessions."},
            {"item": "Seasonal Fresh Fruit", "recommendation": "1 whole seasonal fruit (orange/guava/apple) during mid-morning if available."},
            {"item": "Operational Electrolytes", "recommendation": "Lemon water with a pinch of black salt during high-heat field drills."}
        ]),
        "sample_menu": rec_diet.get("sample_menu", []),
        "recommended_items": rec_diet.get("recommended_items") or [
            "Authorized mess dal, lentils, and lean poultry for muscle repair",
            "Complex carbohydrate portions (chapati, rice) calibrated to physical exertion",
            "Seasonal vegetables and fresh salads from unit rations for vital micronutrients",
            "Consistent daily hydration of minimum 3.5 Liters of clean water"
        ],
        "limit_items": rec_diet.get("limit_items") or [
            "Excessive portions of calorie-dense fried snacks (pakoras, puris) beyond recommendation",
            "Refined sugar, sugary tea/coffee, and carbonated beverages",
            "Excessive table salt, pickles, and high-sodium processed rations",
            "Skipping scheduled breakfast prior to morning physical training",
            "Consuming heavy meals less than 2 hours before lights out"
        ],
        "guidelines": rec_diet.get("dietary_guidelines") or [
            "Meal Timing Discipline: Ensure dinner is finished at least 2 hours before sleep; consume recovery protein within 45 minutes after intensive PT.",
            "Operational Hydration: Consume 500 ml of clean water 30 minutes prior to outdoor drills; maintain continuous fluid replenishment in hot terrain.",
            "Mess Selection Strategy: Prioritize roasted, boiled, or grilled mess items over deep-fried curries; incorporate fresh salads and curd daily."
        ]
    }

    # Section 10: Areas for Improvement
    improvements = prediction.get("improvements", [])
    if not improvements:
        improvements = [
            "Sustain aerobic volume to optimize metabolic rate",
            "Enhance core endurance with daily plank and abdominal circuits",
            "Maintain scheduled hydration intake across high-intensity training"
        ]
    improvement_areas = improvements

    # Section 11: Priority Recommendations
    priority_recs = [
        {
            "priority": "Priority 1 - Aerobic & Functional Readiness",
            "title": "Cardiovascular Interval Training",
            "detail": "Complete 3 weekly structured running and sprinting intervals to elevate peak aerobic VO2 capacity."
        },
        {
            "priority": "Priority 2 - Muscular & Core Conditioning",
            "title": "Calisthenic Resistance Circuits",
            "detail": "Execute progressive sets of push-ups, sit-ups, chin-ups, and 60-second core planks."
        },
        {
            "priority": "Priority 3 - Nutrition & Recovery Protocol",
            "title": "Nutrient Timing & Hydration Discipline",
            "detail": "Target prescribed hydration liters daily and consume high-protein post-training recovery meals."
        }
    ]

    # Section 12: Fitness Goals
    goals = {
        "short_term": "Achieve 100% adherence to scheduled exercise drills and daily hydration targets across the next 30 days.",
        "medium_term": "Reduce BPET 5 km run timing by 45 seconds and record 30 consecutive push-ups within 60 days.",
        "long_term": "Reach peak operational readiness with an EXCELLENT BPET/PPT grade and sustain target BMI benchmark over 90 days."
    }

    # Section 13: Progress Monitoring
    monitoring = [
        {"parameter": "Body Weight (kg)", "current": f"{weight_kg} kg", "target": f"{ideal_kg} kg" if ideal_kg != "N/A" else f"{weight_kg} kg", "frequency": "Weekly"},
        {"parameter": "Body Mass Index (BMI)", "current": f"{bmi}", "target": "22.0 - 24.9", "frequency": "Bi-weekly"},
        {"parameter": "BPET Grading", "current": bpet if bpet != "Untested" else "Untested", "target": "EXCELLENT", "frequency": "Monthly"},
        {"parameter": "PPT Grading", "current": ppt if ppt != "Untested" else "Untested", "target": "EXCELLENT", "frequency": "Quarterly"}
    ]

    # Section 14: AI Fitness Insights
    insights = {
        "overall_assessment": f"Soldier demonstrates a solid military fitness baseline with an AI readiness score of {fit_score}/100 ({cat_label}).",
        "recommended_focus": "Integrate functional resistance conditioning with targeted aerobic intervals to maximize operational stamina.",
        "key_strengths": prediction.get("strengths", []),
        "primary_areas": prediction.get("improvements", [])
    }

    # Section 15: Important Note / Disclaimer
    disclaimer = "This fitness evaluation is an AI-assisted analytical assessment based on standard military physical parameters. It should be used in conjunction with qualified unit physical training instructors and medical officer recommendations."

    # Section 16: Footer
    footer = {
        "report_id": report_id,
        "regiment": "UNIT MANAGEMENT SYSTEM",
        "sub": "UNIT MANAGEMENT SYSTEM • OFFICIAL MILITARY RECORD • CONFIDENTIAL",
        "client_ip": client_ip,
        "timestamp": timestamp_str
    }

    return {
        "header": header,
        "profile": profile,
        "analysis": analysis,
        "assessment": assessment,
        "prediction": prediction,
        "trend": trend,
        "progression": progression,
        "exercise_plan": exercise_plan,
        "nutrition": nutrition,
        "improvement_areas": improvement_areas,
        "priority_recs": priority_recs,
        "goals": goals,
        "monitoring": monitoring,
        "insights": insights,
        "disclaimer": disclaimer,
        "footer": footer,
        "report_id": report_id,
        "language": lang_code,
        "generated_at": timestamp_str,
        "client_ip": client_ip,
        # backward-compatibility references:
        "soldier": soldier_features,
        "recommendations": recommendations,
    }


def generate_fitness_html_report(soldier_features, prediction_result, recommendations, progression_data, client_ip="127.0.0.1", lang="en"):
    """
    Renders the standalone printable HTML report string using pdf_template.html.
    """
    from ..translation import get_report_labels, translate_16section_report
    env = get_jinja_env()
    template = env.get_template("fitness_trend/pdf_template.html")
    rt_logo_path, chinar_logo_path = get_certificate_logos()
    target_lang = (lang or 'en').lower().strip()
    banner_image_path = get_regiment_banner_uri() if target_lang == 'en' else ""

    structured_report = build_structured_fitness_report(
        soldier_features=soldier_features,
        prediction_result=prediction_result,
        recommendations=recommendations,
        progression_data=progression_data,
        client_ip=client_ip,
        language=target_lang
    )

    if target_lang != 'en':
        t_report = translate_16section_report(structured_report, target_lang=target_lang, for_pdf=False)
        labels = get_report_labels(target_lang, for_pdf=False)
    else:
        t_report = structured_report
        labels = get_report_labels('en', for_pdf=False)

    from ..pdf.chart_generator import generate_progression_line_chart_uri
    progression_chart_uri = generate_progression_line_chart_uri(
        progression_data=t_report.get('progression', progression_data),
        title="90-Day Physical Readiness & Weight Projection Curve",
        lang=target_lang
    )

    watermark_datetime = datetime.now().strftime('%d/%m/%Y %I:%M %p')
    rendered_html = template.render(
        report=t_report,
        soldier=t_report.get('soldier', soldier_features),
        prediction=t_report.get('prediction', prediction_result),
        recommendations=t_report.get('recommendations', recommendations),
        progression=t_report.get('progression', progression_data),
        labels=labels,
        client_ip=client_ip,
        watermark_text="UMS 15 CESR",
        watermark_datetime=watermark_datetime,
        show_html_watermark=True,
        lang=target_lang,
        direction="rtl" if target_lang == "ur" else "ltr",
        is_rtl=(target_lang == "ur"),
        progression_chart_uri=progression_chart_uri,
        generated_at=t_report.get('generated_at'),
        model_version=prediction_result.get('model_version', DEFAULT_MODEL_VERSION),
        chinar_logo_path=chinar_logo_path,
        rt_logo_path=rt_logo_path,
        banner_image_path=banner_image_path
    )
    return rendered_html


def overlay_watermark_on_pdf(base_pdf_stream, client_ip="127.0.0.1", watermark_text="UMS 15 CESR"):
    """
    Overlays a clear, single diagonal military watermark on top of each page of the generated PDF using ReportLab and pypdf.
    Includes Unit Name, IP Address, and Date & Time stamp (in 12-hour format) centered on each page.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            from PyPDF2 import PdfReader, PdfWriter

        # Create 1-page watermark PDF in memory
        wm_buffer = io.BytesIO()
        # A4 size in points: 595.27 x 841.89
        c = canvas.Canvas(wm_buffer, pagesize=(595.27, 841.89))
        
        # Position origin at center of the page and rotate 35 degrees
        cx, cy = 595.27 / 2.0, 841.89 / 2.0
        c.translate(cx, cy)
        c.rotate(35)
        
        # Slate color with clear visibility (0.22 opacity)
        c.setFillColor(colors.HexColor('#334155'))
        try:
            c.setFillAlpha(0.22)
        except Exception:
            pass

        # 12-hour format timestamp with AM/PM
        dt_str = datetime.now().strftime('%d/%m/%Y %I:%M %p')
        
        # Centered diagonal watermark block per page with clear military visibility
        c.setFont("Helvetica-Bold", 34)
        c.drawCentredString(0, 26, watermark_text)
        
        c.setFont("Helvetica-Bold", 17)
        c.drawCentredString(0, 2, f"IP ADDRESS: {client_ip}")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(0, -20, f"DATE & TIME: {dt_str}")
        
        c.showPage()
        c.save()
        wm_buffer.seek(0)
        
        # Merge watermark ON TOP of document page content (1 watermark per page)
        base_pdf_stream.seek(0)
        base_reader = PdfReader(base_pdf_stream)
        wm_bytes = wm_buffer.getvalue()
        
        writer = PdfWriter()
        for page in base_reader.pages:
            wm_reader = PdfReader(io.BytesIO(wm_bytes))
            wm_page = wm_reader.pages[0]
            new_page = writer.add_page(page)
            new_page.merge_page(wm_page)
            
        final_stream = io.BytesIO()
        writer.write(final_stream)
        final_stream.seek(0)
        return final_stream
    except Exception as wm_err:
        logger.warning(f"Watermark overlay failed, returning base PDF stream: {wm_err}")
        base_pdf_stream.seek(0)
        return base_pdf_stream


def generate_fitness_pdf_report(soldier_features, prediction_result, recommendations, progression_data, client_ip="127.0.0.1", watermark_text="UMS 15 CESR", lang="en", language=None):
    """
    Generates a high-quality PDF binary stream with AI prediction, recommendations, progression,
    and an official 'UNIT MANAGEMENT SYSTEM' with IP address watermark.
    Supports multilingual generation.
    
    Returns:
        io.BytesIO stream containing the generated PDF document, or None if error occurs.
    """
    target_lang = language or lang or "en"
    try:
        from ..pdf.report_generator import generate_multilingual_fitness_pdf
        return generate_multilingual_fitness_pdf(
            soldier_features=soldier_features,
            prediction_result=prediction_result,
            recommendations=recommendations,
            progression_data=progression_data,
            client_ip=client_ip,
            watermark_text=watermark_text,
            language=target_lang
        )
    except Exception as e:
        logger.error(f"Failed to generate fitness PDF report: {e}", exc_info=True)
        return None
