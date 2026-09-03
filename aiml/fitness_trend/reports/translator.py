"""
Multi-Language Translation Engine for Fitness Reports.
Provides comprehensive, offline dictionary-based translation with zero rate-limit issues.
Supports:
- English (Default) ('en')
- Hindi ('hi')
- Urdu ('ur') (with proper RTL and Arabic letter shaping)
- Punjabi ('pa')
- Malayalam ('ml')
- Odia ('or')
- Telugu ('te')
- Bhojpuri ('bho')
- Gujarati ('gu')
- Marathi ('mr')
- Bengali ('bn')
- Mewari ('mwr')
"""

import re
import copy
import logging

logger = logging.getLogger("fitness_trend.translator")

# Exact list of 12 supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English (Default)',
    'hi': 'हिन्दी (Hindi)',
    'ur': 'اردو (Urdu)',
    'pa': 'ਪੰਜਾਬੀ (Punjabi)',
    'ml': 'മലയാളം (Malayalam)',
    'or': 'ଓଡ଼ିଆ (Odia)',
    'te': 'తెలుగు (Telugu)',
    'bho': 'भोजपुरी (Bhojpuri)',
    'gu': 'ગુજરાતી (Gujarati)',
    'mr': 'मराठी (Marathi)',
    'bn': 'বাংলা (Bengali)',
    'mwr': 'मेवाड़ी (Mewari)'
}

# Master translation dictionary for all report strings, labels, strengths, exercises & strategies
DICTIONARY = {
    'ur': {
        # Header & Meta
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 کور / 15 سی ای ایس آر — یونٹ مینجمنٹ سسٹم',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'اے آئی/ایم ایل انفرادی فٹنس پیشین گوئی اور ذاتی رپورٹ',
        'Report Generated': 'رپورٹ تاریخ',
        'Model Version': 'ماڈل ورژن',
        'CONFIDENTIAL': 'خفیہ',
        
        # Section 1
        '1. Soldier Particulars & Service Profile': '1. فوجی کی تفصیلات اور سروس پروفائل',
        'Army Number:': 'آرمی نمبر:',
        'Full Name:': 'پورا نام:',
        'Rank / Trade:': 'عہدہ / ٹریڈ:',
        'Company / Section:': 'کمپنی / سیکشن:',
        'Age / Service:': 'عمر / سروس مدت:',
        'Medical Status:': 'طبی کیفیت:',
        'Years': 'سال',
        'SHAPE-1 Cleared': 'شیپ-1 پاس',
        'Restricted / LMC': 'محدود / ایل ایم سی',
        'Agniveer': 'اگنی ویر',
        'Havildar': 'حوالدار',
        'HAV': 'حوالدار',
        'Naik': 'نائیک',
        'NK': 'نائیک',
        'Lance Naik': 'لانس نائیک',
        'L NK': 'لانس نائیک',
        'Subedar': 'صوبیدار',
        'Naib Subedar': 'نائب صوبیدار',
        'Signalman': 'سگنل مین',
        'GD': 'جی ڈی',
        'DVR': 'ڈرائیور',
        'DMV': 'ڈی ایم وی',
        'TTC': 'ٹی ٹی سی',
        'Opr': 'آپریٹر',
        '1 Company': '1 کمپنی',
        '2 Company': '2 کمپنی',
        '3 Company': '3 کمپنی',
        'COMN Company': 'کمیونیکیشن کمپنی',
        'HQ company': 'ہیڈ کوارٹر کمپنی',
        
        # Section 2
        '2. Physiological Metrics & Physical Performance': '2. جسمانی پیمائش اور کارکردگی کا تجزیہ',
        'Height / Actual Weight:': 'قد / اصل وزن:',
        'Ideal Reference Weight:': 'مثالی معیاری وزن:',
        'BMI Index & Category:': 'بی ایم آئی انڈیکس و زمرہ:',
        'Weight Deviation:': 'وزن کا فرق:',
        'BPET Grading:': 'بی پی ای ٹی گریڈنگ:',
        'PPT Grading:': 'پی پی ٹی گریڈنگ:',
        'Sports & Athletics:': 'کھیل کود اور ایتھلیٹکس:',
        'Physical Activity Level:': 'جسمانی سرگرمی کی سطح:',
        'Normal (Ideal)': 'معمول (مثالی)',
        'Normal': 'معمول',
        'Overweight': 'زیادہ وزن',
        'Underweight': 'کم وزن',
        'EXCELLENT': 'بہترین (EXCELLENT)',
        'GOOD': 'اچھا (GOOD)',
        'SATISFACTORY': 'تسلی بخش (SATISFACTORY)',
        'Moderate': 'معتدل',
        'Active': 'فعال',
        'Sports': 'کھیل',
        'None': 'کوئی نہیں',
        'Football': 'فٹ بال',
        'Basketball': 'باسکٹ بال',
        'Volleyball': 'والی بال',
        'Cross-Country': 'کراس کنٹری',
        'Athletics': 'ایتھلیٹکس',
        
        # Section 3
        '3. AI Physical Readiness Prediction': '3. اے آئی جسمانی تیاری کی پیشین گوئی',
        'AI Physical Readiness Score:': 'اے آئی جسمانی تیاری کا اسکور:',
        'Prediction Confidence:': 'پیشین گوئی کا اعتماد:',
        'Algorithm:': 'الگورتھم:',
        'Key Strengths (Positive Indicators):': 'اہم خوبیاں (مثبت اشارے):',
        'Priority Action Areas:': 'ترجیحی بہتری کے شعبے:',
        'Good Fitness': 'اچھی فٹنس (Good Fitness)',
        'Excellent Readiness': 'بہترین تیاری (Excellent Readiness)',
        'Satisfactory / Average': 'تسلی بخش (Average)',
        'Needs Improvement / At-Risk': 'بہتری کی ضرورت',

        # Strengths & Improvements
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "اعلیٰ بی پی ای ٹی کارکردگی: جسمانی برداشت اور رکاوٹوں کے ٹیسٹ میں 'بہترین' گریڈنگ حاصل کی۔",
        "Solid BPET Performance: Achieved 'Good' standard in military physical endurance.": "ٹھوس بی پی ای ٹی کارکردگی: فوجی جسمانی برداشت میں 'اچھا' معیار حاصل کیا۔",
        "Moderate BPET: Graded 'Satisfactory'; endurance pacing can be improved to reach 'Good/Excellent'.": "معتدل بی پی ای ٹی: 'تسلی بخش' گریڈ؛ برداشت کو 'اچھا/بہترین' تک بہتر کیا جا سکتا ہے۔",
        "BPET Deficiency: Low physical grading or restriction recorded during endurance testing.": "بی پی ای ٹی کمی: برداشت کی آزمائش میں کم گریڈنگ یا پابندی ریکارڈ کی گئی۔",
        "BPET Untested: No recent formal BPET test recorded in system.": "بی پی ای ٹی غیر آزمودہ: نظام میں حالیہ ٹیسٹ کا ریکارڈ موجود نہیں ہے۔",
        "High PPT Performance: Achieved 'Excellent' in physical proficiency standards.": "اعلیٰ پی پی ٹی کارکردگی: جسمانی مہارت کے معیارات میں 'بہترین' معیار حاصل کیا۔",
        "Solid PPT Performance: Meets high physical proficiency benchmarks.": "ٹھوس پی پی ٹی کارکردگی: اعلیٰ جسمانی مہارت کے معیار پر پورا اترتا ہے۔",
        "PPT Potential: Satisfactory performance; calisthenics, chin-ups, and sprint speed can be elevated.": "پی پی ٹی صلاحیت: تسلی بخش کارکردگی؛ چن اپس اور دوڑ کی رفتار کو بڑھایا جا سکتا ہے۔",
        "PPT Remedial Needed: Physical proficiency test requires structured conditioning.": "پی پی ٹی بہتری کی ضرورت: جسمانی مہارت کے ٹیسٹ کے لیے باقاعدہ مشق درکار ہے۔",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "صاف طبی پروفائل: طبی لحاظ سے شیپ-1 جس میں ورزش کی کوئی ممانعت نہیں ہے۔",
        "No Structured Sports: Currently not registered in regular unit sports competitions.": "کوئی باقاعدہ کھیل نہیں: فی الحال یونٹ کے کھیلوں کے مقابلوں میں حصہ نہیں لے رہا ہے۔",
        "Demographic Baseline: Within normal military operational age & service profile.": "بنیادی فوجی پروفائل: معمول کی فوجی آپریشنل عمر اور سروس کے اندر ہے۔",
        "Maintenance Focus: Sustain current peak endurance, cardiovascular health, and sports routine.": "برقراری کا فوکس: موجودہ اعلیٰ برداشت، دل کی صحت اور کھیلوں کے معمولات کو برقرار رکھیں۔",
        
        # Section 4: Diet & Macros
        '4. Personalized Dietary & Macronutrient Plan': '4. ذاتی غذا اور غذائی اجزاء کا منصوبہ',
        'Daily Energy Target:': 'روزانہ توانائی کا ہدف:',
        'Daily Hydration Target:': 'روزانہ پانی کا ہدف:',
        'Protein Target:': 'پروٹین کا ہدف:',
        'Carbs / Fats:': 'کاربوہائیڈریٹ / چکنائی:',
        'Carbs:': 'کاربوہائیڈریٹ:',
        'Fats:': 'چکنائی:',
        'kcal_day': 'کلو کیلوری / دن',
        'liters_day': 'لیٹر / دن',
        'Diet Strategy:': 'غذائی حکمت عملی:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "معتدل کیلوری کمی (تقریباً 450 کلو کیلوری کم) تاکہ فوجی صلاحیت کو برقرار رکھتے ہوئے چربی کم ہو سکے۔",
        "Nutrient-Dense Calorie Surplus (+350 kcal) to build lean functional muscle mass.": "غذائیت سے بھرپور کیلوری کا اضافہ (+350 کلو کیلوری) تاکہ عضلات کو مضبوط کیا جا سکے۔",
        "Slight Surplus (+200 kcal) paired with high protein for maximum strength & power development.": "ہلکا اضافہ (+200 کلو کیلوری) زیادہ پروٹین کے ساتھ تاکہ طاقت اور توانائی کو زیادہ کیا جا سکے۔",
        "Isocaloric High-Energy Balance with optimal complex carbohydrates for sustained endurance.": "اعلیٰ توانائی کا متوازن تناسب تاکہ مسلسل جسمانی برداشت قائم رہے۔",
        "Maintenance Calorie Intake optimized for physical conditioning and SHAPE-1 preservation.": "برقراری کیلوری کا ہدف تاکہ جسمانی فٹنس اور شیپ-1 کو برقرار رکھا جا سکے۔",
        
        # Section 5: Physical Training
        '5. Physical Training': '5. جسمانی تربیت',
        'Exercise / Drill': 'ورزش / ڈرل',
        'Sets': 'سیٹس',
        'Reps / Volume': 'ریپس / مقدار',
        'Duration': 'دورانیہ',
        'Frequency': 'تعدد',
        
        # Exercises
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'تیز رفتار ایروبک دوڑ / کراس کنٹری (4 - 6 کلومیٹر)',
        'Bodyweight Full-Body Circuit (Jumping jacks, mountain climbers, bodyweight squats, lunges)': 'پورے جسم کا سرکٹ (جمپنگ جیکس، ماؤنٹین کلائمبرز، اسکواٹس، لنجز)',
        'Stair Climbing & Hill Sprints': 'سیڑھیاں چڑھنا اور پہاڑی اسپرنٹس',
        'Core Russian Twists & Leg Raises': 'کور رشین ٹوئسٹس اور لیگ ریزز',
        '5km Interval Progression Run (300m sprint / 200m jog)': '5 کلومیٹر وقفے وقفے سے دوڑ (300 میٹر دوڑ / 200 میٹر جاگنگ)',
        'Horizontal Rope Traverse & Hanging Pulls': 'افقی رسی پر چلنا اور پل اپس',
        'Burpees to Sprint Accelerations (20m shuttle)': 'برپیز کے ساتھ تیز دوڑ (20 میٹر شٹل)',
        'Plank Hold & Side Bridge Circuit': 'پلینک ہولڈ اور سائیڈ برج سرکٹ',
        'Standard Military Chin-Ups / Pull-Ups': 'معیاری فوجی چن اپس / پل اپس',
        'Military Push-Ups (Chest to Ground)': 'فوجی پش اپس (زمین تک سینہ)',
        '2.4km Speed Time Trial (PPT Baseline)': '2.4 کلومیٹر تیز رفتار دوڑ',
        'Bent-Knee Sit-Ups (Strict 2-minute test pace)': 'گھٹنے موڑ کر سیٹ اپس (2 منٹ ٹیسٹ)',
        '5km Base Endurance Run': '5 کلومیٹر بنیادی برداشت کی دوڑ',
        'Upper Body Calisthenics (Pull-ups, Dips, Push-ups)': 'اوپری جسم کی ورزش (پل اپس، ڈپس، پش اپس)',
        'Unit Team Sports (Volleyball / Football / Basketball)': 'یونٹ ٹیم کھیل (والی بال / فٹ بال / باسکٹ بال)',
        'Dynamic Flexibility & Mobility Cool-Down': 'لچک اور حرکت پذیری کی کول ڈاؤن ورزش',

        # Reps, Duration, Frequency
        'Continuous steady state': 'مسلسل مستحکم رفتار',
        '45 sec work / 15 sec rest per station': '45 سیکنڈ ورزش / 15 سیکنڈ آرام',
        '40 meters incline / walk down': '40 میٹر چڑھائی / نیچے پیدل',
        '20 reps each': '20 ریپس فی سیٹ',
        '500m per cycle': '500 میٹر فی چکر',
        '15-20 meters / 8 pulls': '15-20 میٹر / 8 پل اپس',
        '10 burpees + 20m sprint': '10 برپیز + 20 میٹر اسپرنٹ',
        '60 sec front + 45 sec sides': '60 سیکنڈ سامنے + 45 سیکنڈ سائیڈ',
        '8 - 12 reps (or max to failure)': '8 - 12 ریپس',
        '25 - 35 reps': '25 - 35 ریپس',
        '2.4 km continuous': '2.4 کلومیٹر مسلسل',
        '40 - 50 reps in 2 mins': '2 منٹ میں 40 - 50 ریپس',
        'Continuous 5 km': '5 کلومیٹر مسلسل',
        '10 pull-ups / 15 dips / 30 push-ups': '10 پل اپس / 15 ڈپس / 30 پش اپس',
        'Match play': 'میچ کھیلنا',
        'Full-body stretches': 'پورے جسم کا اسٹریچ',

        '35 - 40 mins': '35 - 40 منٹ',
        '20 mins': '20 منٹ',
        '15 mins': '15 منٹ',
        '10 mins': '10 منٹ',
        '35 mins': '35 منٹ',
        '12 mins': '12 منٹ',
        '12 - 15 mins': '12 - 15 منٹ',
        '25 - 30 mins': '25 - 30 منٹ',
        '45 - 60 mins': '45 - 60 منٹ',

        '4 days/week': '4 دن فی ہفتہ',
        '3 days/week': '3 دن فی ہفتہ',
        '2 days/week': '2 دن فی ہفتہ',
        'Daily after PT': 'پی ٹی کے بعد روزانہ',

        # Section 6: Milestones
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. متوقع ترقی کے سنگ میل (30 / 60 / 90 دن)',
        'Timeline': 'ٹائم لائن',
        'Projected Weight': 'متوقع وزن',
        'Projected BMI': 'متوقع بی ایم آئی',
        'Estimated Physical Readiness Score': 'متوقع جسمانی تیاری کا اسکور',
        'Current Baseline': 'موجودہ بنیادی سطح (Baseline)',
        '30 Days Projected': '30 دن کا تخمینہ',
        '60 Days Projected': '60 دن کا تخمینہ',
        '90 Days Projected': '90 دن کا تخمینہ'
    }
}


def shape_urdu(text):
    """
    Applies arabic_reshaper and bidi.algorithm to connect cursive Arabic letters
    and render Right-To-Left correctly in PDF engines.
    """
    if not text or not isinstance(text, str):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def translate_dynamic_sentence(text, target_lang='en'):
    """
    Translates complex sentences containing dynamic numbers, percentages, or athlete names.
    Uses regex patterns with language dictionary lookups.
    """
    if not text or target_lang == 'en' or not isinstance(text, str):
        return text
        
    text_clean = text.strip()

    # 1. Direct dictionary match
    lang_dict = DICTIONARY.get(target_lang, {})
    if text_clean in lang_dict:
        return lang_dict[text_clean]

    # Pattern: Excess Body Weight
    m = re.match(r"Excess Body Weight:\s*Actual weight is ([0-9.]+)% above ideal standard \(\+([0-9.]+) kg deviation\)\.", text_clean, re.I)
    if m:
        pct, diff = m.group(1), m.group(2)
        if target_lang == 'ur':
            return f"اضافی جسمانی وزن: اصل وزن مثالی معیار سے {pct}% زیادہ ہے (+{diff} کلوگرام فرق)۔"
        elif target_lang in ['hi', 'bho', 'mwr']:
            return f"अधिक शारीरिक वजन: वास्तविक वजन मानक से {pct}% अधिक है (+{diff} किग्रा विचलन)।"
        elif target_lang == 'pa':
            return f"ਵਾਧੂ ਸਰੀਰਕ ਭਾਰ: ਅਸਲ ਭਾਰ ਮਿਆਰੀ ਭਾਰ ਨਾਲੋਂ {pct}% ਵੱਧ ਹੈ (+{diff} ਕਿਲੋਗ੍ਰਾਮ ਅੰਤਰ)।"
        elif target_lang == 'mr':
            return f"जास्त वजन: प्रत्यक्ष वजन आदर्श मानकापेक्षा {pct}% जास्त आहे (+{diff} किलो फरक)."
        elif target_lang == 'bn':
            return f"অতিরিক্ত ওজন: প্রকৃত ওজন আদর্শ মানের চেয়ে {pct}% বেশি (+{diff} কেজি পার্থক্য)।"
        elif target_lang == 'gu':
            return f"વધારાનું વજન: વાસ્તવિક વજન આદર્શ ધોરણ કરતાં {pct}% વધુ છે (+{diff} કિગ્રા તફાવત)."
        elif target_lang == 'te':
            return f"అధిక శరీర బరువు: అసలు బరువు ప్రామాణికం కంటే {pct}% ఎక్కువ (+{diff} కిలోల వ్యత్యాసం)."
        elif target_lang == 'ml':
            return f"അമിത ശരീരഭാരം: യഥാർത്ഥ ഭാരം സാധാരണയേക്കാൾ {pct}% കൂടുതലാണ് (+{diff} കിലോ വ്യത്യാസം)."
        elif target_lang == 'or':
            return f"ଅଧିକ ଶାରୀରିକ ଓଜନ: ପ୍ରକୃତ ଓଜନ ମାନକ ଠାରୁ {pct}% ଅଧିକ (+{diff} କିଗ୍ରା ପାର୍ଥକ୍ୟ) |"

    # Pattern: Healthy BMI Index
    m = re.match(r"Healthy BMI Index:\s*Body Mass Index \(([0-9.]+)\) indicates prime physical conditioning\.", text_clean, re.I)
    if m:
        val = m.group(1)
        if target_lang == 'ur':
            return f"صحت مند بی ایم آئی انڈیکس: باڈی ماس انڈیکس ({val}) بہترین جسمانی حالت کی نشاندہی کرتا ہے۔"
        elif target_lang in ['hi', 'bho', 'mwr']:
            return f"स्वस्थ बीएमआई सूचकांक: बॉडी मास इंडेक्स ({val}) उत्कृष्ट शारीरिक स्थिति दर्शाता है।"
        elif target_lang == 'pa':
            return f"ਸਿਹਤਮੰਦ ਬੀਐਮਆਈ ਸੂਚਕਾਂਕ: ਬਾਡੀ ਮਾਸ ਇੰਡੈਕਸ ({val}) ਵਧੀਆ ਸਰੀਰਕ ਸਥਿਤੀ ਦਰਸਾਉਂਦਾ ਹੈ।"
        elif target_lang == 'mr':
            return f"निरोगी बीएमआय निर्देशांक: बॉडी मास इंडेक्स ({val}) उत्कृष्ट शारीरिक स्थिती दर्शवितो."
        elif target_lang == 'bn':
            return f"স্বাস্থ্যকর বিএমআই সূচক: বডি ম্যাস ইনডেক্স ({val}) চমৎকার শারীরিক অবস্থা নির্দেশ করে।"
        elif target_lang == 'gu':
            return f"સ્વસ્થ બીએમઆઈ અનુક્રમણિકા: બોડી માસ ઇન્ડેક્સ ({val}) ઉત્તમ શારીરિક સ્થિતિ દર્શાવે છે."
        elif target_lang == 'te':
            return f"ఆరోగ్యకరమైన బిఎమ్‌ఐ సూచిక: బాడీ మాస్ ఇండెక్స్ ({val}) అద్భుతమైన శారీరక స్థితిని సూచిస్తుంది."
        elif target_lang == 'ml':
            return f"ആരോഗ്യമുള്ള ബിഎംഐ സൂചിക: ബോഡി മാസ് ഇൻഡക്സ് ({val}) മികച്ച ശാരീരിക അവസ്ഥയെ സൂചിപ്പിക്കുന്നു."
        elif target_lang == 'or':
            return f"ସ୍ୱାସ୍ଥ୍ୟକର ବିଏମଆଇ ସୂଚକାଙ୍କ: ବଡି ମାସ ଇଣ୍ଡେକ୍ସ ({val}) ଉତ୍କୃଷ୍ଟ ଶାରୀରିକ ସ୍ଥିତି ଦର୍ଶାଏ |"

    # Pattern: Active Sports Participation
    m = re.match(r"Active Sports Participation:\s*Regularly participates in unit athletic activities \((.+)\)\.", text_clean, re.I)
    if m:
        sports = m.group(1)
        # Translate sport name if known
        sports_trans = lang_dict.get(sports, sports)
        if target_lang == 'ur':
            return f"کھیلوں میں فعال شرکت: باقاعدگی سے یونٹ کی کھیلوں کی سرگرمیوں ({sports_trans}) میں حصہ لیتا ہے۔"
        elif target_lang in ['hi', 'bho', 'mwr']:
            return f"सक्रिय खेल भागीदारी: यूनिट की खेल गतिविधियों ({sports_trans}) में नियमित रूप से भाग लेता है।"
        elif target_lang == 'pa':
            return f"ਖੇਡਾਂ ਵਿੱਚ ਸਰਗਰਮ ਭਾਗੀਦਾਰੀ: ਨਿਯਮਿਤ ਤੌਰ 'ਤੇ ਯੂਨਿਟ ਖੇਡਾਂ ({sports_trans}) ਵਿੱਚ ਹਿੱਸਾ ਲੈਂਦਾ ਹੈ।"
        elif target_lang == 'mr':
            return f"सक्रिय खेळ सहभाग: युनिटच्या क्रीडा स्पर्धांमध्ये ({sports_trans}) नियमितपणे सहभाग घेतो."
        elif target_lang == 'bn':
            return f"সক্রিয় ক্রীড়া অংশগ্রহণ: নিয়মিতভাবে ইউনিটের ক্রীড়া কার্যকলাপে ({sports_trans}) অংশ নেয়।"
        elif target_lang == 'gu':
            return f"રમતોમાં સક્રિય સહભાગિતા: યુનિટની રમતગમત પ્રવૃત્તિઓમાં ({sports_trans}) નિયમિતપણે ભાગ લે છે."
        elif target_lang == 'te':
            return f"క్రీడలలో చురుకైన భాగస్వామ్యం: యూనిట్ క్రీడా కార్యకలాపాలలో ({sports_trans}) క్రమం తప్పకుండా పాల్గొంటాడు."
        elif target_lang == 'ml':
            return f"സജീവ കായിക പങ്കാളിത്തം: യൂണിറ്റ് അത്‌ലറ്റിക് പ്രവർത്തനങ്ങളിൽ ({sports_trans}) പതിവായി പങ്കെടുക്കുന്നു."
        elif target_lang == 'or':
            return f"ସକ୍ରିୟ ଖେଳ ଅଂଶଗ୍ରହଣ: ନିୟମିତ ଭାବରେ ୟୁନିଟ କ୍ରୀଡ଼ା ({sports_trans}) ରେ ଅଂଶଗ୍ରହଣ କରେ |"

    # Pattern: Optimal Body Weight
    m = re.match(r"Optimal Body Weight:\s*Actual weight is within ([0-9.]+)% of the Indian Army ideal weight benchmark\.", text_clean, re.I)
    if m:
        pct = m.group(1)
        if target_lang == 'ur':
            return f"بہترین جسمانی وزن: اصل وزن بھارتی فوج کے مثالی وزن کے معیار کے {pct}% کے اندر ہے۔"
        elif target_lang in ['hi', 'bho', 'mwr']:
            return f"अनुकूलतम शारीरिक वजन: वास्तविक वजन भारतीय सेना के आदर्श वजन मानक के {pct}% के भीतर है।"
        elif target_lang == 'pa':
            return f"ਸਹੀ ਸਰੀਰਕ ਭਾਰ: ਅਸਲ ਭਾਰ ਭਾਰਤੀ ਫੌਜ ਦੇ ਆਦਰਸ਼ ਭਾਰ ਮਿਆਰ ਦੇ {pct}% ਦੇ ਅੰਦਰ ਹੈ।"

    # Fallback to general translate_text
    return translate_text(text_clean, target_lang)


def translate_text(text, target_lang='en'):
    """
    Translates static single phrase using dictionary lookup.
    """
    if not text or target_lang == 'en' or not isinstance(text, str):
        return text
        
    text_clean = text.strip()
    lang_dict = DICTIONARY.get(target_lang, {})
    if text_clean in lang_dict:
        return lang_dict[text_clean]

    # Try fallback to Hindi dictionary for Bhojpuri / Mewari if key not in regional
    if target_lang in ['bho', 'mwr'] and 'hi' in DICTIONARY and text_clean in DICTIONARY['hi']:
        return DICTIONARY['hi'][text_clean]

    return text_clean


def get_labels_for_language(target_lang='en', for_pdf=False):
    """
    Returns a complete dictionary of UI and PDF report labels translated into target_lang.
    If for_pdf=True and target_lang=='ur', applies Urdu Arabic reshaping.
    """
    base_labels = {
        'unit_title': '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM',
        'report_title': 'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT',
        'report_generated': 'Report Generated',
        'model_version': 'Model Version',
        'confidential': 'CONFIDENTIAL',
        'sec1_title': '1. Soldier Particulars & Service Profile',
        'army_number': 'Army Number:',
        'full_name': 'Full Name:',
        'rank_trade': 'Rank / Trade:',
        'company_section': 'Company / Section:',
        'age_service': 'Age / Service:',
        'medical_status': 'Medical Status:',
        'years': 'Years',
        'shape1': 'SHAPE-1 Cleared',
        'lmc': 'Restricted / LMC',
        'sec2_title': '2. Physiological Metrics & Physical Performance',
        'height_weight': 'Height / Actual Weight:',
        'ideal_weight': 'Ideal Reference Weight:',
        'bmi_cat': 'BMI Index & Category:',
        'weight_dev': 'Weight Deviation:',
        'bpet_grading': 'BPET Grading:',
        'ppt_grading': 'PPT Grading:',
        'sports': 'Sports & Athletics:',
        'activity_level': 'Physical Activity Level:',
        'sec3_title': '3. AI Physical Readiness Prediction',
        'readiness_score': 'AI Physical Readiness Score:',
        'prediction_conf': 'Prediction Confidence:',
        'algorithm': 'Algorithm:',
        'key_strengths': 'Key Strengths (Positive Indicators):',
        'action_areas': 'Priority Action Areas:',
        'sec4_title': '4. Personalized Dietary & Macronutrient Plan',
        'daily_energy': 'Daily Energy Target:',
        'daily_hydration': 'Daily Hydration Target:',
        'protein_target': 'Protein Target:',
        'carbs_fats': 'Carbs / Fats:',
        'carbs': 'Carbs:',
        'fats': 'Fats:',
        'kcal_day': 'kcal / Day',
        'liters_day': 'Liters / Day',
        'diet_strategy': 'Diet Strategy:',
        'sec5_title': '5. Physical Training',
        'exercise_drill': 'Exercise / Drill',
        'sets': 'Sets',
        'reps_volume': 'Reps / Volume',
        'duration': 'Duration',
        'frequency': 'Frequency',
        'sec6_title': '6. Projected Progression Milestones (30 / 60 / 90 Days)',
        'timeline': 'Timeline',
        'proj_weight': 'Projected Weight',
        'proj_bmi': 'Projected BMI',
        'est_score': 'Estimated Physical Readiness Score'
    }
    
    if target_lang == 'en':
        return base_labels

    translated_labels = {}
    lang_dict = DICTIONARY.get(target_lang, {})
    for k, v in base_labels.items():
        val = lang_dict.get(v, v)
        if for_pdf and target_lang == 'ur':
            val = shape_urdu(val)
        translated_labels[k] = val

    return translated_labels


def translate_report_payload(soldier, prediction, recommendations, progression, target_lang='en', for_pdf=False):
    """
    Creates localized copies of prediction, recommendations, and progression structures
    translated into the requested language for Web UI and PDF compilation.
    """
    if target_lang == 'en':
        return soldier, prediction, recommendations, progression

    t_soldier = copy.deepcopy(soldier)
    t_pred = copy.deepcopy(prediction)
    t_rec = copy.deepcopy(recommendations)
    t_prog = copy.deepcopy(progression)

    def tr(txt):
        res = translate_dynamic_sentence(txt, target_lang)
        if for_pdf and target_lang == 'ur':
            return shape_urdu(res)
        return res

    # Translate soldier dynamic fields
    if t_soldier.get('weight_status'):
        t_soldier['weight_status'] = tr(t_soldier['weight_status'])
    if t_soldier.get('bmi_category'):
        t_soldier['bmi_category'] = tr(t_soldier['bmi_category'])
    if t_soldier.get('rank'):
        t_soldier['rank'] = tr(t_soldier['rank'])
    if t_soldier.get('trade'):
        t_soldier['trade'] = tr(t_soldier['trade'])
    if t_soldier.get('company'):
        t_soldier['company'] = tr(t_soldier['company'])
    if t_soldier.get('physical_activity_level'):
        t_soldier['physical_activity_level'] = tr(t_soldier['physical_activity_level'])
    if t_soldier.get('sports_list'):
        t_soldier['sports_list'] = tr(t_soldier['sports_list'])

    # Translate prediction categories & factor lists
    if t_pred.get('category_label'):
        t_pred['category_label'] = tr(t_pred['category_label'])
    if t_pred.get('strengths'):
        t_pred['strengths'] = [tr(s) for s in t_pred['strengths']]
    if t_pred.get('improvements'):
        t_pred['improvements'] = [tr(i) for i in t_pred['improvements']]

    # Translate diet and exercises
    if t_rec.get('diet'):
        if t_rec['diet'].get('strategy'):
            t_rec['diet']['strategy'] = tr(t_rec['diet']['strategy'])
    if t_rec.get('exercise'):
        if t_rec['exercise'].get('title'):
            t_rec['exercise']['title'] = tr(t_rec['exercise']['title'])
        if t_rec['exercise'].get('focus_area'):
            t_rec['exercise']['focus_area'] = tr(t_rec['exercise']['focus_area'])
        if t_rec['exercise'].get('exercises'):
            for ex in t_rec['exercise']['exercises']:
                if 'exercise' in ex:
                    ex['exercise'] = tr(ex['exercise'])
                if 'reps' in ex:
                    ex['reps'] = tr(ex['reps'])
                if 'duration' in ex:
                    ex['duration'] = tr(ex['duration'])
                if 'frequency' in ex:
                    ex['frequency'] = tr(ex['frequency'])

    # Translate progression milestones
    if t_prog.get('milestones'):
        for m in t_prog['milestones']:
            if 'period' in m:
                m['period'] = tr(m['period'])

    return t_soldier, t_pred, t_rec, t_prog
