"""
Master Translation Layer for UMS Fitness Trend.
Orchestrates IndicTrans2 with offline high-speed military dictionary fallback.
Preserves internal database keys, IDs, scores, and numeric values without alteration.
"""

import re
import copy
import logging
from .language_config import is_supported_language, is_rtl, get_language_name
from .indictrans2_translator import IndicTrans2Translator

logger = logging.getLogger("fitness_trend.translation.translator")

# Global translator instance and memory cache
_INDICTRANS_INSTANCE = None
_TRANSLATION_CACHE = {}


def get_indictrans():
    global _INDICTRANS_INSTANCE
    if _INDICTRANS_INSTANCE is None:
        _INDICTRANS_INSTANCE = IndicTrans2Translator()
    return _INDICTRANS_INSTANCE


# Curated military terminology dictionaries for all 13 languages
VOCABULARY = {
    'hi': {

        'Personal Fitness Report': 'व्यक्तिगत फिटनेस रिपोर्ट',
        'Personnal Fitness Report': 'व्यक्तिगत फिटनेस रिपोर्ट',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'व्यक्तिगत फिटनेस रिपोर्ट',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 कोर / 15 सीईएसआर — यूनिट प्रबंधन प्रणाली',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': '15 कोर इंजीनियरिंग सिग्नल रेजिमेंट',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'एआई/एमएल व्यक्तिगत फिटनेस भविष्यवाणी एवं व्यक्तिगत रिपोर्ट',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'एआई/एमएल व्यक्तिगत फिटनेस भविष्यवाणी एवं तत्परता रिपोर्ट',
        'UNIT MANAGEMENT SYSTEM • OFFICIAL MILITARY RECORD • CONFIDENTIAL': 'यूनिट प्रबंधन प्रणाली • आधिकारिक सैन्य रिकॉर्ड • गोपनीय',
        'Official Individual Fitness Report Preview': 'आधिकारिक व्यक्तिगत फिटनेस रिपोर्ट पूर्वावलोकन',
        'Download PDF Document': 'पीडीएफ दस्तावेज़ डाउनलोड करें',
        'Export PDF': 'निर्यात पीडीएफ',
        'Individual Fitness Report': 'व्यक्तिगत फिटनेस रिपोर्ट',
        'Report Generated': 'रिपोर्ट दिनांक',
        'Model Version': 'मॉडल संस्करण',
        'CONFIDENTIAL': 'गोपनीय',
        '1. Soldier Particulars & Service Profile': '1. सैनिक विवरण एवं सेवा प्रोफ़ाइल',
        'Personnel Details': 'सैनिक विवरण',
        'Name': 'नाम',
        'Name:': 'नाम:',
        'Full Name': 'पूरा नाम',
        'Army Number': 'आर्मी नंबर',
        'Army Number:': 'आर्मी नंबर:',
        'Full Name:': 'पूरा नाम:',
        'Rank / Trade': 'पद / ट्रेड',
        'Rank / Trade:': 'पद / ट्रेड:',
        'Company / Section': 'कंपनी / सेक्शन',
        'Company / Section:': 'कंपनी / सेक्शन:',
        'Height / Weight': 'कद / वास्तविक वजन',
        'Ideal Wt / Deviation': 'आदर्श मानक वजन / अंतर',
        'BMI & Category': 'बीएमआई सूचकांक व श्रेणी',
        'BPET / PPT Grading': 'बीपीईटी / पीपीटी ग्रेडिंग',
        'Age / Service:': 'आयु / सेवा वर्ष:',
        'Medical Status:': 'चिकित्सा स्थिति:',
        'Years': 'वर्ष',
        'SHAPE-1 Cleared': 'शेप-1 पास',
        'Restricted / LMC': 'प्रतिबंधित / एलएमसी',
        'Agniveer': 'अग्निवीर',
        'Havildar': 'हवलदार',
        'HAV': 'हवलदार',
        'Naik': 'नायक',
        'NK': 'नायक',
        'Lance Naik': 'लांस नायक',
        'L NK': 'लांस नायक',
        'Subedar': 'सूबेदार',
        'Naib Subedar': 'नायब सूबेदार',
        'Signalman': 'सिग्नलमैन',
        'GD': 'जीडी',
        'DVR': 'चालक',
        'DMV': 'डीएमवी',
        'TTC': 'टीटीसी',
        'Opr': 'ऑपरेटर',
        '1 Company': '1 कंपनी',
        '2 Company': '2 कंपनी',
        '3 Company': '3 कंपनी',
        'COMN Company': 'संचार कंपनी',
        'HQ company': 'मुख्यालय कंपनी',
        'MW': 'माइक्रोवेव (MW)',
        'MW Section': 'माइक्रोवेव सेक्शन',
        'Line Section': 'लाइन सेक्शन',
        'Radio Section': 'रेडियो सेक्शन',
        'Cipher Section': 'सिफर सेक्शन',
        'N/A': 'एन/ए',
        'Untested': 'अपरिक्षित',
        '2. Physiological Metrics & Physical Performance': '2. शारीरिक माप एवं प्रदर्शन विश्लेषण',
        'Fitness Assessment': 'फिटनेस मूल्यांकन',
        'Current Fitness Level': 'वर्तमान फिटनेस स्तर',
        'Height / Actual Weight:': 'कद / वास्तविक वजन:',
        'Ideal Reference Weight:': 'आदर्श मानक वजन:',
        'BMI Index & Category:': 'बीएमआई सूचकांक व श्रेणी:',
        'Weight Deviation:': 'वजन में अंतर:',
        'BPET Grading:': 'बीपीईटी ग्रेडिंग:',
        'PPT Grading:': 'पीपीटी ग्रेडिंग:',
        'Sports & Athletics:': 'खेलकूद व एथलेटिक्स:',
        'Physical Activity Level:': 'शारीरिक गतिविधि स्तर:',
        'Normal (Ideal)': 'सामान्य (आदर्श)',
        'Normal': 'सामान्य',
        'Overweight': 'अधिक वजन',
        'Underweight': 'कम वजन',
        'EXCELLENT': 'उत्कृष्ट (EXCELLENT)',
        'GOOD': 'उत्तम (GOOD)',
        'SATISFACTORY': 'संतोषजनक (SATISFACTORY)',
        'Moderate': 'मध्यम',
        'Active': 'सक्रिय',
        'Sports': 'खेल',
        'Football': 'फ़ुटबॉल',
        'Basketball': 'बास्केटबॉल',
        'Volleyball': 'वॉलीबॉल',
        'Cross-Country': 'क्रॉस-कंट्री',
        'Athletics': 'एथलेटिक्स',
        '3. AI Physical Readiness Prediction': '3. एआई शारीरिक तैयारी भविष्यवाणी',
        'Fitness Score': 'फिटनेस स्कोर',
        'Fitness Status': 'फिटनेस स्थिति',
        'AI Physical Readiness Score:': 'एआई शारीरिक तैयारी स्कोर:',
        'Prediction Confidence:': 'भविष्यवाणी सटीकता:',
        'Algorithm:': 'एल्गोरिदम:',
        'Key Strengths (Positive Indicators):': 'मुख्य मजबूती (सकारात्मक पहलू):',
        'Priority Action Areas:': 'प्राथमिक सुधार क्षेत्र:',
        'Good Fitness': 'अच्छा फिटनेस (Good Fitness)',
        'Excellent Readiness': 'उत्कृष्ट तैयारी (Excellent Readiness)',
        'Satisfactory / Average': 'संतोषजनक (Average)',
        'Needs Improvement / At-Risk': 'सुधार की आवश्यकता',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "उच्च बीपीईटी प्रदर्शन: शारीरिक सहनशक्ति और बाधा परीक्षण में 'उत्कृष्ट' ग्रेडिंग प्राप्त की।",
        "Solid BPET Performance: Achieved 'Good' standard in military physical endurance.": "ठोस बीपीईटी प्रदर्शन: सैन्य शारीरिक सहनशक्ति में 'उत्तम' मानक प्राप्त किया।",
        "Moderate BPET: Graded 'Satisfactory'; endurance pacing can be improved to reach 'Good/Excellent'.": "मध्यम बीपीईटी: 'संतोषजनक' ग्रेड; सहनशक्ति को 'उत्तम/उत्कृष्ट' तक बढ़ाया जा सकता है।",
        "BPET Deficiency: Low physical grading or restriction recorded during endurance testing.": "बीपीईटी कमी: सहनशक्ति परीक्षण के दौरान निम्न ग्रेडिंग या प्रतिबंध दर्ज।",
        "BPET Untested: No recent formal BPET test recorded in system.": "बीपीईटी अप्रमाणित: सिस्टम में हालिया औपचारिक परीक्षण दर्ज नहीं है।",
        "High PPT Performance: Achieved 'Excellent' in physical proficiency standards.": "उच्च पीपीटी प्रदर्शन: शारीरिक प्रवीणता मानकों में 'उत्कृष्ट' ग्रेड प्राप्त किया।",
        "Solid PPT Performance: Meets high physical proficiency benchmarks.": "ठोस पीपीटी प्रदर्शन: उच्च शारीरिक दक्षता मानकों पर खरा उतरता है।",
        "PPT Potential: Satisfactory performance; calisthenics, chin-ups, and sprint speed can be elevated.": "पीपीटी सुधार क्षमता: संतोषजनक प्रदर्शन; चिन-अप और स्प्रिंट गति में सुधार संभव है।",
        "PPT Remedial Needed: Physical proficiency test requires structured conditioning.": "पीपीटी उपचारात्मक आवश्यकता: शारीरिक प्रवीणता परीक्षण में नियमित अभ्यास आवश्यक है।",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "स्पष्ट चिकित्सा प्रोफ़ाइल: चिकित्सकीय रूप से शेप-1, जिसमें व्यायाम पर कोई प्रतिबंध नहीं है।",
        "No Structured Sports: Currently not registered in regular unit sports competitions.": "नियमित खेल में अनुपस्थिति: वर्तमान में यूनिट की नियमित खेल प्रतियोगिताओं में भाग नहीं ले रहा है।",
        "Demographic Baseline: Within normal military operational age & service profile.": "सैन्य आधारभूत प्रोफ़ाइल: सामान्य सैन्य परिचालन आयु एवं सेवा प्रोफ़ाइल के अंतर्गत।",
        "Maintenance Focus: Sustain current peak endurance, cardiovascular health, and sports routine.": "अनुरक्षण लक्ष्य: वर्तमान उच्चतम सहनशक्ति, हृदय स्वास्थ्य और खेल दिनचर्या को बनाए रखें।",
        '4. Personalized Dietary & Macronutrient Plan': '4. व्यक्तिगत आहार एवं पोषण योजना',
        'Personalized Recommendations': 'व्यक्तिगत अनुशंसाएँ',
        'Diet Recommendations': 'आहार अनुशंसाएँ',
        'Daily Energy Target:': 'दैनिक ऊर्जा लक्ष्य:',
        'Daily Hydration Target:': 'दैनिक जल लक्ष्य:',
        'Protein Target:': 'प्रोटीन लक्ष्य:',
        'Carbs / Fats:': 'कार्बोहाइड्रेट / वसा:',
        'Carbs:': 'कार्बोहाइड्रेट:',
        'Fats:': 'वसा:',
        'COMPLEX CARBS': 'जटिल कार्बोहाइड्रेट',
        'HEALTHY FATS': 'स्वस्थ वसा',
        'DAILY PROTEIN': 'दैनिक प्रोटीन',
        'HYDRATION': 'दैनिक जल लक्ष्य',
        'AI Physical Readiness Prediction': 'एआई शारीरिक तैयारी भविष्यवाणी',
        'Key Positive Factors:': 'मुख्य सकारात्मक पहलू:',
        'Priority Action Areas:': 'प्राथमिक सुधार क्षेत्र:',
        'Diet Strategy:': 'आहार रणनीति:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "मध्यम कैलोरी घाटा (लगभग 450 किलो कैलोरी कम) ताकि सहनशक्ति बनाए रखते हुए वजन घट सके।",
        "Nutrient-Dense Calorie Surplus (+350 kcal) to build lean functional muscle mass.": "पोषक तत्वों से भरपूर कैलोरी वृद्धि (+350 किलो कैलोरी) लीन मांसपेशियों के निर्माण हेतु।",
        "Slight Surplus (+200 kcal) paired with high protein for maximum strength & power development.": "हल्की कैलोरी वृद्धि (+200 किलो कैलोरी) उच्च प्रोटीन के साथ अधिकतम शक्ति व ऊर्जा हेतु।",
        "Isocaloric High-Energy Balance with optimal complex carbohydrates for sustained endurance.": "संतुलित ऊर्जा स्तर निरंतर शारीरिक सहनशक्ति बनाए रखने हेतु।",
        "Maintenance Calorie Intake optimized for physical conditioning and SHAPE-1 preservation.": "रखरखाव कैलोरी लक्ष्य शारीरिक फिटनेस और शेप-1 बनाए रखने हेतु।",
        '5. Physical Training': '5. शारीरिक प्रशिक्षण',
        'Exercise Recommendations': 'व्यायाम अनुशंसाएँ',
        'Exercise / Drill': 'व्यायाम / ड्रिल',
        'Exercise Name': 'व्यायाम का नाम',
        'Sets': 'सेट्स',
        'Reps / Volume': 'रेप्स / मात्रा',
        'Duration': 'अवधि',
        'Frequency': 'आवृत्ति',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'तीव्र गति एरोबिक दौड़ / क्रॉस-कंट्री (4 - 6 किमी)',
        'Bodyweight Full-Body Circuit (Jumping jacks, mountain climbers, bodyweight squats, lunges)': 'बॉडीवेट सर्किट (जंपिंग जैक, माउंटेन क्लाइंबर, स्क्वैट्स, लंजेस)',
        'Stair Climbing & Hill Sprints': 'सीढ़ी चढ़ाई और पहाड़ी स्प्रिंट्स',
        'Core Russian Twists & Leg Raises': 'कोर रशियन ट्विस्ट्स और लेग राइज़',
        '5km Interval Progression Run (300m sprint / 200m jog)': '5 किमी अंतराल प्रगति दौड़ (300 मी स्प्रिंट / 200 मी जॉग)',
        'Horizontal Rope Traverse & Hanging Pulls': 'क्षैतिज रस्सी पार करना और पुल-अप्स',
        'Burpees to Sprint Accelerations (20m shuttle)': 'बर्पीज़ के साथ स्प्रिंट (20 मी शटल)',
        'Plank Hold & Side Bridge Circuit': 'प्लैंक होल्ड और साइड ब्रिज सर्किट',
        'Standard Military Chin-Ups / Pull-Ups': 'मानक सैन्य चिन-अप्स / पुल-अप्स',
        'Military Push-Ups (Chest to Ground)': 'सैन्य पुश-अप्स (जमीन तक छाती)',
        '2.4km Speed Time Trial (PPT Baseline)': '2.4 किमी गति परीक्षण (पीपीटी आधार)',
        'Bent-Knee Sit-Ups (Strict 2-minute test pace)': 'मुड़े हुए घुटने के सिट-अप्स (2 मिनट गति)',
        '5km Base Endurance Run': '5 किमी बुनियादी सहनशक्ति दौड़',
        'Upper Body Calisthenics (Pull-ups, Dips, Push-ups)': 'ऊपरी शरीर कैलिस्थेनिक्स (पुल-अप्स, डिप्स, पुश-अप्स)',
        'Unit Team Sports (Volleyball / Football / Basketball)': 'यूनिट टीम खेल (वॉलीबॉल / फुटबॉल / बास्केटबॉल)',
        'Dynamic Flexibility & Mobility Cool-Down': 'गतिशीलता व स्ट्रेचिंग कूल-डाउन',
        'Continuous steady state': 'निरंतर स्थिर गति',
        '45 sec work / 15 sec rest per station': '45 सेकंड व्यायाम / 15 सेकंड विश्राम',
        '40 meters incline / walk down': '40 मीटर चढ़ाई / नीचे पैदल',
        '20 reps each': '20 रेप्स प्रत्येक',
        '500m per cycle': '500 मी प्रति चक्र',
        '15-20 meters / 8 pulls': '15-20 मीटर / 8 पुल-अप्स',
        '10 burpees + 20m sprint': '10 बर्पीज़ + 20 मी स्प्रिंट',
        '60 sec front + 45 sec sides': '60 सेकंड सामने + 45 सेकंड साइड',
        '8 - 12 reps (or max to failure)': '8 - 12 रेप्स',
        '25 - 35 reps': '25 - 35 रेप्स',
        '2.4 km continuous': '2.4 किमी निरंतर',
        '40 - 50 reps in 2 mins': '2 मिनट में 40 - 50 रेप्स',
        'Continuous 5 km': 'निरंतर 5 किमी',
        '10 pull-ups / 15 dips / 30 push-ups': '10 पुल-अप्स / 15 डिप्स / 30 पुश-अप्स',
        'Match play': 'मैच खेलना',
        'Full-body stretches': 'पूर्ण शरीर स्ट्रेच',
        '35 - 40 mins': '35 - 40 मिनट',
        '20 mins': '20 मिनट',
        '15 mins': '15 मिनट',
        '10 mins': '10 मिनट',
        '35 mins': '35 मिनट',
        '12 mins': '12 मिनट',
        '12 - 15 mins': '12 - 15 मिनट',
        '25 - 30 mins': '25 - 30 मिनट',
        '45 - 60 mins': '45 - 60 मिनट',
        '4 days/week': '4 दिन / सप्ताह',
        '3 days/week': '3 दिन / सप्ताह',
        '2 days/week': '2 दिन / सप्ताह',
        'Daily after PT': 'पीटी के बाद प्रतिदिन',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. अनुमानित प्रगति मील के पत्थर (30 / 60 / 90 दिन)',
        'Progression Timeline': 'प्रगति समयरेखा',
        'Timeline': 'समयरेखा',
        'Projected Weight': 'अनुमानित वजन',
        'Projected BMI': 'अनुमानित बीएमआई',
        'Estimated Physical Readiness Score': 'अनुमानित फिटनेस स्कोर',
        'Current Baseline': 'वर्तमान आधार रेखा (Baseline)',
        '30 Days Projected': '30 दिन का अनुमान',
        '60 Days Projected': '60 दिन का अनुमान',
        '90 Days Projected': '90 दिन का अनुमान',
        'UNIT MANAGEMENT SYSTEM': 'यूनिट प्रबंधन प्रणाली',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'यूनिट प्रबंधन प्रणाली',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'यूनिट प्रबंधन प्रणाली',
        'UMS 15 CESR': 'यूनिट प्रबंधन प्रणाली',
        '8. Personalized Nutrition Recommendations': '8. व्यक्तिगत पोषण अनुशंसाएँ',
        'Personalized Nutrition Recommendations': 'व्यक्तिगत पोषण अनुशंसाएँ',
        "✔ DO'S (Recommended Protocol):": "✔ क्या करें (अनुशंसित प्रोटोकॉल):",
        "✔ DO'S (Recommended Protocol)": "✔ क्या करें (अनुशंसित प्रोटोकॉल)",
        "DO'S (Recommended Protocol):": "✔ क्या करें (अनुशंसित प्रोटोकॉल):",
        "DO'S (Recommended Protocol)": "✔ क्या करें (अनुशंसित प्रोटोकॉल)",
        "DO'S": "क्या करें",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ क्या न करें (परहेज करने योग्य चीजें व आदतें):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ क्या न करें (परहेज करने योग्य चीजें व आदतें):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ क्या न करें (परहेज करने योग्य चीजें व आदतें)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ क्या न करें (परहेज करने योग्य चीजें व आदतें)",
        "DON'TS (Items & Habits to Avoid):": "✖ क्या न करें (परहेज करने योग्य चीजें व आदतें):",
        "DONTS (Items & Habits to Avoid):": "✖ क्या न करें (परहेज करने योग्य चीजें व आदतें):",
        "DON'TS": "क्या न करें",
        "DONTS": "क्या न करें",
        'Operational Nutrition & Hydration Discipline:': 'ऑपरेशनल पोषण एवं जलयोजन अनुशासन:',
        'Operational Nutrition & Hydration Discipline': 'ऑपरेशनल पोषण एवं जलयोजन अनुशासन',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'मांसपेशियों के प्रोटीन संश्लेषण के लिए लीन चिकन, उबले अंडे और पनीर',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'लगातार अमीनो एसिड के लिए साबुत दालें और अंकुरित अनाज',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'ग्लाइकोजन की पुनःपूर्ति के लिए साबुत अनाज (ओट्स, ब्राउन राइस, गेहूं की रोटी)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'इलेक्ट्रोलाइट्स और सूक्ष्म पोषक तत्वों के लिए मौसमी ताजे फल और हरी पत्तेदार सब्जियां',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'प्रतिदिन कम से कम 3.0 से 3.5 लीटर साफ पानी का नियमित सेवन',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'मेस के तले हुए स्नैक्स, पकौड़े और कैंटीन के प्रोसेस्ड खाद्य पदार्थ',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'रिफाइंड चीनी, अत्यधिक मीठी चाय/कॉफी और कोल्ड ड्रिंक्स (कार्बोनेटेड पेय)',
        'Excessive table salt, pickles, and high-sodium processed rations': 'अत्यधिक नमक, अचार और अधिक सोडियम वाले प्रोसेस्ड राशन',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'भोजन का अनियमित समय या सुबह पीटी से पहले नाश्ता छोड़ना',
        'Heavy meals consumed less than 2 hours before lights out': 'सोने (लाइट्स आउट) से 2 घंटे से कम समय पहले भारी भोजन करना',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'भोजन का नियमित समय बनाए रखें; सोने (लाइट्स आउट) से कम से कम 2 घंटे पहले रात का खाना समाप्त करें।',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'मांसपेशियों की त्वरित रिकवरी के लिए लीन प्रोटीन (दाल, अंकुरित अनाज, पनीर, अंडे, चिकन) को प्राथमिकता दें।',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'यूनिट कैंटीन के तले हुए स्नैक्स, मीठे पेय और प्रोसेस्ड कन्फेक्शनरी से बचें।',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'प्रतिदिन कम से कम 3.5 से 4.0 लीटर पानी का सेवन सुनिश्चित करें, विशेष रूप से बाहरी पीटी सत्रों के दौरान।',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'महत्वपूर्ण सूक्ष्म पोषक तत्वों और इलेक्ट्रोलाइट्स के लिए हरी पत्तेदार सब्जियां और मौसमी खट्टे फल शामिल करें।',
        'Meal Timing Discipline: Ensure dinner is finished at least 2 hours before sleep; consume recovery protein within 45 minutes after intensive PT.': 'भोजन के समय का अनुशासन: सोने से कम से कम 2 घंटे पहले रात का खाना समाप्त करें; गहन पीटी के 45 मिनट के भीतर रिकवरी प्रोटीन लें।',
        'Operational Hydration: Consume 500 ml of clean water 30 minutes prior to outdoor drills; maintain continuous fluid replenishment in hot terrain.': 'ऑपरेशनल जलयोजन: बाहरी अभ्यासों से 30 मिनट पहले 500 मिलीलीटर साफ पानी पिएं; गर्म इलाकों में लगातार पानी की पूर्ति बनाए रखें।',
        'Mess Selection Strategy: Prioritize roasted, boiled, or grilled mess items over deep-fried curries; incorporate fresh salads and curd daily.': 'मेस चयन रणनीति: तली हुई करी की तुलना में भुनी, उबली या ग्रिल्ड मेस वस्तुओं को प्राथमिकता दें; रोजाना ताजा सलाद और दही शामिल करें।',
    },
    'ur': {

        'Personal Fitness Report': 'ذاتی فٹنس رپورٹ',
        'Personnal Fitness Report': 'ذاتی فٹنس رپورٹ',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'ذاتی فٹنس رپورٹ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 کور / 15 سی ای ایس آر — یونٹ مینجمنٹ سسٹم',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'اے آئی/ایم ایل انفرادی فٹنس پیشین گوئی اور ذاتی رپورٹ',
        'Individual Fitness Report': 'انفرادی فٹنس رپورٹ',
        'Report Generated': 'رپورٹ تاریخ',
        'Model Version': 'ماڈل ورژن',
        'CONFIDENTIAL': 'خفیہ',
        '1. Soldier Particulars & Service Profile': '1. فوجی کی تفصیلات اور سروس پروفائل',
        'Personnel Details': 'فوجی تفصیلات',
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
        '2. Physiological Metrics & Physical Performance': '2. جسمانی پیمائش اور کارکردگی کا تجزیہ',
        'Fitness Assessment': 'فٹنس جائزہ',
        'Current Fitness Level': 'موجودہ فٹنس لیول',
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
        'Football': 'فٹ بال',
        'Basketball': 'باسکٹ بال',
        'Volleyball': 'والی بال',
        'Cross-Country': 'کراس کنٹری',
        'Athletics': 'ایتھلیٹکس',
        '3. AI Physical Readiness Prediction': '3. اے آئی جسمانی تیاری کی پیشین گوئی',
        'Fitness Score': 'فٹنس اسکور',
        'Fitness Status': 'فٹنس کیفیت',
        'AI Physical Readiness Score:': 'اے آئی جسمانی تیاری کا اسکور:',
        'Prediction Confidence:': 'پیشین گوئی کا اعتماد:',
        'Algorithm:': 'الگورتھم:',
        'Key Strengths (Positive Indicators):': 'اہم خوبیاں (مثبت اشارے):',
        'Priority Action Areas:': 'ترجیحی بہتری کے شعبے:',
        'Good Fitness': 'اچھی فٹنس (Good Fitness)',
        'Excellent Readiness': 'بہترین تیاری (Excellent Readiness)',
        'Satisfactory / Average': 'تسلی بخش (Average)',
        'Needs Improvement / At-Risk': 'بہتری کی ضرورت',
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
        '4. Personalized Dietary & Macronutrient Plan': '4. ذاتی غذا اور غذائی اجزاء کا منصوبہ',
        'Personalized Recommendations': 'ذاتی تجاویز',
        'Diet Recommendations': 'غذائی تجاویز',
        'Daily Energy Target:': 'روزانہ توانائی کا ہدف:',
        'Daily Hydration Target:': 'روزانہ پانی کا ہدف:',
        'Protein Target:': 'پروٹین کا ہدف:',
        'Carbs / Fats:': 'کاربوہائیڈریٹ / چکنائی:',
        'Carbs:': 'کاربوہائیڈریٹ:',
        'Fats:': 'چکنائی:',
        'Diet Strategy:': 'غذائی حکمت عملی:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "معتدل کیلوری کمی (تقریباً 450 کلو کیلوری کم) تاکہ فوجی صلاحیت کو برقرار رکھتے ہوئے چربی کم ہو سکے۔",
        "Nutrient-Dense Calorie Surplus (+350 kcal) to build lean functional muscle mass.": "غذائیت سے بھرپور کیلوری کا اضافہ (+350 کلو کیلوری) تاکہ عضلات کو مضبوط کیا جا سکے۔",
        "Slight Surplus (+200 kcal) paired with high protein for maximum strength & power development.": "ہلکا اضافہ (+200 کلو کیلوری) زیادہ پروٹین کے ساتھ تاکہ طاقت اور توانائی کو زیادہ کیا جا سکے۔",
        "Isocaloric High-Energy Balance with optimal complex carbohydrates for sustained endurance.": "اعلیٰ توانائی کا متوازن تناسب تاکہ مسلسل جسمانی برداشت قائم رہے۔",
        "Maintenance Calorie Intake optimized for physical conditioning and SHAPE-1 preservation.": "برقراری کیلوری کا ہدف تاکہ جسمانی فٹنس اور شیپ-1 کو برقرار رکھا جا سکے۔",
        '5. Physical Training': '5. جسمانی تربیت',
        'Exercise Recommendations': 'ورزش کی تجاویز',
        'Exercise / Drill': 'ورزش / ڈرل',
        'Exercise Name': 'ورزش کا نام',
        'Sets': 'سیٹس',
        'Reps / Volume': 'ریپس / مقدار',
        'Duration': 'دورانیہ',
        'Frequency': 'تعدد',
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
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. متوقع ترقی کے سنگ میل (30 / 60 / 90 دن)',
        'Progression Timeline': 'ترقیاتی ٹائم لائن',
        'Timeline': 'ٹائم لائن',
        'Projected Weight': 'متوقع وزن',
        'Projected BMI': 'متوقع بی ایم آئی',
        'Estimated Physical Readiness Score': 'متوقع جسمانی تیاری کا اسکور',
        'Current Baseline': 'موجودہ بنیادی سطح (Baseline)',
        '30 Days Projected': '30 دن کا تخمینہ',
        '60 Days Projected': '60 دن کا تخمینہ',
        '90 Days Projected': '90 دن کا تخمینہ',
        'UNIT MANAGEMENT SYSTEM': 'یونٹ مینجمنٹ سسٹم',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'یونٹ مینجمنٹ سسٹم',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'یونٹ مینجمنٹ سسٹم',
        'UMS 15 CESR': 'یونٹ مینجمنٹ سسٹم',
        '8. Personalized Nutrition Recommendations': '8. ذاتی غذائی تجاویز',
        'Personalized Nutrition Recommendations': 'ذاتی غذائی تجاویز',
        "✔ DO'S (Recommended Protocol):": "✔ کیا کریں (تجویز کردہ پروٹوکول):",
        "✔ DO'S (Recommended Protocol)": "✔ کیا کریں (تجویز کردہ پروٹوکول)",
        "DO'S (Recommended Protocol):": "✔ کیا کریں (تجویز کردہ پروٹوکول):",
        "DO'S (Recommended Protocol)": "✔ کیا کریں (تجویز کردہ پروٹوکول)",
        "DO'S": "کیا کریں",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ کیا نہ کریں (پرہیز کی جانے والی عادات اور اشیاء):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ کیا نہ کریں (پرہیز کی جانے والی عادات اور اشیاء):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ کیا نہ کریں (پرہیز کی جانے والی عادات اور اشیاء)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ کیا نہ کریں (پرہیز کی جانے والی عادات اور اشیاء)",
        "DON'TS (Items & Habits to Avoid):": "✖ کیا نہ کریں (پرہیز کی جانے والی عادات اور اشیاء):",
        "DONTS (Items & Habits to Avoid):": "✖ کیا نہ کریں (پرہیز کی جانے والی عادات اور اشیاء):",
        "DON'TS": "کیا نہ کریں",
        "DONTS": "کیا نہ کریں",
        'Operational Nutrition & Hydration Discipline:': 'آپریشنل غذائیت اور ہائیڈریشن کا نظم و ضبط:',
        'Operational Nutrition & Hydration Discipline': 'آپریشنل غذائیت اور ہائیڈریشن کا نظم و ضبط',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'دبلے گوشت، ابلے انڈے اور پنیر پٹھوں کی پروٹین کی تیاری کے لیے',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'مسلسل امینو ایسڈز کے لیے ثابت دالیں اور انکرت شدہ دالیں',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'گلائکوجن کی بحالی کے لیے اناج (اوٹس، براؤن رائس، گندم کی روٹی)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'الیکٹرولائٹس اور مائیکرو نیوٹرینٹس کے لیے موسمی تازہ پھل اور سبزیاں',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'روزانہ کم از کم 3.0 سے 3.5 لیٹر صاف پانی کے ساتھ مسلسل ہائیڈریشن',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'میس کے تلے ہوئے اسنیکس، پکوڑے اور کینٹین کی تلی ہوئی یا پروسیس شدہ اشیاء',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'صاف شدہ چینی، میٹھی چائے/کافی اور کاربونیٹیڈ مشروبات',
        'Excessive table salt, pickles, and high-sodium processed rations': 'اضافی نمک، اچار اور زیادہ سوڈیم والے پروسیس شدہ راشن',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'کھانے کے غیر منظم اوقات یا صبح کی پی ٹی سے پہلے ناشتہ چھوڑنا',
        'Heavy meals consumed less than 2 hours before lights out': 'سوتے وقت (لائٹس آؤٹ) سے 2 گھنٹے سے کم وقت پہلے بھاری کھانا کھانا',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'کھانے کے اوقات میں تسلسل برقرار رکھیں؛ سونے سے کم از کم 2 گھنٹے پہلے رات کا کھانا ختم کریں۔',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'پٹھوں کی تیزی سے بحالی کے لیے دبلے پروٹین (دال، انکرت، پنیر، انڈے، چکن) کو ترجیح دیں۔',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'یونٹ کینٹین سے تلے ہوئے اسنیکس، میٹھے مشروبات اور پروسیس شدہ مٹھائیوں سے پرہیز کریں۔',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'روزانہ کم از کم 3.5 سے 4.0 لیٹر پانی کا استعمال یقینی بنائیں، خاص طور پر بیرونی پی ٹی سیشنز کے دوران۔',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'اہم مائیکرو نیوٹرینٹس اور الیکٹرولائٹس کے لیے سبز پتوں والی سبزیاں اور موسمی ترش پھل شامل کریں۔',
        'Meal Timing Discipline: Ensure dinner is finished at least 2 hours before sleep; consume recovery protein within 45 minutes after intensive PT.': 'کھانے کے اوقات کا نظم و ضبط: سونے سے کم از کم 2 گھنٹے پہلے رات کا کھانا ختم کریں؛ سخت پی ٹی کے 45 منٹ کے اندر ریکوری پروٹین لیں۔',
        'Operational Hydration: Consume 500 ml of clean water 30 minutes prior to outdoor drills; maintain continuous fluid replenishment in hot terrain.': 'آپریشنل ہائیڈریشن: آؤٹ ڈور مشقوں سے 30 منٹ پہلے 500 ملی لیٹر صاف پانی پئیں؛ گرم موسم میں مسلسل پانی کی کمی پوری کریں۔',
        'Mess Selection Strategy: Prioritize roasted, boiled, or grilled mess items over deep-fried curries; incorporate fresh salads and curd daily.': 'میس سلیکشن حکمت عملی: تلی ہوئی سالن کے بجائے بھنی ہوئی، ابلی ہوئی اشیاء کو ترجیح دیں؛ روزانہ تازہ سلاد اور دہی شامل کریں۔',
    },
    'bn': {

        'Personal Fitness Report': 'ব্যক্তিগত ফিটনেস রিপোর্ট',
        'Personnal Fitness Report': 'ব্যক্তিগত ফিটনেস রিপোর্ট',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'ব্যক্তিগত ফিটনেস রিপোর্ট',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '১৫ কোর / ১৫ সিইএসআর — ইউনিট ম্যানেজমেন্ট সিস্টেম',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'এআই/এমএল ব্যক্তিগত ফিটনেস পূর্বাভাস ও প্রতিবেদন',
        'Individual Fitness Report': 'ব্যক্তিগত ফিটনেস রিপোর্ট',
        'Report Generated': 'প্রতিবেদন তারিখ',
        'Model Version': 'মডেল সংস্করণ',
        'CONFIDENTIAL': 'গোপনীয়',
        '1. Soldier Particulars & Service Profile': '১. সৈনিকের বিবরণ ও চাকরির প্রোফাইল',
        'Personnel Details': 'সৈনিকের বিবরণ',
        'Army Number:': 'আর্মি নম্বর:',
        'Full Name:': 'পূর্ণ নাম:',
        'Rank / Trade:': 'পদবী / ট্রেড:',
        'Company / Section:': 'কোম্পানি / বিভাগ:',
        'Age / Service:': 'বয়স / চাকরি কাল:',
        'Medical Status:': 'চিকিৎসা স্থিতি:',
        'Years': 'বছর',
        'SHAPE-1 Cleared': 'শেপ-১ পাস',
        'Restricted / LMC': 'সীমাবদ্ধ / এলএমসি',
        '2. Physiological Metrics & Physical Performance': '২. শারীরিক পরিমাপ ও কর্মক্ষমতা বিশ্লেষণ',
        'Fitness Assessment': 'ফিটনেস মূল্যায়ন',
        'Current Fitness Level': 'বর্তমান ফিটনেস স্তর',
        'Height / Actual Weight:': 'উচ্চতা / প্রকৃত ওজন:',
        'Ideal Reference Weight:': 'আদর্শ মান ওজন:',
        'BMI Index & Category:': 'বিএমআই সূচক ও শ্রেণি:',
        'Weight Deviation:': 'ওজনের পার্থক্য:',
        'BPET Grading:': 'বিপিইটি গ্রেডিং:',
        'PPT Grading:': 'পিপিটি গ্রেডিং:',
        'Sports & Athletics:': 'খেলাধুলা ও অ্যাথলেটিক্স:',
        'Physical Activity Level:': 'শারীরিক কার্যকলাপ স্তর:',
        'Normal (Ideal)': 'স্বাভাবিক (আদর্শ)',
        'Normal': 'স্বাভাবিক',
        'Overweight': 'অতিরিক্ত ওজন',
        'Underweight': 'কম ওজন',
        'EXCELLENT': 'চমৎকার (EXCELLENT)',
        'GOOD': 'উত্তম (GOOD)',
        'SATISFACTORY': 'সন্তোষজনক (SATISFACTORY)',
        'Moderate': 'মাঝারি',
        'Active': 'সক্রিয়',
        'Sports': 'খেলাধুলা',
        'Football': 'ফুটবল',
        '3. AI Physical Readiness Prediction': '৩. এআই শারীরিক প্রস্তুতি পূর্বাভাস',
        'Fitness Score': 'ফিটনেস স্কোর',
        'Fitness Status': 'ফিটনেস অবস্থা',
        'AI Physical Readiness Score:': 'এআই শারীরিক প্রস্তুতি স্কোর:',
        'Prediction Confidence:': 'পূর্বাভাস নির্ভুলতা:',
        'Algorithm:': 'অ্যালগরিদম:',
        'Key Strengths (Positive Indicators):': 'প্রধান শক্তি (ইতিবাচক সূচক):',
        'Priority Action Areas:': 'অগ্রাধিকার উন্নয়ন ক্ষেত্র:',
        'Good Fitness': 'ভালো ফিটনেস (Good Fitness)',
        'Excellent Readiness': 'চমৎকার প্রস্তুতি (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "উচ্চ বিপিইটি কর্মক্ষমতা: শারীরিক সহনশীলতা ও বাধা পরীক্ষায় 'চমৎকার' গ্রেডিং অর্জন।",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "পরিচ্ছন্ন মেডিকেল প্রোফাইল: চিকিৎসাগতভাবে শেপ-১, কোনো ব্যায়াম বিধিনিষেধ নেই।",
        '4. Personalized Dietary & Macronutrient Plan': '৪. ব্যক্তিগত খাদ্য ও পুষ্টি পরিকল্পনা',
        'Personalized Recommendations': 'ব্যক্তিগত সুপারিশমালা',
        'Diet Recommendations': 'খাদ্য সুপারিশমালা',
        'Daily Energy Target:': 'দৈনিক শক্তির লক্ষ্য:',
        'Daily Hydration Target:': 'দৈনিক জলের লক্ষ্য:',
        'Protein Target:': 'প্রোটিনের লক্ষ্য:',
        'Carbs / Fats:': 'কার্বোহাইড্রেট / চর্বি:',
        'Carbs:': 'কার্বোহাইড্রেট:',
        'Fats:': 'চর্বি:',
        'Diet Strategy:': 'খাদ্য কৌশল:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "পরিমিত ক্যালোরি ঘাটতি (প্রায় ৪৫০ কিলোক্যালোরি কম) যাতে সহনশীলতা অক্ষুণ্ন রেখে চর্বি হ্রাস পায়।",
        '5. Physical Training': '৫. শারীরিক প্রশিক্ষণ',
        'Exercise Recommendations': 'ব্যায়াম সুপারিশমালা',
        'Exercise / Drill': 'ব্যায়াম / ড্রিল',
        'Exercise Name': 'ব্যায়ামের নাম',
        'Sets': 'সেট',
        'Reps / Volume': 'রেপস / পরিমাণ',
        'Duration': 'সময়কাল',
        'Frequency': 'পুনরাবৃত্তি',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'উচ্চগতির অ্যারোবিক জগ / ক্রস-কান্ট্রি (৪ - ৬ কিমি)',
        'Continuous steady state': 'একটানা স্থিতিশীল গতি',
        '35 - 40 mins': '৩৫ - ৪০ মিনিট',
        '4 days/week': '৪ দিন / সপ্তাহ',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '৬. প্রত্যাশিত অগ্রগতির মাইলফলক (৩০ / ৬০ / ৯০ দিন)',
        'Progression Timeline': 'অগ্রগতির সময়রেখা',
        'Timeline': 'সময়রেখা',
        'Projected Weight': 'প্রত্যাশিত ওজন',
        'Projected BMI': 'প্রত্যাশিত বিএমআই',
        'Estimated Physical Readiness Score': 'প্রত্যাশিত ফিটনেস স্কোর',
        'Current Baseline': 'বর্তমান ভিত্তি (Baseline)',
        '30 Days Projected': '৩০ দিনের পূর্বাভাস',
        '60 Days Projected': '৬০ দিনের পূর্বাভাস',
        '90 Days Projected': '৯০ দিনের পূর্বাভাস',
        'UNIT MANAGEMENT SYSTEM': 'ইউনিট ম্যানেজমেন্ট সিস্টেম',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'ইউনিট ম্যানেজমেন্ট সিস্টেম',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'ইউনিট ম্যানেজমেন্ট সিস্টেম',
        'UMS 15 CESR': 'ইউনিট ম্যানেজমেন্ট সিস্টেম',
        '8. Personalized Nutrition Recommendations': '৮. ব্যক্তিগত পুষ্টি সুপারিশ',
        'Personalized Nutrition Recommendations': 'ব্যক্তিগত পুষ্টি সুপারিশ',
        "✔ DO'S (Recommended Protocol):": "✔ করণীয় (প্রস্তাবিত নির্দেশিকা):",
        "✔ DO'S (Recommended Protocol)": "✔ করণীয় (প্রস্তাবিত নির্দেশিকা)",
        "DO'S (Recommended Protocol):": "✔ করণীয় (প্রস্তাবিত নির্দেশিকা):",
        "DO'S (Recommended Protocol)": "✔ করণীয় (প্রস্তাবিত নির্দেশিকা)",
        "DO'S": "করণীয়",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ বর্জনীয় (পরিহার করার মতো অভ্যাস ও খাদ্য):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ বর্জনীয় (পরিহার করার মতো অভ্যাস ও খাদ্য):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ বর্জনীয় (পরিহার করার মতো অভ্যাস ও খাদ্য)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ বর্জনীয় (পরিহার করার মতো অভ্যাস ও খাদ্য)",
        "DON'TS (Items & Habits to Avoid):": "✖ বর্জনীয় (পরিহার করার মতো অভ্যাস ও খাদ্য):",
        "DONTS (Items & Habits to Avoid):": "✖ বর্জনীয় (পরিহার করার মতো অভ্যাস ও খাদ্য):",
        "DON'TS": "বর্জনীয়",
        "DONTS": "বর্জনীয়",
        'Operational Nutrition & Hydration Discipline:': 'অপারেশনাল পুষ্টি এবং হাইড্রেশন শৃঙ্খলা:',
        'Operational Nutrition & Hydration Discipline': 'অপারেশনাল পুষ্টি এবং হাইড্রেশন শৃঙ্খলা',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'পেশী প্রোটিন গঠনের জন্য মুরগির মাংস, সিদ্ধ ডিম এবং পনির',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'টেকসই অ্যামিনো অ্যাসিডের জন্য গোটা মসুর ডাল এবং অঙ্কুরিত শস্য',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'গ্লাইকোজেন পূরণের জন্য গোটা শস্য (ওটস, ব্রাউন রাইস, লাল আটার রুটি)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'ইলেক্ট্রোলাইটস এবং খনিজের জন্য তাজা ফল ও সবুজ শাকসবজি',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'প্রতিদিন কমপক্ষে ৩.০ থেকে ৩.৫ লিটার পরিষ্কার জল পান করা',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'ডিপ-ফ্রাই করা মেসের খাবার, পকোড়া এবং প্রক্রিয়াজাত কেন্টিনের খাবার',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'পরিশোধিত চিনি, মিষ্টি চা/কফি এবং কোমল পানীয়',
        'Excessive table salt, pickles, and high-sodium processed rations': 'অতিরিক্ত লবণ, আচার এবং উচ্চ সোডিয়ামযুক্ত প্রক্রিয়াজাত খাবার',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'খাবারের অনিয়মিত সময় বা সকালের পিটির আগে প্রাতঃরাশ বাদ দেওয়া',
        'Heavy meals consumed less than 2 hours before lights out': 'ঘুমানোর (লাইটস আউট) ২ ঘণ্টার কম সময় আগে ভারী খাবার খাওয়া',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'খাবারের নিয়মিত সময় বজায় রাখুন; ঘুমানোর কমপক্ষে ২ ঘণ্টা আগে রাতের খাবার শেষ করুন।',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'পেশীর দ্রুত পুনরুদ্ধারের জন্য প্রোটিনকে (ডাল, অঙ্কুরিত শস্য, পনির, ডিম, মুরগি) অগ্রাধিকার দিন।',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'ইউনিট ক্যান্টিনের ভাজা খাবার, মিষ্টি পানীয় এবং প্রক্রিয়াজাত মিষ্টান্ন পরিহার করুন।',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'প্রতিদিন কমপক্ষে ৩.৫ থেকে ৪.০ লিটার জল পান নিশ্চিত করুন, বিশেষ করে আউটডোর পিটি চলাকালীন।',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'প্রয়োজনীয় খনিজ ও ইলেক্ট্রোলাইটসের জন্য সবুজ শাকসবজি এবং মৌসুমি লেবুজাতীয় ফল অন্তর্ভুক্ত করুন।',
    },
    'pa': {

        'Personal Fitness Report': 'ਨਿੱਜੀ ਫਿਟਨੈਸ ਰਿਪੋਰਟ',
        'Personnal Fitness Report': 'ਨਿੱਜੀ ਫਿਟਨੈਸ ਰਿਪੋਰਟ',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'ਨਿੱਜੀ ਫਿਟਨੈਸ ਰਿਪੋਰਟ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 ਕੋਰ / 15 ਸੀਈਐਸਆਰ — ਯੂਨਿਟ ਪ੍ਰਬੰਧਨ ਪ੍ਰਣਾਲੀ',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'ਏਆਈ/ਐਮਐਲ ਨਿੱਜੀ ਫਿਟਨੈਸ ਭਵਿੱਖਬਾਣੀ ਅਤੇ ਰਿਪੋਰਟ',
        'Individual Fitness Report': 'ਨਿੱਜੀ ਫਿਟਨੈਸ ਰਿਪੋਰਟ',
        'Report Generated': 'ਰਿਪੋਰਟ ਮਿਤੀ',
        'Model Version': 'ਮਾਡਲ ਸੰਸਕਰਣ',
        'CONFIDENTIAL': 'ਗੁਪਤ',
        '1. Soldier Particulars & Service Profile': '1. ਸਿਪਾਹੀ ਦੇ ਵੇਰਵੇ ਅਤੇ ਸੇਵਾ ਪ੍ਰੋਫਾਈਲ',
        'Personnel Details': 'ਸਿਪਾਹੀ ਦੇ ਵੇਰਵੇ',
        'Army Number:': 'ਆਰਮੀ ਨੰਬਰ:',
        'Full Name:': 'ਪੂਰਾ ਨਾਮ:',
        'Rank / Trade:': 'ਅਹੁਦਾ / ਟਰੇਡ:',
        'Company / Section:': 'ਕੰਪਨੀ / ਸੈਕਸ਼ਨ:',
        'Age / Service:': 'ਉਮਰ / ਸੇਵਾ:',
        'Medical Status:': 'ਮੈਡੀਕਲ ਸਥਿਤੀ:',
        'Years': 'ਸਾਲ',
        'SHAPE-1 Cleared': 'ਸ਼ੇਪ-1 ਪਾਸ',
        'Restricted / LMC': 'ਪ੍ਰਤਿਬੰਧਿਤ / ਐਲਐਮਸੀ',
        '2. Physiological Metrics & Physical Performance': '2. ਸਰੀਰਕ ਮਾਪ ਅਤੇ ਪ੍ਰਦਰਸ਼ਨ ਵਿਸ਼ਲੇਸ਼ਣ',
        'Fitness Assessment': 'ਫਿਟਨੈਸ ਮੁਲਾਂਕਣ',
        'Current Fitness Level': 'ਮੌਜੂਦਾ ਫਿਟਨੈਸ ਪੱਧਰ',
        'Height / Actual Weight:': 'ਕੱਦ / ਅਸਲ ਭਾਰ:',
        'Ideal Reference Weight:': 'ਆਦਰਸ਼ ਮਿਆਰੀ ਭਾਰ:',
        'BMI Index & Category:': 'ਬੀਐਮਆਈ ਸੂਚਕਾਂਕ ਅਤੇ ਸ਼੍ਰੇਣੀ:',
        'Weight Deviation:': 'ਭਾਰ ਵਿੱਚ ਅੰਤਰ:',
        'BPET Grading:': 'ਬੀਪੀਈਟੀ ਗਰੇਡਿੰਗ:',
        'PPT Grading:': 'ਪੀਪੀਟੀ ਗਰੇਡਿੰਗ:',
        'Sports & Athletics:': 'ਖੇਡਾਂ ਅਤੇ ਅਥਲੈਟਿਕਸ:',
        'Physical Activity Level:': 'ਸਰੀਰਕ ਗਤੀਵਿਧੀ ਪੱਧਰ:',
        'Normal (Ideal)': 'ਆਮ (ਆਦਰਸ਼)',
        'Normal': 'ਆਮ',
        'Overweight': 'ਵੱਧ ਭਾਰ',
        'Underweight': 'ਘੱਟ ਭਾਰ',
        'EXCELLENT': 'ਸ਼ਾਨਦਾਰ (EXCELLENT)',
        'GOOD': 'ਚੰਗਾ (GOOD)',
        'SATISFACTORY': 'ਤਸੱਲੀਬਖ਼ਸ਼ (SATISFACTORY)',
        'Moderate': 'ਦਰਮਿਆਨਾ',
        'Active': 'ਸਰਗਰਮ',
        'Sports': 'ਖੇਡਾਂ',
        'Football': 'ਫੁੱਟਬਾਲ',
        '3. AI Physical Readiness Prediction': '3. ਏਆਈ ਸਰੀਰਕ ਤਿਆਰੀ ਭਵਿੱਖਬਾਣੀ',
        'Fitness Score': 'ਫਿਟਨੈਸ ਸਕੋਰ',
        'Fitness Status': 'ਫਿਟਨੈਸ ਸਥਿਤੀ',
        'AI Physical Readiness Score:': 'ਏਆਈ ਸਰੀਰਕ ਤਿਆਰੀ ਸਕੋਰ:',
        'Prediction Confidence:': 'ਭਵਿੱਖਬਾਣੀ ਸ਼ੁੱਧਤਾ:',
        'Algorithm:': 'ਐਲਗੋਰਿਦਮ:',
        'Key Strengths (Positive Indicators):': 'ਮੁੱਖ ਖੂਬੀਆਂ (ਸਕਾਰਾਤਮਕ ਸੰਕੇਤਕ):',
        'Priority Action Areas:': 'ਤਰਜੀਹੀ ਸੁਧਾਰ ਖੇਤਰ:',
        'Good Fitness': 'ਵਧੀਆ ਫਿਟਨੈਸ (Good Fitness)',
        'Excellent Readiness': 'ਬਿਹਤਰੀਨ ਤਿਆਰੀ (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "ਉੱਚ ਬੀਪੀਈਟੀ ਪ੍ਰਦਰਸ਼ਨ: ਸਰੀਰਕ ਸਹਿਣਸ਼ੀਲਤਾ ਟੈਸਟ ਵਿੱਚ 'ਸ਼ਾਨਦਾਰ' ਗਰੇਡਿੰਗ ਪ੍ਰਾਪਤ ਕੀਤੀ।",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "ਸਾਫ਼ ਮੈਡੀਕਲ ਪ੍ਰੋਫਾਈਲ: ਡਾਕਟਰੀ ਤੌਰ 'ਤੇ ਸ਼ੇਪ-1 ਜਿਸ ਵਿੱਚ ਕਸਰਤ 'ਤੇ ਕੋਈ ਪਾਬੰਦੀ ਨਹੀਂ ਹੈ।",
        '4. Personalized Dietary & Macronutrient Plan': '4. ਨਿੱਜੀ ਖੁਰਾਕ ਅਤੇ ਪੋਸ਼ਣ ਯੋਜਨਾ',
        'Personalized Recommendations': 'ਨਿੱਜੀ ਸਿਫ਼ਾਰਸ਼ਾਂ',
        'Diet Recommendations': 'ਖੁਰਾਕ ਸਿਫ਼ਾਰਸ਼ਾਂ',
        'Daily Energy Target:': 'ਰੋਜ਼ਾਨਾ ਊਰਜਾ ਟੀਚਾ:',
        'Daily Hydration Target:': 'ਰੋਜ਼ਾਨਾ ਪਾਣੀ ਦਾ ਟੀਚਾ:',
        'Protein Target:': 'ਪ੍ਰੋਟੀਨ ਟੀਚਾ:',
        'Carbs / Fats:': 'ਕਾਰਬੋਹਾਈਡਰੇਟ / ਚਰਬੀ:',
        'Carbs:': 'ਕਾਰਬੋਹਾਈਡਰੇਟ:',
        'Fats:': 'ਚਰਬੀ:',
        'Diet Strategy:': 'ਖੁਰਾਕ ਰਣਨੀਤੀ:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "ਦਰਮਿਆਨੀ ਕੈਲੋਰੀ ਘਾਟ (ਲਗਭਗ 450 ਕਿਲੋ ਕੈਲੋਰੀ ਘੱਟ) ਤਾਂ ਜੋ ਸਟੈਮਿਨਾ ਬਰਕਰਾਰ ਰੱਖਦੇ ਹੋਏ ਚਰਬੀ ਘਟ ਸਕੇ।",
        '5. Physical Training': '5. ਸਰੀਰਕ ਸਿਖਲਾਈ',
        'Exercise Recommendations': 'ਕਸਰਤ ਸਿਫ਼ਾਰਸ਼ਾਂ',
        'Exercise / Drill': 'ਕਸਰਤ / ਡਰਿੱਲ',
        'Exercise Name': 'ਕਸਰਤ ਦਾ ਨਾਮ',
        'Sets': 'ਸੈੱਟ',
        'Reps / Volume': 'ਰੈਪਸ / ਮਾਤਰਾ',
        'Duration': 'ਸਮਾਂ',
        'Frequency': 'ਵਾਰਵਾਰਤਾ',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'ਤੇਜ਼ ਰਫ਼ਤਾਰ ਐਰੋਬਿਕ ਦੌੜ / ਕਰਾਸ-ਕੰਟਰੀ (4 - 6 ਕਿਲੋਮੀਟਰ)',
        'Continuous steady state': 'ਲਗਾਤਾਰ ਸਥਿਰ ਗਤੀ',
        '35 - 40 mins': '35 - 40 ਮਿੰਟ',
        '4 days/week': '4 ਦਿਨ / ਹਫ਼ਤਾ',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. ਅਨੁਮਾਨਿਤ ਪ੍ਰਗਤੀ ਦੇ ਪੜਾਅ (30 / 60 / 90 ਦਿਨ)',
        'Progression Timeline': 'ਪ੍ਰਗਤੀ ਸਮਾਂਰੇਖਾ',
        'Timeline': 'ਸਮਾਂਰੇਖਾ',
        'Projected Weight': 'ਅਨੁਮਾਨਿਤ ਭਾਰ',
        'Projected BMI': 'ਅਨੁਮਾਨਿਤ ਬੀਐਮਆਈ',
        'Estimated Physical Readiness Score': 'ਅਨੁਮਾਨਿਤ ਫਿਟਨੈਸ ਸਕੋਰ',
        'Current Baseline': 'ਮੌਜੂਦਾ ਅਧਾਰ (Baseline)',
        '30 Days Projected': '30 ਦਿਨ ਦਾ ਅਨੁਮਾਨ',
        '60 Days Projected': '60 ਦਿਨ ਦਾ ਅਨੁਮਾਨ',
        '90 Days Projected': '90 ਦਿਨ ਦਾ ਅਨੁਮਾਨ',
        'UNIT MANAGEMENT SYSTEM': 'ਯੂਨਿਟ ਪ੍ਰਬੰਧਨ ਪ੍ਰਣਾਲੀ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'ਯੂਨਿਟ ਪ੍ਰਬੰਧਨ ਪ੍ਰਣਾਲੀ',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'ਯੂਨਿਟ ਪ੍ਰਬੰਧਨ ਪ੍ਰਣਾਲੀ',
        'UMS 15 CESR': 'ਯੂਨਿਟ ਪ੍ਰਬੰਧਨ ਪ੍ਰਣਾਲੀ',
        '8. Personalized Nutrition Recommendations': '8. ਵਿਅਕਤੀਗਤ ਪੋਸ਼ਣ ਸੰਬੰਧੀ ਸਿਫ਼ਾਰਸ਼ਾਂ',
        'Personalized Nutrition Recommendations': 'ਵਿਅਕਤੀਗਤ ਪੋਸ਼ਣ ਸੰਬੰਧੀ ਸਿਫ਼ਾਰਸ਼ਾਂ',
        "✔ DO'S (Recommended Protocol):": "✔ ਕੀ ਕਰਨਾ ਹੈ (ਸਿਫ਼ਾਰਸ਼ ਕੀਤਾ ਪ੍ਰੋਟੋਕੋਲ):",
        "✔ DO'S (Recommended Protocol)": "✔ ਕੀ ਕਰਨਾ ਹੈ (ਸਿਫ਼ਾਰਸ਼ ਕੀਤਾ ਪ੍ਰੋਟੋਕੋਲ)",
        "DO'S (Recommended Protocol):": "✔ ਕੀ ਕਰਨਾ ਹੈ (ਸਿਫ਼ਾਰਸ਼ ਕੀਤਾ ਪ੍ਰੋਟੋਕੋਲ):",
        "DO'S (Recommended Protocol)": "✔ ਕੀ ਕਰਨਾ ਹੈ (ਸਿਫ਼ਾਰਸ਼ ਕੀਤਾ ਪ੍ਰੋਟੋਕੋਲ)",
        "DO'S": "ਕੀ ਕਰਨਾ ਹੈ",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ ਕੀ ਨਹੀਂ ਕਰਨਾ (ਪਰਹੇਜ਼ ਕਰਨ ਯੋਗ ਆਦਤਾਂ ਅਤੇ ਚੀਜ਼ਾਂ):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ ਕੀ ਨਹੀਂ ਕਰਨਾ (ਪਰਹੇਜ਼ ਕਰਨ ਯੋਗ ਆਦਤਾਂ ਅਤੇ ਚੀਜ਼ਾਂ):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ ਕੀ ਨਹੀਂ ਕਰਨਾ (ਪਰਹੇਜ਼ ਕਰਨ ਯੋਗ ਆਦਤਾਂ ਅਤੇ ਚੀਜ਼ਾਂ)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ ਕੀ ਨਹੀਂ ਕਰਨਾ (ਪਰਹੇਜ਼ ਕਰਨ ਯੋਗ ਆਦਤਾਂ ਅਤੇ ਚੀਜ਼ਾਂ)",
        "DON'TS (Items & Habits to Avoid):": "✖ ਕੀ ਨਹੀਂ ਕਰਨਾ (ਪਰਹੇਜ਼ ਕਰਨ ਯੋਗ ਆਦਤਾਂ ਅਤੇ ਚੀਜ਼ਾਂ):",
        "DONTS (Items & Habits to Avoid):": "✖ ਕੀ ਨਹੀਂ ਕਰਨਾ (ਪਰਹੇਜ਼ ਕਰਨ ਯੋਗ ਆਦਤਾਂ ਅਤੇ ਚੀਜ਼ਾਂ):",
        "DON'TS": "ਕੀ ਨਹੀਂ ਕਰਨਾ",
        "DONTS": "ਕੀ ਨਹੀਂ ਕਰਨਾ",
        'Operational Nutrition & Hydration Discipline:': 'ਆਪਰੇਸ਼ਨਲ ਪੋਸ਼ਣ ਅਤੇ ਹਾਈਡ੍ਰੇਸ਼ਨ ਅਨੁਸ਼ਾਸਨ:',
        'Operational Nutrition & Hydration Discipline': 'ਆਪਰੇਸ਼ਨਲ ਪੋਸ਼ਣ ਅਤੇ ਹਾਈਡ੍ਰੇਸ਼ਨ ਅਨੁਸ਼ਾਸਨ',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'ਮਾਸਪੇਸ਼ੀਆਂ ਦੇ ਪ੍ਰੋਟੀਨ ਨਿਰਮਾਣ ਲਈ ਚਿਕਨ, ਉਬਲੇ ਅੰਡੇ ਅਤੇ ਪਨੀਰ',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'ਲਗਾਤਾਰ ਅਮੀਨੋ ਐਸਿਡ ਲਈ ਸਾਬਤ ਦਾਲਾਂ ਅਤੇ ਪੁੰਗਰੀਆਂ ਦਾਲਾਂ',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'ਗਲਾਈਕੋਜਨ ਦੀ ਪੂਰਤੀ ਲਈ ਸਾਬਤ ਅਨਾਜ (ਓਟਸ, ਬ੍ਰਾਊਨ ਰਾਈਸ, ਕਣਕ ਦੀ ਰੋਟੀ)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'ਇਲੈਕਟ੍ਰੋਲਾਈਟਸ ਅਤੇ ਪੌਸ਼ਟਿਕ ਤੱਤਾਂ ਲਈ ਤਾਜ਼ੇ ਮੌਸਮੀ ਫਲ ਅਤੇ ਹਰੀਆਂ ਸਬਜ਼ੀਆਂ',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'ਰੋਜ਼ਾਨਾ ਘੱਟੋ-ਘੱਟ 3.0 ਤੋਂ 3.5 ਲੀਟਰ ਸਾਫ਼ ਪਾਣੀ ਨਾਲ ਲਗਾਤਾਰ ਹਾਈਡ੍ਰੇਸ਼ਨ',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'ਮੈੱਸ ਦੇ ਤਲੇ ਹੋਏ ਸਨੈਕਸ, ਪਕੌੜੇ ਅਤੇ ਪ੍ਰੋਸੈਸਡ ਕੰਟੀਨ ਸਨੈਕਸ',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'ਰਿਫਾਇੰਡ ਚੀਨੀ, ਮਿੱਠੀ ਚਾਹ/ਕੌਫੀ ਅਤੇ ਕੋਲਡ ਡ੍ਰਿੰਕਸ',
        'Excessive table salt, pickles, and high-sodium processed rations': 'ਵੱਧ ਨਮਕ, ਅਚਾਰ ਅਤੇ ਵੱਧ ਸੋਡੀਅਮ ਵਾਲੇ ਪ੍ਰੋਸੈਸਡ ਰਾਸ਼ਨ',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'ਖਾਣੇ ਦਾ ਅਨਿਯਮਿਤ ਸਮਾਂ ਜਾਂ ਸਵੇਰ ਦੀ ਪੀਟੀ ਤੋਂ ਪਹਿਲਾਂ ਨਾਸ਼ਤਾ ਛੱਡਣਾ',
        'Heavy meals consumed less than 2 hours before lights out': 'ਸੌਣ (ਲਾਈਟਸ ਆਊਟ) ਤੋਂ 2 ਘੰਟੇ ਤੋਂ ਘੱਟ ਸਮਾਂ ਪਹਿਲਾਂ ਭਾਰੀ ਭੋਜਨ ਖਾਣਾ',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'ਖਾਣੇ ਦੇ ਨਿਯਮਿਤ ਸਮੇਂ ਦੀ ਪਾਲਣਾ ਕਰੋ; ਸੌਣ ਤੋਂ ਘੱਟੋ-ਘੱਟ 2 ਘੰਟੇ ਪਹਿਲਾਂ ਰਾਤ ਦਾ ਖਾਣਾ ਖਤਮ ਕਰੋ।',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'ਮਾਸਪੇਸ਼ੀਆਂ ਦੀ ਤੇਜ਼ ਰਿਕਵਰੀ ਲਈ ਪ੍ਰੋਟੀਨ (ਦਾਲ, ਪੁੰਗਰੇ ਅਨਾਜ, ਪਨੀਰ, ਅੰਡੇ, ਚਿਕਨ) ਨੂੰ ਤਰਜੀਹ ਦਿਓ।',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'ਯੂਨਿਟ ਕੰਟੀਨ ਤੋਂ ਤਲੇ ਹੋਏ ਸਨੈਕਸ, ਮਿੱਠੇ ਪੀਣ ਵਾਲੇ ਪਦਾਰਥਾਂ ਅਤੇ ਪ੍ਰੋਸੈਸਡ ਮਿਠਾਈਆਂ ਤੋਂ ਪਰਹੇਜ਼ ਕਰੋ।',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'ਰੋਜ਼ਾਨਾ ਘੱਟੋ-ਘੱਟ 3.5 ਤੋਂ 4.0 ਲੀਟਰ ਪਾਣੀ ਪੀਣਾ ਯਕੀਨੀ ਬਣਾਓ, ਖਾਸ ਕਰਕੇ ਬਾਹਰੀ ਪੀਟੀ ਦੌਰਾਨ।',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'ਜ਼ਰੂਰੀ ਪੌਸ਼ਟਿਕ ਤੱਤਾਂ ਅਤੇ ਇਲੈਕਟ੍ਰੋਲਾਈਟਸ ਲਈ ਹਰੀਆਂ ਪੱਤੇਦਾਰ ਸਬਜ਼ੀਆਂ ਅਤੇ ਮੌਸਮੀ ਫਲ ਸ਼ਾਮਲ ਕਰੋ।',
    },
    'mr': {

        'Personal Fitness Report': 'वैयक्तिक तंदुरुस्ती अहवाल',
        'Personnal Fitness Report': 'वैयक्तिक तंदुरुस्ती अहवाल',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'वैयक्तिक तंदुरुस्ती अहवाल',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 कॉर्प्स / 15 सीईएसआर — युनिट व्यवस्थापन प्रणाली',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'एआय/एमएल वैयक्तिक तंदुरुस्ती अंदाज आणि अहवाल',
        'Individual Fitness Report': 'वैयक्तिक तंदुरुस्ती अहवाल',
        'Report Generated': 'अहवाल तारीख',
        'Model Version': 'मॉडेल आवृत्ती',
        'CONFIDENTIAL': 'गोपनीय',
        '1. Soldier Particulars & Service Profile': '1. सैनिकाचा तपशील आणि सेवा प्रोफाइल',
        'Personnel Details': 'सैनिक तपशील',
        'Army Number:': 'आर्मी नंबर:',
        'Full Name:': 'पूर्ण नाव:',
        'Rank / Trade:': 'पद / ट्रेड:',
        'Company / Section:': 'कंपनी / विभाग:',
        'Age / Service:': 'वय / सेवा वर्ष:',
        'Medical Status:': 'वैद्यकीय स्थिती:',
        'Years': 'वर्षे',
        'SHAPE-1 Cleared': 'शेप-1 उत्तीर्ण',
        'Restricted / LMC': 'प्रतिबंधित / एलएमसी',
        '2. Physiological Metrics & Physical Performance': '2. शारीरिक मापदंड आणि कार्यक्षमता विश्लेषण',
        'Fitness Assessment': 'तंदुरुस्ती मूल्यांकन',
        'Current Fitness Level': 'सध्याची तंदुरुस्ती पातळी',
        'Height / Actual Weight:': 'उंची / प्रत्यक्ष वजन:',
        'Ideal Reference Weight:': 'आदर्श मानक वजन:',
        'BMI Index & Category:': 'बीएमआय निर्देशांक आणि श्रेणी:',
        'Weight Deviation:': 'वजनातील फरक:',
        'BPET Grading:': 'बीपीईटी श्रेणी:',
        'PPT Grading:': 'पीपीटी श्रेणी:',
        'Sports & Athletics:': 'खेळ आणि ॲथलेटिक्स:',
        'Physical Activity Level:': 'शारीरिक हालचाल पातळी:',
        'Normal (Ideal)': 'सामान्य (आदर्श)',
        'Normal': 'सामान्य',
        'Overweight': 'जास्त वजन',
        'Underweight': 'कमी वजन',
        'EXCELLENT': 'उत्कृष्ट (EXCELLENT)',
        'GOOD': 'चांगले (GOOD)',
        'SATISFACTORY': 'समाधानकारक (SATISFACTORY)',
        'Moderate': 'मध्यम',
        'Active': 'सक्रिय',
        'Sports': 'खेळ',
        'Football': 'फुटबॉल',
        '3. AI Physical Readiness Prediction': '3. एआय शारीरिक सज्जता अंदाज',
        'Fitness Score': 'तंदुरुस्ती गुण',
        'Fitness Status': 'तंदुरुस्ती स्थिती',
        'AI Physical Readiness Score:': 'एआय शारीरिक सज्जता गुण:',
        'Prediction Confidence:': 'अंदाज अचूकता:',
        'Algorithm:': 'अल्गोरिदम:',
        'Key Strengths (Positive Indicators):': 'मुख्य सामर्थ्ये (सकारात्मक निर्देशक):',
        'Priority Action Areas:': 'प्राधान्य सुधारणा क्षेत्र:',
        'Good Fitness': 'चांगली तंदुरुस्ती (Good Fitness)',
        'Excellent Readiness': 'उत्कृष्ट सज्जता (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "उच्च बीपीईटी कार्यक्षमता: शारीरिक सहनशक्ती चाचणीत 'उत्कृष्ट' श्रेणी मिळवली.",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "स्वच्छ वैद्यकीय प्रोफाइल: वैद्यकीयदृष्ट्या शेप-1, व्यायामावर कोणतेही बंधन नाही.",
        '4. Personalized Dietary & Macronutrient Plan': '4. वैयक्तिक आहार आणि पोषण योजना',
        'Personalized Recommendations': 'वैयक्तिक शिफारसी',
        'Diet Recommendations': 'आहार शिफारसी',
        'Daily Energy Target:': 'दैनंदिन ऊर्जा लक्ष्य:',
        'Daily Hydration Target:': 'दैनंदिन पाणी लक्ष्य:',
        'Protein Target:': 'प्रथिने लक्ष्य:',
        'Carbs / Fats:': 'कर्बोदके / चरबी:',
        'Carbs:': 'कर्बोदके:',
        'Fats:': 'चरबी:',
        'Diet Strategy:': 'आहार रणनीती:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "मध्यम कॅलरी तूट (अंदाजे 450 किलो कॅलरी कमी) जेणेकरून सहनशक्ती कायम ठेवून चरबी कमी होईल.",
        '5. Physical Training': '5. शारीरिक प्रशिक्षण',
        'Exercise Recommendations': 'व्यायाम शिफारसी',
        'Exercise / Drill': 'व्यायाम / ड्रिल',
        'Exercise Name': 'व्यायामाचे नाव',
        'Sets': 'सेट्स',
        'Reps / Volume': 'रेप्स / प्रमाण',
        'Duration': 'कालावधी',
        'Frequency': 'वारंवारता',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'जलद ॲरोबिक जॉग / क्रॉस-कंट्री (4 - 6 किमी)',
        'Continuous steady state': 'सतत स्थिर गती',
        '35 - 40 mins': '35 - 40 मिनिटे',
        '4 days/week': '4 दिवस / आठवडा',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. अपेक्षित प्रगती टप्पे (30 / 60 / 90 दिवस)',
        'Progression Timeline': 'प्रगती समयरेखा',
        'Timeline': 'समयरेखा',
        'Projected Weight': 'अपेक्षित वजन',
        'Projected BMI': 'अपेक्षित बीएमआय',
        'Estimated Physical Readiness Score': 'अपेक्षित तंदुरुस्ती गुण',
        'Current Baseline': 'सध्याचा पाया (Baseline)',
        '30 Days Projected': '30 दिवसांचा अंदाज',
        '60 Days Projected': '60 दिवसांचा अंदाज',
        '90 Days Projected': '90 दिवसांचा अंदाज',
        'UNIT MANAGEMENT SYSTEM': 'युनिट व्यवस्थापन प्रणाली',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'युनिट व्यवस्थापन प्रणाली',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'युनिट व्यवस्थापन प्रणाली',
        'UMS 15 CESR': 'युनिट व्यवस्थापन प्रणाली',
        '8. Personalized Nutrition Recommendations': '८. वैयक्तिकृत पोषण शिफारसी',
        'Personalized Nutrition Recommendations': 'वैयक्तिकृत पोषण शिफारसी',
        "✔ DO'S (Recommended Protocol):": "✔ काय करावे (शिफारस केलेली नियमावली):",
        "✔ DO'S (Recommended Protocol)": "✔ काय करावे (शिफारस केलेली नियमावली)",
        "DO'S (Recommended Protocol):": "✔ काय करावे (शिफारस केलेली नियमावली):",
        "DO'S (Recommended Protocol)": "✔ काय करावे (शिफारस केलेली नियमावली)",
        "DO'S": "काय करावे",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ काय करू नये (टाळायच्या गोष्टी आणि सवयी):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ काय करू नये (टाळायच्या गोष्टी आणि सवयी):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ काय करू नये (टाळायच्या गोष्टी आणि सवयी)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ काय करू नये (टाळायच्या गोष्टी आणि सवयी)",
        "DON'TS (Items & Habits to Avoid):": "✖ काय करू नये (टाळायच्या गोष्टी आणि सवयी):",
        "DONTS (Items & Habits to Avoid):": "✖ काय करू नये (टाळायच्या गोष्टी आणि सवयी):",
        "DON'TS": "काय करू नये",
        "DONTS": "काय करू नये",
        'Operational Nutrition & Hydration Discipline:': 'ऑपरेशनल पोषण आणि हायड्रेशन शिस्त:',
        'Operational Nutrition & Hydration Discipline': 'ऑपरेशनल पोषण आणि हायड्रेशन शिस्त',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'स्नायू प्रथिन निर्मितीसाठी चिकन, उकडलेली अंडी आणि पनीर',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'सातत्यपूर्ण अमिनो ऍसिडसाठी अख्खी डाळ आणि मोड आलेली कडधान्ये',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'ग्लायकोजेन भरून काढण्यासाठी संपूर्ण धान्य (ओट्स, ब्राऊन राईस, गव्हाची पोळी)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'इलेक्ट्रोलाइट्स आणि सूक्ष्म पोषक घटकांसाठी हंगामी ताजी फळे आणि पालेभाज्या',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'दररोज किमान ३.० ते ३.५ लिटर स्वच्छ पाणी पिऊन शरीरातील पाण्याचे प्रमाण राखणे',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'मेसमधील तळलेले पदार्थ, भजी आणि कॅन्टीनमधील प्रक्रिया केलेले पदार्थ',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'रिफाइंड साखर, गोड चहा/कॉफी आणि शीतपेये (कार्बोनेटेड पेये)',
        'Excessive table salt, pickles, and high-sodium processed rations': 'जास्त मीठ, लोणचे आणि जास्त सोडियम असलेले प्रक्रिया केलेले अन्न',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'जेवणाची अनियमित वेळ किंवा सकाळच्या पीटीपूर्वी नाश्ता न करणे',
        'Heavy meals consumed less than 2 hours before lights out': 'झोपण्यापूर्वी (लाइट्स आऊट) २ तासांपेक्षा कमी वेळेत जड जेवण करणे',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'जेवणाची नियमित वेळ पाळा; झोपण्यापूर्वी किमान २ तास आधी रात्रीचे जेवण पूर्ण करा.',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'स्नायूंच्या जलद रिकव्हरीसाठी प्रथिनांना (डाळ, मोड आलेली कडधान्ये, पनीर, अंडी, चिकन) प्राधान्य द्या.',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'युनिट कॅन्टीनमधील तळलेले स्नॅक्स, गोड पेये आणि प्रक्रिया केलेले गोड पदार्थ टाळा.',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'दररोज किमान ३.५ ते ४.० लिटर पाणी पिणे सुनिश्चित करा, विशेषतः मैदानी पीटी सत्रांमध्ये.',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'महत्त्वपूर्ण पोषक घटकांसाठी हिरव्या पालेभाज्या आणि हंगामी लिंबूवर्गीय फळांचा आहारात समावेश करा.',
    },
    'gu': {

        'Personal Fitness Report': 'વ્યક્તિગત ફિટનેસ રિપોર્ટ',
        'Personnal Fitness Report': 'વ્યક્તિગત ફિટનેસ રિપોર્ટ',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'વ્યક્તિગત ફિટનેસ રિપોર્ટ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 કોર્પ્સ / 15 સીઈએસઆર — યુનિટ મેનેજમેન્ટ સિસ્ટમ',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'એઆઈ/એમએલ વ્યક્તિગત ફિટનેસ અનુમાન અને રિપોર્ટ',
        'Individual Fitness Report': 'વ્યક્તિગત ફિટનેસ રિપોર્ટ',
        'Report Generated': 'રિપોર્ટ તારીખ',
        'Model Version': 'મોડેલ આવૃત્તિ',
        'CONFIDENTIAL': 'ગોપનીય',
        '1. Soldier Particulars & Service Profile': '1. સૈનિક વિગત અને સેવા પ્રોફાઇલ',
        'Personnel Details': 'સૈનિક વિગત',
        'Army Number:': 'આર્મી નંબર:',
        'Full Name:': 'પૂરું નામ:',
        'Rank / Trade:': 'હોદ્દો / ટ્રેડ:',
        'Company / Section:': 'કંપની / વિભાગ:',
        'Age / Service:': 'ઉંમર / સેવા વર્ષ:',
        'Medical Status:': 'તબીબી સ્થિતિ:',
        'Years': 'વર્ષ',
        'SHAPE-1 Cleared': 'શેપ-1 પાસ',
        'Restricted / LMC': 'પ્રતિબંધિત / એલએમસી',
        '2. Physiological Metrics & Physical Performance': '2. શારીરિક માપદંડ અને પ્રદર્શન વિશ્લેષણ',
        'Fitness Assessment': 'ફિટનેસ મૂલ્યાંકન',
        'Current Fitness Level': 'વર્તમાન ફિટનેસ સ્તર',
        'Height / Actual Weight:': 'ઊંચાઈ / વાસ્તવિક વજન:',
        'Ideal Reference Weight:': 'આદર્શ વજન:',
        'BMI Index & Category:': 'બીએમઆઈ અનુક્રમણિકા અને શ્રેણી:',
        'Weight Deviation:': 'વજનમાં તફાવત:',
        'BPET Grading:': 'બીપીઈટી ગ્રેડિંગ:',
        'PPT Grading:': 'પીપીટી ગ્રેડિંગ:',
        'Sports & Athletics:': 'રમતો અને એથ્લેટિક્સ:',
        'Physical Activity Level:': 'શારીરિક પ્રવૃત્તિ સ્તર:',
        'Normal (Ideal)': 'સામાન્ય (આદર્શ)',
        'Normal': 'સામાન્ય',
        'Overweight': 'વધારે વજન',
        'Underweight': 'ઓછું વજન',
        'EXCELLENT': 'ઉત્કૃષ્ટ (EXCELLENT)',
        'GOOD': 'સારું (GOOD)',
        'SATISFACTORY': 'સંતોષકારક (SATISFACTORY)',
        'Moderate': 'મધ્યમ',
        'Active': 'સક્રિય',
        'Sports': 'રમતો',
        'Football': 'ફૂટબોલ',
        '3. AI Physical Readiness Prediction': '3. એઆઈ શારીરિક તત્પરતા અનુમાન',
        'Fitness Score': 'ફિટનેસ સ્કોર',
        'Fitness Status': 'ફિટનેસ સ્થિતિ',
        'AI Physical Readiness Score:': 'એઆઈ શારીરિક તત્પરતા સ્કોર:',
        'Prediction Confidence:': 'અનુમાન ચોકસાઈ:',
        'Algorithm:': 'અલ્ગોરિધમ:',
        'Key Strengths (Positive Indicators):': 'મુખ્ય શક્તિઓ (સકારાત્મક સૂચકો):',
        'Priority Action Areas:': 'સુધારણા ક્ષેત્રો:',
        'Good Fitness': 'સારી ફિટનેસ (Good Fitness)',
        'Excellent Readiness': 'ઉત્કૃષ્ટ તત્પરતા (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "ઉચ્ચ બીપીઈટી પ્રદર્શન: સહનશક્તિ પરીક્ષણમાં 'ઉત્કૃષ્ટ' ગ્રેડિંગ મેળવ્યું.",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "સ્વચ્છ તબીબી પ્રોફાઇલ: તબીબી રીતે શેપ-1, કસરત પર કોઈ પ્રતિબંધ નથી.",
        '4. Personalized Dietary & Macronutrient Plan': '4. વ્યક્તિગત આહાર અને પોષણ યોજના',
        'Personalized Recommendations': 'વ્યક્તિગત ભલામણો',
        'Diet Recommendations': 'આહાર ભલામણો',
        'Daily Energy Target:': 'દૈનિક ઊર્જા લક્ષ્ય:',
        'Daily Hydration Target:': 'દૈનિક પાણી લક્ષ્ય:',
        'Protein Target:': 'પ્રોટીન લક્ષ્ય:',
        'Carbs / Fats:': 'કાર્બોહાઇડ્રેટ / ચરબી:',
        'Carbs:': 'કાર્બોહાઇડ્રેટ:',
        'Fats:': 'ચરબી:',
        'Diet Strategy:': 'આહાર વ્યૂહરચના:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "મધ્યમ કેલરી ખાધ (આશરે 450 કેલરી ઓછી) જેથી સ્ટેમિના જાળવી રાખીને ચરબી ઘટે.",
        '5. Physical Training': '5. શારીરિક તાલીમ',
        'Exercise Recommendations': 'કસરત ભલામણો',
        'Exercise / Drill': 'કસરત / ડ્રીલ',
        'Exercise Name': 'કસરતનું નામ',
        'Sets': 'સેટ્સ',
        'Reps / Volume': 'રેપ્સ / પ્રમાણ',
        'Duration': 'સમયગાળો',
        'Frequency': 'આવૃત્તિ',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'ઝડપી એરોબિક જોગ / ક્રોસ-કન્ટ્રી (4 - 6 કિમી)',
        'Continuous steady state': 'સતત સ્થિર ગતિ',
        '35 - 40 mins': '35 - 40 મિનિટ',
        '4 days/week': '4 દિવસ / અઠવાડિયું',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. અપેક્ષિત પ્રગતિ તબક્કા (30 / 60 / 90 દિવસ)',
        'Progression Timeline': 'પ્રગતિ સમયરેખા',
        'Timeline': 'સમયરેખા',
        'Projected Weight': 'અપેક્ષિત વજન',
        'Projected BMI': 'અપેક્ષિત બીએમઆઈ',
        'Estimated Physical Readiness Score': 'અપેક્ષિત ફિટનેસ સ્કોર',
        'Current Baseline': 'વર્તમાન આધાર (Baseline)',
        '30 Days Projected': '30 દિવસનો અંદાજ',
        '60 Days Projected': '60 દિવસનો અંદાજ',
        '90 Days Projected': '90 દિવસનો અંદાજ',
        'UNIT MANAGEMENT SYSTEM': 'યુનિટ મેનેજમેન્ટ સિસ્ટમ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'યુનિટ મેનેજમેન્ટ સિસ્ટમ',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'યુનિટ મેનેજમેન્ટ સિસ્ટમ',
        'UMS 15 CESR': 'યુનિટ મેનેજમેન્ટ સિસ્ટમ',
        '8. Personalized Nutrition Recommendations': '8. વ્યક્તિગત પોષણ ભલામણો',
        'Personalized Nutrition Recommendations': 'વ્યક્તિગત પોષણ ભલામણો',
        "✔ DO'S (Recommended Protocol):": "✔ શું કરવું (ભલામણ કરેલ નિયમો):",
        "✔ DO'S (Recommended Protocol)": "✔ શું કરવું (ભલામણ કરેલ નિયમો)",
        "DO'S (Recommended Protocol):": "✔ શું કરવું (ભલામણ કરેલ નિયમો):",
        "DO'S (Recommended Protocol)": "✔ શું કરવું (ભલામણ કરેલ નિયમો)",
        "DO'S": "શું કરવું",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ શું ન કરવું (ટાળવા યોગ્ય બાબતો અને આદતો):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ શું ન કરવું (ટાળવા યોગ્ય બાબતો અને આદતો):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ શું ન કરવું (ટાળવા યોગ્ય બાબતો અને આદતો)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ શું ન કરવું (ટાળવા યોગ્ય બાબતો અને આદતો)",
        "DON'TS (Items & Habits to Avoid):": "✖ શું ન કરવું (ટાળવા યોગ્ય બાબતો અને આદતો):",
        "DONTS (Items & Habits to Avoid):": "✖ શું ન કરવું (ટાળવા યોગ્ય બાબતો અને આદતો):",
        "DON'TS": "શું ન કરવું",
        "DONTS": "શું ન કરવું",
        'Operational Nutrition & Hydration Discipline:': 'ઓપરેશનલ પોષણ અને હાઇડ્રેશન શિસ્ત:',
        'Operational Nutrition & Hydration Discipline': 'ઓપરેશનલ પોષણ અને હાઇડ્રેશન શિસ્ત',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'સ્નાયુ પ્રોટીન નિર્માણ માટે ચિકન, બાફેલા ઈંડા અને પનીર',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'સતત એમિનો એસિડ માટે આખી દાળ અને ફણગાવેલા કઠોળ',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'ગ્લાયકોજેન ભરપાઈ કરવા માટે આખા અનાજ (ઓટ્સ, બ્રાઉન રાઇસ, ઘઉંની રોટલી)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'ઇલેક્ટ્રોલાઇટ્સ અને સૂક્ષ્મ પોષકતત્વો માટે મોસમી તાજા ફળો અને લીલા શાકભાજી',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'દરરોજ ઓછામાં ઓછું 3.0 થી 3.5 લિટર સ્વચ્છ પાણી પીવું',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'મેસના તળેલા નાસ્તા, ભજીયા અને પ્રોસેસ્ડ કેન્ટીન ખાદ્યપદાર્થો',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'રિફાઈન્ડ ખાંડ, વધુ પડતી મીઠી ચા/કોફી અને સોફ્ટ ડ્રિંક્સ',
        'Excessive table salt, pickles, and high-sodium processed rations': 'વધારે મીઠું, અથાણાં અને વધુ સોડિયમવાળા પ્રોસેસ્ડ ખોરાક',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'જમવાનો અનિયમિત સમય અથવા સવારની પીટી પહેલાં નાસ્તો છોડી દેવો',
        'Heavy meals consumed less than 2 hours before lights out': 'ઊંઘવાના (લાઇટ્સ આઉટ) 2 કલાક કરતાં ઓછા સમય પહેલાં ભારે ખોરાક લેવો',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'જમવાનો નિયમિત સમય જાળવો; ઊંઘવાના ઓછામાં ઓછા 2 કલાક પહેલાં રાત્રિભોજન પૂરું કરો.',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'સ્નાયુઓના ઝડપી સુધારા માટે પ્રોટીન (દાળ, ફણગાવેલા કઠોળ, પનીર, ઈંડા, ચિકન)ને પ્રાથમિકતા આપો.',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'યુનિટ કેન્ટીનમાંથી તળેલા નાસ્તા, મીઠા પીણાં અને પ્રોસેસ્ડ કન્ફેક્શનરી ટાળો.',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'દરરોજ ઓછામાં ઓછું 3.5 થી 4.0 લિટર પાણી પીવું સુનિશ્ચિત કરો, ખાસ કરીને આઉટડોર પીટી દરમિયાન.',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'મહત્વપૂર્ણ સૂક્ષ્મ પોષકતત્વો અને ઇલેક્ટ્રોલાઇટ્સ માટે લીલા પાંદડાવાળા શાકભાજી અને મોસમી ખાટા ફળોનો સમાવેશ કરો.',
    },
    'ta': {

        'Personal Fitness Report': 'தனிநபர் உடற்தகுதி அறிக்கை',
        'Personnal Fitness Report': 'தனிநபர் உடற்தகுதி அறிக்கை',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'தனிநபர் உடற்தகுதி அறிக்கை',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 கார்ப்ஸ் / 15 சிஇஎஸ்ஆர் — யூனிட் மேலாண்மை அமைப்பு',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'AI/ML தனிநபர் உடற்தகுதி கணிப்பு மற்றும் அறிக்கை',
        'Individual Fitness Report': 'தனிநபர் உடற்தகுதி அறிக்கை',
        'Report Generated': 'அறிக்கை தேதி',
        'Model Version': 'மாதிரி பதிப்பு',
        'CONFIDENTIAL': 'ரகசியமானது',
        '1. Soldier Particulars & Service Profile': '1. படைவீரர் விவரங்கள் மற்றும் சேவை விவரக்குறிப்பு',
        'Personnel Details': 'படைவீரர் விவரங்கள்',
        'Army Number:': 'இராணுவ எண்:',
        'Full Name:': 'முழுப் பெயர்:',
        'Rank / Trade:': 'பதவி / தொழில்:',
        'Company / Section:': 'நிறுவனம் / பிரிவு:',
        'Age / Service:': 'வயது / சேவைக்காலம்:',
        'Medical Status:': 'மருத்துவ நிலை:',
        'Years': 'ஆண்டுகள்',
        'SHAPE-1 Cleared': 'ஷேப்-1 தேர்ச்சி',
        'Restricted / LMC': 'வரையறுக்கப்பட்ட / LMC',
        '2. Physiological Metrics & Physical Performance': '2. உடலியல் அளவீடுகள் மற்றும் செயல்திறன் பகுப்பாய்வு',
        'Fitness Assessment': 'உடற்தகுதி மதிப்பீடு',
        'Current Fitness Level': 'தற்போதைய உடற்தகுதி நிலை',
        'Height / Actual Weight:': 'உயரம் / உண்மையான எடை:',
        'Ideal Reference Weight:': 'சிறந்த நிலையான எடை:',
        'BMI Index & Category:': 'பிஎம்ஐ குறியீடு மற்றும் வகை:',
        'Weight Deviation:': 'எடை வேறுபாடு:',
        'BPET Grading:': 'BPET தரம்:',
        'PPT Grading:': 'PPT தரம்:',
        'Sports & Athletics:': 'விளையாட்டு மற்றும் தடகளம்:',
        'Physical Activity Level:': 'உடற்பயிற்சி நிலை:',
        'Normal (Ideal)': 'இயல்பான (சிறந்த)',
        'Normal': 'இயல்பான',
        'Overweight': 'அதிக எடை',
        'Underweight': 'குறைந்த எடை',
        'EXCELLENT': 'சிறப்பானது (EXCELLENT)',
        'GOOD': 'நன்று (GOOD)',
        'SATISFACTORY': 'திருப்திகரமானது (SATISFACTORY)',
        'Moderate': 'மிதமான',
        'Active': 'சுறுசுறுப்பான',
        'Sports': 'விளையாட்டு',
        'Football': 'கால்பந்து',
        '3. AI Physical Readiness Prediction': '3. AI உடற்தகுதி தயார்நிலை கணிப்பு',
        'Fitness Score': 'உடற்தகுதி மதிப்பெண்',
        'Fitness Status': 'உடற்தகுதி நிலை',
        'AI Physical Readiness Score:': 'AI உடற்தகுதி தயார்நிலை மதிப்பெண்:',
        'Prediction Confidence:': 'கணிப்பு துல்லியம்:',
        'Algorithm:': 'அல்காரிதம்:',
        'Key Strengths (Positive Indicators):': 'முக்கிய பலங்கள் (நேர்மறை குறிகாட்டிகள்):',
        'Priority Action Areas:': 'முன்னுரிமை மேம்பாட்டு பகுதிகள்:',
        'Good Fitness': 'நல்ல உடற்தகுதி (Good Fitness)',
        'Excellent Readiness': 'சிறந்த தயார்நிலை (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "உயர் BPET செயல்திறன்: உடல் சகிப்புத்தன்மை தேர்வில் 'சிறந்த' தரம் பெற்றது.",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "தெளிவான மருத்துவ சுயவிவரம்: உடற்பயிற்சி தடைகள் இல்லாத ஷேப்-1 நிலை.",
        '4. Personalized Dietary & Macronutrient Plan': '4. தனிப்பயனாக்கப்பட்ட உணவு மற்றும் ஊட்டச்சத்து திட்டம்',
        'Personalized Recommendations': 'தனிப்பயன் பரிந்துரைகள்',
        'Diet Recommendations': 'உணவு பரிந்துரைகள்',
        'Daily Energy Target:': 'தினசரி ஆற்றல் இலக்கு:',
        'Daily Hydration Target:': 'தினசரி நீர் இலக்கு:',
        'Protein Target:': 'புரத இலக்கு:',
        'Carbs / Fats:': 'கார்போஹைட்ரேட் / கொழுப்பு:',
        'Carbs:': 'கார்போஹைட்ரேட்:',
        'Fats:': 'கொழுப்பு:',
        'Diet Strategy:': 'உணவு உத்தி:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "சகிப்புத்தன்மையை பராமரித்து கொழுப்பைக் குறைக்க மிதமான கலோரி குறைப்பு (சுமார் 450 kcal).",
        '5. Physical Training': '5. உடற்பயிற்சி பயிற்சி',
        'Exercise Recommendations': 'உடற்பயிற்சி பரிந்துரைகள்',
        'Exercise / Drill': 'உடற்பயிற்சி / துரப்பணம்',
        'Exercise Name': 'பயிற்சியின் பெயர்',
        'Sets': 'செட்',
        'Reps / Volume': 'முறை / அளவு',
        'Duration': 'கால அளவு',
        'Frequency': 'அதிர்வெண்',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'வேகமான ஏரோபிக் ஓட்டம் / கிராஸ்-கன்ட்ரி (4 - 6 கிமீ)',
        'Continuous steady state': 'தொடர்ச்சியான நிலையான வேகம்',
        '35 - 40 mins': '35 - 40 நிமிடங்கள்',
        '4 days/week': '4 நாட்கள் / வாரம்',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. எதிர்பார்க்கப்படும் முன்னேற்ற மைல்கற்கள் (30 / 60 / 90 நாட்கள்)',
        'Progression Timeline': 'முன்னேற்ற காலவரிசை',
        'Timeline': 'காலவரிசை',
        'Projected Weight': 'எதிர்பார்க்கப்படும் எடை',
        'Projected BMI': 'எதிர்பார்க்கப்படும் பிஎம்ஐ',
        'Estimated Physical Readiness Score': 'எதிர்பார்க்கப்படும் உடற்தகுதி மதிப்பெண்',
        'Current Baseline': 'தற்போதைய அடிப்படை (Baseline)',
        '30 Days Projected': '30 நாட்கள் கணிப்பு',
        '60 Days Projected': '60 நாட்கள் கணிப்பு',
        '90 Days Projected': '90 நாட்கள் கணிப்பு',
        'UNIT MANAGEMENT SYSTEM': 'யூனிட் மேலாண்மை அமைப்பு',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'யூனிட் மேலாண்மை அமைப்பு',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'யூனிட் மேலாண்மை அமைப்பு',
        'UMS 15 CESR': 'யூனிட் மேலாண்மை அமைப்பு',
        '8. Personalized Nutrition Recommendations': '8. தனிப்பயனாக்கப்பட்ட ஊட்டச்சத்து பரிந்துரைகள்',
        'Personalized Nutrition Recommendations': 'தனிப்பயனாக்கப்பட்ட ஊட்டச்சத்து பரிந்துரைகள்',
        "✔ DO'S (Recommended Protocol):": "✔ செய்ய வேண்டியவை (பரிந்துரைக்கப்பட்ட நெறிமுறை):",
        "✔ DO'S (Recommended Protocol)": "✔ செய்ய வேண்டியவை (பரிந்துரைக்கப்பட்ட நெறிமுறை)",
        "DO'S (Recommended Protocol):": "✔ செய்ய வேண்டியவை (பரிந்துரைக்கப்பட்ட நெறிமுறை):",
        "DO'S (Recommended Protocol)": "✔ செய்ய வேண்டியவை (பரிந்துரைக்கப்பட்ட நெறிமுறை)",
        "DO'S": "செய்ய வேண்டியவை",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ தவிர்க்க வேண்டியவை (தவிர்க்க வேண்டிய பழக்கங்கள் மற்றும் பொருட்கள்):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ தவிர்க்க வேண்டியவை (தவிர்க்க வேண்டிய பழக்கங்கள் மற்றும் பொருட்கள்):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ தவிர்க்க வேண்டியவை (தவிர்க்க வேண்டிய பழக்கங்கள் மற்றும் பொருட்கள்)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ தவிர்க்க வேண்டியவை (தவிர்க்க வேண்டிய பழக்கங்கள் மற்றும் பொருட்கள்)",
        "DON'TS (Items & Habits to Avoid):": "✖ தவிர்க்க வேண்டியவை (தவிர்க்க வேண்டிய பழக்கங்கள் மற்றும் பொருட்கள்):",
        "DONTS (Items & Habits to Avoid):": "✖ தவிர்க்க வேண்டியவை (தவிர்க்க வேண்டிய பழக்கங்கள் மற்றும் பொருட்கள்):",
        "DON'TS": "தவிர்க்க வேண்டியவை",
        "DONTS": "தவிர்க்க வேண்டியவை",
        'Operational Nutrition & Hydration Discipline:': 'செயல்பாட்டு ஊட்டச்சத்து மற்றும் நீரேற்ற ஒழுக்கம்:',
        'Operational Nutrition & Hydration Discipline': 'செயல்பாட்டு ஊட்டச்சத்து மற்றும் நீரேற்ற ஒழுக்கம்',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'தசை புரத உருவாக்கத்திற்கு கோழி இறைச்சி, வேகவைத்த முட்டை மற்றும் பன்னீர்',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'நிலையான அமினோ அமிலங்களுக்கு முழு பருப்பு மற்றும் முளைகட்டிய பயிர்கள்',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'கிளைகோஜன் மீட்புக்கு முழு தானியங்கள் (ஓட்ஸ், பிரவுன் ரைஸ், கோதுமை ரொட்டி)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'எலக்ட்ரோலைட்டுகள் மற்றும் தாதுக்களுக்கு பருவகால புதிய பழங்கள் மற்றும் காய்கறிகள்',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'தினமும் குறைந்தது 3.0 முதல் 3.5 லிட்டர் சுத்தமான தண்ணீர் குடித்தல்',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'எண்ணெயில் பொரித்த தின்பண்டங்கள், பக்கோடா மற்றும் பதப்படுத்தப்பட்ட பொருட்கள்',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'சுத்திகரிக்கப்பட்ட சர்க்கரை, இனிப்பு டீ/காபி மற்றும் குளிர்பானங்கள்',
        'Excessive table salt, pickles, and high-sodium processed rations': 'அதிகப்படியான உப்பு, ஊறுகாய் மற்றும் அதிக சோடியம் கொண்ட உணவுகள்',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'முறையற்ற உணவு நேரம் அல்லது காலை உடற்பயிற்சிக்கு முன் உணவைத் தவிர்ப்பது',
        'Heavy meals consumed less than 2 hours before lights out': 'தூங்குவதற்கு (லைட்ஸ் அவுட்) 2 மணி நேரத்திற்கும் குறைவான நேரத்தில் கனமான உணவு உண்ணுதல்',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'சீரான உணவு நேரத்தைப் பராமரிக்கவும்; தூங்குவதற்கு குறைந்தது 2 மணி நேரத்திற்கு முன் இரவு உணவை முடிக்கவும்.',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'விரைவான தசை மீட்பை உறுதி செய்ய புரதத்திற்கு (பருப்பு, முளைகள், பன்னீர், முட்டை, கோழி) முன்னுரிமை கொடுங்கள்.',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'யூனிட் கேன்டீனில் இருந்து எண்ணெயில் பொரித்த தின்பண்டங்கள், குளிர்பானங்கள் மற்றும் இனிப்புகளைத் தவிர்க்கவும்.',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'குறிப்பாக வெளிப்புற உடற்பயிற்சியின் போது தினமும் குறைந்தது 3.5 முதல் 4.0 லிட்டர் தண்ணீர் குடிப்பதை உறுதிப்படுத்தவும்.',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'முக்கிய ஊட்டச்சத்துக்கள் மற்றும் எலக்ட்ரோலைட்டுகளுக்கு பச்சை இலைக் காய்கறிகள் மற்றும் சிட்ரஸ் பழங்களைச் சேர்க்கவும்.',
    },
    'te': {

        'Personal Fitness Report': 'వ్యక్తిగత ఫిట్‌నెస్ నివేదిక',
        'Personnal Fitness Report': 'వ్యక్తిగత ఫిట్‌నెస్ నివేదిక',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'వ్యక్తిగత ఫిట్‌నెస్ నివేదిక',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 కార్ప్స్ / 15 సిఈఎస్ఆర్ — యూనిట్ నిర్వహణ వ్యవస్థ',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'ఏఐ/ఎంఎల్ వ్యక్తిగత ఫిట్‌నెస్ అంచనా మరియు నివేదిక',
        'Individual Fitness Report': 'వ్యక్తిగత ఫిట్‌నెస్ నివేదిక',
        'Report Generated': 'నివేదిక తేదీ',
        'Model Version': 'మోడల్ వెర్షన్',
        'CONFIDENTIAL': 'రహస్యమైనది',
        '1. Soldier Particulars & Service Profile': '1. సైనికుడి వివరాలు మరియు సేవా ప్రొఫైల్',
        'Personnel Details': 'సైనికుడి వివరాలు',
        'Army Number:': 'ఆర్మీ నంబర్:',
        'Full Name:': 'పూర్తి పేరు:',
        'Rank / Trade:': 'ర్యాంక్ / ట్రేడ్:',
        'Company / Section:': 'కంపెనీ / విభాగం:',
        'Age / Service:': 'వయస్సు / సేవా కాలం:',
        'Medical Status:': 'వైద్య స్థితి:',
        'Years': 'సంవత్సరాలు',
        'SHAPE-1 Cleared': 'షేప్-1 ఆమోదించబడింది',
        'Restricted / LMC': 'పరిమిత / ఎల్‌ఎమ్‌సి',
        '2. Physiological Metrics & Physical Performance': '2. శరీర కొలతలు మరియు పనితీరు విశ్లేషణ',
        'Fitness Assessment': 'ఫిట్‌నెస్ అంచనా',
        'Current Fitness Level': 'ప్రస్తుత ఫిట్‌నెస్ స్థాయి',
        'Height / Actual Weight:': 'ఎత్తు / అసలు బరువు:',
        'Ideal Reference Weight:': 'ఆదర్శ ప్రామాణిక బరువు:',
        'BMI Index & Category:': 'బిఎమ్‌ఐ సూచిక మరియు వర్గం:',
        'Weight Deviation:': 'బరువు వ్యత్యాసం:',
        'BPET Grading:': 'బిపిఈటి గ్రేడింగ్:',
        'PPT Grading:': 'పిపిటి గ్రేడింగ్:',
        'Sports & Athletics:': 'క్రీడలు మరియు అథ్లెటిక్స్:',
        'Physical Activity Level:': 'శారీరక శ్రమ స్థాయి:',
        'Normal (Ideal)': 'సాధారణ (ఆదర్శ)',
        'Normal': 'సాధారణ',
        'Overweight': 'అధిక బరువు',
        'Underweight': 'తక్కువ బరువు',
        'EXCELLENT': 'అద్భుతమైనది (EXCELLENT)',
        'GOOD': 'మంచిది (GOOD)',
        'SATISFACTORY': 'సంతృప్తికరమైనది (SATISFACTORY)',
        'Moderate': 'మితమైన',
        'Active': 'చురుకైన',
        'Sports': 'క్రీడలు',
        'Football': 'ఫుట్‌బాల్',
        '3. AI Physical Readiness Prediction': '3. ఏఐ శారీరక సంసిద్ధత అంచనా',
        'Fitness Score': 'ఫిట్‌నెస్ స్కోరు',
        'Fitness Status': 'ఫిట్‌నెస్ స్థితి',
        'AI Physical Readiness Score:': 'ఏఐ శారీరక సంసిద్ధత స్కోరు:',
        'Prediction Confidence:': 'అంచనా ఖచ్చితత్వం:',
        'Algorithm:': 'అల్గారిథమ్:',
        'Key Strengths (Positive Indicators):': 'ప్రధాన బలాలు (సానుకూల సూచికలు):',
        'Priority Action Areas:': 'ప్రాధాన్యతా అభివృద్ధి రంగాలు:',
        'Good Fitness': 'మంచి ఫిట్‌నెస్ (Good Fitness)',
        'Excellent Readiness': 'అద్భుతమైన సంసిద్ధత (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "అధిక BPET పనితీరు: శారీరక సత్తువ పరీక్షలో 'అద్భుతమైన' గ్రేడింగ్ సాధించారు.",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "స్పష్టమైన వైద్య ప్రొఫైల్: వైద్యపరంగా షేప్-1, వ్యాయామాలపై ఎలాంటి పరిమితులు లేవు.",
        '4. Personalized Dietary & Macronutrient Plan': '4. వ్యక్తిగత ఆహారం మరియు పోషకాహార ప్రణాళిక',
        'Personalized Recommendations': 'వ్యక్తిగతీకరించిన సిఫార్సులు',
        'Diet Recommendations': 'ఆహార సిఫార్సులు',
        'Daily Energy Target:': 'రోజువారీ శక్తి లక్ష్యం:',
        'Daily Hydration Target:': 'రోజువారీ నీటి లక్ష్యం:',
        'Protein Target:': 'ప్రోటీన్ లక్ష్యం:',
        'Carbs / Fats:': 'కార్బోహైడ్రేట్లు / కొవ్వులు:',
        'Carbs:': 'కార్బోహైడ్రేట్లు:',
        'Fats:': 'కొవ్వులు:',
        'Diet Strategy:': 'ఆహార వ్యూహం:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "సైనిక సత్తువను కాపాడుకుంటూ కొవ్వును తగ్గించడానికి మితమైన కేలరీల లోటు (సుమారు 450 kcal).",
        '5. Physical Training': '5. శారీరక శిక్షణ',
        'Exercise Recommendations': 'వ్యాయామ సిఫార్సులు',
        'Exercise / Drill': 'వ్యాయామం / డ్రిల్',
        'Exercise Name': 'వ్యాయామం పేరు',
        'Sets': 'సెట్లు',
        'Reps / Volume': 'రిప్స్ / పరిమాణం',
        'Duration': 'వ్యవధి',
        'Frequency': 'ఫ్రీక్వెన్సీ',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'హై-టెంపో ఏరోబిక్ రన్ / క్రాస్-కంట్రీ (4 - 6 కి.మీ)',
        'Continuous steady state': 'నిరంతర స్థిరమైన వేగం',
        '35 - 40 mins': '35 - 40 నిమిషాలు',
        '4 days/week': 'వారానికి 4 రోజులు',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. అంచనా వేసిన పురోగతి మైలురాళ్లు (30 / 60 / 90 రోజులు)',
        'Progression Timeline': 'పురోగతి కాలక్రమం',
        'Timeline': 'సమయరేఖ',
        'Projected Weight': 'అంచనా బరువు',
        'Projected BMI': 'అంచనా బిఎమ్‌ఐ',
        'Estimated Physical Readiness Score': 'అంచనా శారీరక సంసిద్ధత స్కోరు',
        'Current Baseline': 'ప్రస్తుత బేస్‌లైన్ (Baseline)',
        '30 Days Projected': '30 రోజుల అంచనా',
        '60 Days Projected': '60 రోజుల అంచనా',
        '90 Days Projected': '90 రోజుల అంచనా',
        'UNIT MANAGEMENT SYSTEM': 'యూనిట్ నిర్వహణ వ్యవస్థ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'యూనిట్ నిర్వహణ వ్యవస్థ',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'యూనిట్ నిర్వహణ వ్యవస్థ',
        'UMS 15 CESR': 'యూనిట్ నిర్వహణ వ్యవస్థ',
        '8. Personalized Nutrition Recommendations': '8. వ్యక్తిగతీకరించిన పోషకాహార సిఫార్సులు',
        'Personalized Nutrition Recommendations': 'వ్యక్తిగతీకరించిన పోషకాహార సిఫార్సులు',
        "✔ DO'S (Recommended Protocol):": "✔ చేయవలసినవి (సిఫార్సు చేయబడిన ప్రోటోకాల్):",
        "✔ DO'S (Recommended Protocol)": "✔ చేయవలసినవి (సిఫార్సు చేయబడిన ప్రోటోకాల్)",
        "DO'S (Recommended Protocol):": "✔ చేయవలసినవి (సిఫార్సు చేయబడిన ప్రోటోకాల్):",
        "DO'S (Recommended Protocol)": "✔ చేయవలసినవి (సిఫార్సు చేయబడిన ప్రోటోకాల్)",
        "DO'S": "చేయవలసినవి",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ చేయకూడనివి (నివారించాల్సిన అంశాలు మరియు అలవాట్లు):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ చేయకూడనివి (నివారించాల్సిన అంశాలు మరియు అలవాట్లు):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ చేయకూడనివి (నివారించాల్సిన అంశాలు మరియు అలవాట్లు)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ చేయకూడనివి (నివారించాల్సిన అంశాలు మరియు అలవాట్లు)",
        "DON'TS (Items & Habits to Avoid):": "✖ చేయకూడనివి (నివారించాల్సిన అంశాలు మరియు అలవాట్లు):",
        "DONTS (Items & Habits to Avoid):": "✖ చేయకూడనివి (నివారించాల్సిన అంశాలు మరియు అలవాట్లు):",
        "DON'TS": "చేయకూడనివి",
        "DONTS": "చేయకూడనివి",
        'Operational Nutrition & Hydration Discipline:': 'కార్యాచరణ పోషకాహారం మరియు హైడ్రేషన్ క్రమశిక్షణ:',
        'Operational Nutrition & Hydration Discipline': 'కార్యాచరణ పోషకాహారం మరియు హైడ్రేషన్ క్రమశిక్షణ',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'కండరాల ప్రోటీన్ నిర్మాణం కోసం చికెన్, ఉడికించిన గుడ్లు మరియు పన్నీర్',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'నిరంతర అమైనో ఆమ్లాల కోసం సంపూర్ణ పప్పులు మరియు మొలకెత్తిన గింజలు',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'గ్లైకోజెన్ భర్తీ కోసం తృణధాన్యాలు (ఓట్స్, బ్రౌన్ రైస్, గోధుమ రొట్టె)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'ఎలక్ట్రోలైట్లు మరియు సూక్ష్మపోషకాల కోసం కాలానుగుణ తాజా పండ్లు మరియు ఆకుకూరలు',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'రోజూ కనీసం 3.0 నుండి 3.5 లీటర్ల స్వచ్ఛమైన నీరు త్రాగడం',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'నూనెలో వేయించిన చిరుతిళ్లు, పకోడీలు మరియు ప్రాసెస్ చేసిన క్యాంటీన్ పదార్థాలు',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'శుద్ధి చేసిన చక్కెర, తీపి టీ/కాఫీ మరియు కార్బోనేటేడ్ పానీయాలు',
        'Excessive table salt, pickles, and high-sodium processed rations': 'అధిక ఉప్పు, ఊరగాయలు మరియు ఎక్కువ సోడియం ఉన్న ఆహారాలు',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'సమయానికి ఆహారం తీసుకోకపోవడం లేదా ఉదయం పీటీకి ముందు అల్పాహారం మానేయడం',
        'Heavy meals consumed less than 2 hours before lights out': 'పడుకోవడానికి (లైట్స్ అవుట్) 2 గంటల కంటే తక్కువ సమయంలో భారీ ఆహారం తీసుకోవడం',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'క్రమమైన భోజన వేళలను పాటించండి; పడుకోవడానికి కనీసం 2 గంటల ముందు రాత్రి భోజనం పూర్తి చేయండి.',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'కండరాలు త్వరగా కోలుకోవడానికి ప్రోటీన్‌కు (పప్పు, మొలకలు, పన్నీర్, గుడ్లు, చికెన్) ప్రాధాన్యత ఇవ్వండి.',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'యూనిట్ క్యాంటీన్ నుండి వేయించిన చిరుతిళ్లు, తీపి పానీయాలు మరియు ప్రాసెస్ చేసిన స్వీట్లను నివారించండి.',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'ముఖ్యంగా బహిరంగ పీటీ సెషన్ల సమయంలో రోజూ కనీసం 3.5 నుండి 4.0 లీటర్ల నీరు త్రాగాలని నిర్ధారించుకోండి.',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'ముఖ్యమైన సూక్ష్మపోషకాలు మరియు ఎలక్ట్రోలైట్ల కోసం ఆకుకూరలు మరియు నిమ్మజాతి పండ్లను చేర్చండి.',
    },
    'kn': {

        'Personal Fitness Report': 'ವೈಯಕ್ತಿಕ ಫಿಟ್‌ನೆಸ್ ವರದಿ',
        'Personnal Fitness Report': 'ವೈಯಕ್ತಿಕ ಫಿಟ್‌ನೆಸ್ ವರದಿ',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'ವೈಯಕ್ತಿಕ ಫಿಟ್‌ನೆಸ್ ವರದಿ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 ಕಾರ್ಪ್ಸ್ / 15 ಸಿಇಎಸ್ಆರ್ — ಯುನಿಟ್ ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'AI/ML ವೈಯಕ್ತಿಕ ಫಿಟ್‌ನೆಸ್ ಮುನ್ಸೂಚನೆ ಮತ್ತು ವರದಿ',
        'Individual Fitness Report': 'ವೈಯಕ್ತಿಕ ಫಿಟ್‌ನೆಸ್ ವರದಿ',
        'Report Generated': 'ವರದಿ ದಿನಾಂಕ',
        'Model Version': 'ಮಾದರಿ ಆವೃತ್ತಿ',
        'CONFIDENTIAL': 'ಗೌಪ್ಯ',
        '1. Soldier Particulars & Service Profile': '1. ಸೈನಿಕರ ವಿವರಗಳು ಮತ್ತು ಸೇವಾ ವಿವರ',
        'Personnel Details': 'ಸೈನಿಕರ ವಿವರಗಳು',
        'Army Number:': 'ಸೇನಾ ಸಂಖ್ಯೆ:',
        'Full Name:': 'ಪೂರ್ಣ ಹೆಸರು:',
        'Rank / Trade:': 'ಹುದ್ದೆ / ವೃತ್ತಿ:',
        'Company / Section:': 'ಕಂಪನಿ / ವಿಭಾಗ:',
        'Age / Service:': 'ವಯಸ್ಸು / ಸೇವಾ ಅವಧಿ:',
        'Medical Status:': 'ವೈದ್ಯಕೀಯ ಸ್ಥಿತಿ:',
        'Years': 'ವರ್ಷಗಳು',
        'SHAPE-1 Cleared': 'ಶೇಪ್-1 ತೇರ್ಗಡೆ',
        'Restricted / LMC': 'ನಿರ್ಬಂಧಿತ / ಎಲ್ಎಂಸಿ',
        '2. Physiological Metrics & Physical Performance': '2. ಶಾರೀರಿಕ ಅಳತೆಗಳು ಮತ್ತು ಕಾರ್ಯಕ್ಷಮತೆ ವಿಶ್ಲೇಷಣೆ',
        'Fitness Assessment': 'ಫಿಟ್‌ನೆಸ್ ಮೌಲ್ಯಮಾಪನ',
        'Current Fitness Level': 'ಪ್ರಸ್ತುತ ಫಿಟ್‌ನೆಸ್ ಮಟ್ಟ',
        'Height / Actual Weight:': 'ಎತ್ತರ / ನೈಜ ತೂಕ:',
        'Ideal Reference Weight:': 'ಆದರ್ಶ ಪ್ರಮಾಣಿತ ತೂಕ:',
        'BMI Index & Category:': 'ಬಿಎಂಐ ಸೂಚ್ಯಂಕ ಮತ್ತು ವರ್ಗ:',
        'Weight Deviation:': 'ತೂಕದ ವ್ಯತ್ಯಾಸ:',
        'BPET Grading:': 'BPET ಶ್ರೇಣಿ:',
        'PPT Grading:': 'PPT ಶ್ರೇಣಿ:',
        'Sports & Athletics:': 'ಕ್ರೀಡೆ ಮತ್ತು ಅಥ್ಲೆಟಿಕ್ಸ್:',
        'Physical Activity Level:': 'ದೈಹಿಕ ಚಟುವಟಿಕೆ ಮಟ್ಟ:',
        'Normal (Ideal)': 'ಸಾಮಾನ್ಯ (ಆದರ್ಶ)',
        'Normal': 'ಸಾಮಾನ್ಯ',
        'Overweight': 'ಹೆಚ್ಚಿನ ತೂಕ',
        'Underweight': 'ಕಡಿಮೆ ತೂಕ',
        'EXCELLENT': 'ಅತ್ಯುತ್ತಮ (EXCELLENT)',
        'GOOD': 'ಉತ್ತಮ (GOOD)',
        'SATISFACTORY': 'ತೃಪ್ತಿಕರ (SATISFACTORY)',
        'Moderate': 'ಮಧ್ಯಮ',
        'Active': 'ಸಕ್ರಿಯ',
        'Sports': 'ಕ್ರೀಡೆ',
        'Football': 'ಫುಟ್ಬಾಲ್',
        '3. AI Physical Readiness Prediction': '3. AI ದೈಹಿಕ ಸನ್ನದ್ಧತೆ ಮುನ್ಸೂಚನೆ',
        'Fitness Score': 'ಫಿಟ್‌ನೆಸ್ ಅಂಕ',
        'Fitness Status': 'ಫಿಟ್‌ನೆಸ್ ಸ್ಥಿತಿ',
        'AI Physical Readiness Score:': 'AI ದೈಹಿಕ ಸನ್ನದ್ಧತೆ ಅಂಕ:',
        'Prediction Confidence:': 'ಮುನ್ಸೂಚನೆ ನಿಖರತೆ:',
        'Algorithm:': 'ಅಲ್ಗಾರಿದಮ್:',
        'Key Strengths (Positive Indicators):': 'ಪ್ರಮುಖ ಸಾಮರ್ಥ್ಯಗಳು (ಧನಾತ್ಮಕ ಸೂಚಕಗಳು):',
        'Priority Action Areas:': 'ಆದ್ಯತೆಯ ಸುಧಾರಣಾ ಕ್ಷೇತ್ರಗಳು:',
        'Good Fitness': 'ಉತ್ತಮ ಫಿಟ್‌ನೆಸ್ (Good Fitness)',
        'Excellent Readiness': 'ಅತ್ಯುತ್ತಮ ಸನ್ನದ್ಧತೆ (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "ಉನ್ನತ BPET ಕಾರ್ಯಕ್ಷಮತೆ: ದೈಹಿಕ ಸಹಿಷ್ಣುತಾ ಪರೀಕ್ಷೆಯಲ್ಲಿ 'ಅತ್ಯುತ್ತಮ' ಶ್ರೇಣಿ ಗಳಿಸಿದೆ.",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "ಸ್ಪಷ್ಟ ವೈದ್ಯಕೀಯ ವಿವರ: ವ್ಯಾಯಾಮ ನಿರ್ಬಂಧಗಳಿಲ್ಲದ ಶೇಪ್-1 ಸ್ಥಿತಿ.",
        '4. Personalized Dietary & Macronutrient Plan': '4. ವೈಯಕ್ತಿಕ ಆಹಾರ ಮತ್ತು ಪೋಷಕಾಂಶ ಯೋಜನೆ',
        'Personalized Recommendations': 'ವೈಯಕ್ತಿಕ ಶಿಫಾರಸುಗಳು',
        'Diet Recommendations': 'ಆಹಾರ ಶಿಫಾರಸುಗಳು',
        'Daily Energy Target:': 'ದೈನಂದಿನ ಶಕ್ತಿ ಗುರಿ:',
        'Daily Hydration Target:': 'ದೈನಂದಿನ ನೀರಿನ ಗುರಿ:',
        'Protein Target:': 'ಪ್ರೋಟೀನ್ ಗುರಿ:',
        'Carbs / Fats:': 'ಕಾರ್ಬೋಹೈಡ್ರೇಟ್ / ಕೊಬ್ಬು:',
        'Carbs:': 'ಕಾರ್ಬೋಹೈಡ್ರೇಟ್:',
        'Fats:': 'ಕೊಬ್ಬು:',
        'Diet Strategy:': 'ಆಹಾರ ತಂತ್ರ:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "ಸಹಿಷ್ಣುತೆ ಕಾಪಾಡಿಕೊಂಡು ಕೊಬ್ಬು ಕರಗಿಸಲು ಮಧ್ಯಮ ಕ್ಯಾಲೋರಿ ಕೊರತೆ (ಸುಮಾರು 450 kcal).",
        '5. Physical Training': '5. ದೈಹಿಕ ತರಬೇತಿ',
        'Exercise Recommendations': 'ವ್ಯಾಯಾಮ ಶಿಫಾರಸುಗಳು',
        'Exercise / Drill': 'ವ್ಯಾಯಾಮ / ಡ್ರಿಲ್',
        'Exercise Name': 'ವ್ಯಾಯಾಮದ ಹೆಸರು',
        'Sets': 'ಸೆಟ್‌ಗಳು',
        'Reps / Volume': 'ಪ್ರಮಾಣ / ಪುನರಾವರ್ತನೆ',
        'Duration': 'ಅವಧಿ',
        'Frequency': 'ಆವರ್ತನ',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'ವೇಗದ ಏರೋಬಿಕ್ ಓಟ / ಕ್ರಾಸ್-ಕಂಟ್ರಿ (4 - 6 ಕಿಮೀ)',
        'Continuous steady state': 'ನಿರಂತರ ಸ್ಥಿರ ವೇಗ',
        '35 - 40 mins': '35 - 40 ನಿಮಿಷಗಳು',
        '4 days/week': 'ವಾರಕ್ಕೆ 4 ದಿನಗಳು',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. ನಿರೀಕ್ಷಿತ ಪ್ರಗತಿಯ ಮೈಲಿಗಲ್ಲುಗಳು (30 / 60 / 90 ದಿನಗಳು)',
        'Progression Timeline': 'ಪ್ರಗತಿ ಕಾಲಾವಧಿ',
        'Timeline': 'ಸಮಯಾವಧಿ',
        'Projected Weight': 'ನಿರೀಕ್ಷಿತ ತೂಕ',
        'Projected BMI': 'ನಿರೀಕ್ಷಿತ ಬಿಎಂಐ',
        'Estimated Physical Readiness Score': 'ನಿರೀಕ್ಷಿತ ಫಿಟ್‌ನೆಸ್ ಅಂಕ',
        'Current Baseline': 'ಪ್ರಸ್ತುತ ಮೂಲ (Baseline)',
        '30 Days Projected': '30 ದಿನಗಳ ಮುನ್ನೋಟ',
        '60 Days Projected': '60 ದಿನಗಳ ಮುನ್ನೋಟ',
        '90 Days Projected': '90 ದಿನಗಳ ಮುನ್ನೋಟ',
        'UNIT MANAGEMENT SYSTEM': 'ಯುನಿಟ್ ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'ಯುನಿಟ್ ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'ಯುನಿಟ್ ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ',
        'UMS 15 CESR': 'ಯುನಿಟ್ ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ',
        '8. Personalized Nutrition Recommendations': '8. ವೈಯಕ್ತಿಕಗೊಳಿಸಿದ ಪೌಷ್ಟಿಕಾಂಶ ಶಿಫಾರಸುಗಳು',
        'Personalized Nutrition Recommendations': 'ವೈಯಕ್ತಿಕಗೊಳಿಸಿದ ಪೌಷ್ಟಿಕಾಂಶ ಶಿಫಾರಸುಗಳು',
        "✔ DO'S (Recommended Protocol):": "✔ ಮಾಡಬೇಕಾದದ್ದು (ಶಿಫಾರಸು ಮಾಡಲಾದ ನಿಯಮಗಳು):",
        "✔ DO'S (Recommended Protocol)": "✔ ಮಾಡಬೇಕಾದದ್ದು (ಶಿಫಾರಸು ಮಾಡಲಾದ ನಿಯಮಗಳು)",
        "DO'S (Recommended Protocol):": "✔ ಮಾಡಬೇಕಾದದ್ದು (ಶಿಫಾರಸು ಮಾಡಲಾದ ನಿಯಮಗಳು):",
        "DO'S (Recommended Protocol)": "✔ ಮಾಡಬೇಕಾದದ್ದು (ಶಿಫಾರಸು ಮಾಡಲಾದ ನಿಯಮಗಳು)",
        "DO'S": "ಮಾಡಬೇಕಾದದ್ದು",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ ಮಾಡಬಾರದವು (ತ್ಯಜಿಸಬೇಕಾದ ಅಭ್ಯಾಸಗಳು ಮತ್ತು ವಸ್ತುಗಳು):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ ಮಾಡಬಾರದವು (ತ್ಯಜಿಸಬೇಕಾದ ಅಭ್ಯಾಸಗಳು ಮತ್ತು ವಸ್ತುಗಳು):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ ಮಾಡಬಾರದವು (ತ್ಯಜಿಸಬೇಕಾದ ಅಭ್ಯಾಸಗಳು ಮತ್ತು ವಸ್ತುಗಳು)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ ಮಾಡಬಾರದವು (ತ್ಯಜಿಸಬೇಕಾದ ಅಭ್ಯಾಸಗಳು ಮತ್ತು ವಸ್ತುಗಳು)",
        "DON'TS (Items & Habits to Avoid):": "✖ ಮಾಡಬಾರದವು (ತ್ಯಜಿಸಬೇಕಾದ ಅಭ್ಯಾಸಗಳು ಮತ್ತು ವಸ್ತುಗಳು):",
        "DONTS (Items & Habits to Avoid):": "✖ ಮಾಡಬಾರದವು (ತ್ಯಜಿಸಬೇಕಾದ ಅಭ್ಯಾಸಗಳು ಮತ್ತು ವಸ್ತುಗಳು):",
        "DON'TS": "ಮಾಡಬಾರದವು",
        "DONTS": "ಮಾಡಬಾರದವು",
        'Operational Nutrition & Hydration Discipline:': 'ಕಾರ್ಯಾಚರಣೆಯ ಪೌಷ್ಟಿಕಾಂಶ ಮತ್ತು ಜಲಸಂಚಯನ ಶಿಸ್ತು:',
        'Operational Nutrition & Hydration Discipline': 'ಕಾರ್ಯಾಚರಣೆಯ ಪೌಷ್ಟಿಕಾಂಶ ಮತ್ತು ಜಲಸಂಚಯನ ಶಿಸ್ತು',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'ಸ್ನಾಯು ಪ್ರೋಟೀನ್ ನಿರ್ಮಾಣಕ್ಕಾಗಿ ಚಿಕನ್, ಬೇಯಿಸಿದ ಮೊಟ್ಟೆಗಳು ಮತ್ತು ಪನೀರ್',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'ನಿರಂತರ ಅಮೈನೋ ಆಮ್ಲಗಳಿಗಾಗಿ ಕಾಳುಗಳು, ಬೇಳೆ ಮತ್ತು ಮೊಳಕೆ ಕಾಳುಗಳು',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'ಗ್ಲೈಕೋಜೆನ್ ಮರುಪೂರಣಕ್ಕಾಗಿ ಧಾನ್ಯಗಳು (ಓಟ್ಸ್, ಬ್ರೌನ್ ರೈಸ್, ಗೋಧಿ ರೊಟ್ಟಿ)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'ಎಲೆಕ್ಟ್ರೋಲೈಟ್‌ಗಳು ಮತ್ತು ಪೋಷಕಾಂಶಗಳಿಗಾಗಿ ಕಾಲೋಚಿತ ತಾಜಾ ಹಣ್ಣುಗಳು ಮತ್ತು ಸೊಪ್ಪು ತರಕಾರಿಗಳು',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'ದಿನಕ್ಕೆ ಕನಿಷ್ಠ 3.0 ರಿಂದ 3.5 ಲೀಟರ್ ಶುದ್ಧ ನೀರನ್ನು ನಿಯಮಿತವಾಗಿ ಕುಡಿಯುವುದು',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'ಎಣ್ಣೆಯಲ್ಲಿ ಕರಿದ ತಿಂಡಿಗಳು, ಬಜ್ಜಿ-ಬೋಂಡಾ ಮತ್ತು ಸಂಸ್ಕರಿಸಿದ ಕ್ಯಾಂಟೀನ್ ತಿನಿಸುಗಳು',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'ಸಂಸ್ಕರಿಸಿದ ಸಕ್ಕರೆ, ಸಿಹಿ ಚಹಾ/ಕಾಫಿ ಮತ್ತು ತಂಪು ಪಾನೀಯಗಳು',
        'Excessive table salt, pickles, and high-sodium processed rations': 'ಹೆಚ್ಚುವರಿ ಉಪ್ಪು, ಉಪ್ಪಿನಕಾಯಿ ಮತ್ತು ಹೆಚ್ಚಿನ ಸೋಡಿಯಂ ಹೊಂದಿರುವ ಆಹಾರಗಳು',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'ಅನಿಯಮಿತ ಊಟದ ಸಮಯ ಅಥವಾ ಬೆಳಗಿನ ಪಿಟಿ ಮುನ್ನ ಉಪಹಾರವನ್ನು ಬಿಡುವುದು',
        'Heavy meals consumed less than 2 hours before lights out': 'ಮಲಗುವ (ಲೈಟ್ಸ್ ಔಟ್) 2 ಗಂಟೆಗಿಂತ ಕಡಿಮೆ ಸಮಯದಲ್ಲಿ ಭಾರೀ ಊಟ ಮಾಡುವುದು',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'ನಿಯಮಿತ ಊಟದ ಸಮಯವನ್ನು ಕಾಪಾಡಿಕೊಳ್ಳಿ; ಮಲಗುವ ಕನಿಷ್ಠ 2 ಗಂಟೆಗಳ ಮೊದಲು ರಾತ್ರಿಯ ಊಟವನ್ನು ಮುಗಿಸಿ.',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'ಸ್ನಾಯುಗಳ ತ್ವರಿತ ಚೇತರಿಕೆಗಾಗಿ ಪ್ರೋಟೀನ್‌ಗೆ (ಬೇಳೆ, ಮೊಳಕೆ ಕಾಳು, ಪನೀರ್, ಮೊಟ್ಟೆ, ಚಿಕನ್) ಆದ್ಯತೆ ನೀಡಿ.',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'ಯೂನಿಟ್ ಕ್ಯಾಂಟೀನ್‌ನ ಕರಿದ ತಿಂಡಿಗಳು, ಸಿಹಿ ಪಾನೀಯಗಳು ಮತ್ತು ಸಂಸ್ಕರಿಸಿದ ಸಿಹಿತಿಂಡಿಗಳನ್ನು ತಪ್ಪಿಸಿ.',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'ದಿನಕ್ಕೆ ಕನಿಷ್ಠ 3.5 ರಿಂದ 4.0 ಲೀಟರ್ ನೀರು ಕುಡಿಯುವುದನ್ನು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ, ವಿಶೇಷವಾಗಿ ಹೊರಾಂಗಣ ಪಿಟಿ ಸಮಯದಲ್ಲಿ.',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'ಪ್ರಮುಖ ಪೋಷಕಾಂಶಗಳು ಮತ್ತು ಎಲೆಕ್ಟ್ರೋಲೈಟ್‌ಗಳಿಗಾಗಿ ಹಸಿರು ಸೊಪ್ಪುಗಳು ಮತ್ತು ಸಿಟ್ರಸ್ ಹಣ್ಣುಗಳನ್ನು ಸೇರಿಸಿ.',
    },
    'ml': {

        'Personal Fitness Report': 'വ്യക്തിഗത ഫിറ്റ്നസ് റിപ്പോർട്ട്',
        'Personnal Fitness Report': 'വ്യക്തിഗത ഫിറ്റ്നസ് റിപ്പോർട്ട്',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'വ്യക്തിഗത ഫിറ്റ്നസ് റിപ്പോർട്ട്',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 കോർപ്സ് / 15 സിഇഎസ്ആർ — യൂണിറ്റ് മാനേജ്മെന്റ് സിസ്റ്റം',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'AI/ML വ്യക്തിഗത ഫിറ്റ്നസ് പ്രവചനവും റിപ്പോർട്ടും',
        'Individual Fitness Report': 'വ്യക്തിഗത ഫിറ്റ്നസ് റിപ്പോർട്ട്',
        'Report Generated': 'റിപ്പോർട്ട് തീയതി',
        'Model Version': 'മോഡൽ പതിപ്പ്',
        'CONFIDENTIAL': 'രഹസ്യാത്മകം',
        '1. Soldier Particulars & Service Profile': '1. സൈനികന്റെ വിവരങ്ങളും സേവന പ്രൊഫൈലും',
        'Personnel Details': 'സൈനികന്റെ വിവരങ്ങൾ',
        'Army Number:': 'ആർമി നമ്പർ:',
        'Full Name:': 'പൂർണ്ണ പേര്:',
        'Rank / Trade:': 'പദവി / ട്രേഡ്:',
        'Company / Section:': 'കമ്പനി / വിഭാഗം:',
        'Age / Service:': 'പ്രായം / സേവന കാലം:',
        'Medical Status:': 'മെഡിക്കൽ അവസ്ഥ:',
        'Years': 'വർഷങ്ങൾ',
        'SHAPE-1 Cleared': 'ഷേപ്പ്-1 പാസ്സായി',
        'Restricted / LMC': 'നിയന്ത്രിത / എൽഎംസി',
        '2. Physiological Metrics & Physical Performance': '2. ശാരീരിക അളവുകളും പ്രകടന വിശകലനവും',
        'Fitness Assessment': 'ഫിറ്റ്നസ് വിലയിരുത്തൽ',
        'Current Fitness Level': 'നിലവിലെ ഫിറ്റ്നസ് നില',
        'Height / Actual Weight:': 'ഉയരം / യഥാർത്ഥ ഭാരം:',
        'Ideal Reference Weight:': 'ആദർശപരമായ ഭാരം:',
        'BMI Index & Category:': 'ബിഎംഐ സൂചികയും വിഭാഗവും:',
        'Weight Deviation:': 'ഭാര വ്യത്യാസം:',
        'BPET Grading:': 'BPET ഗ്രേഡിംഗ്:',
        'PPT Grading:': 'PPT ഗ്രേഡിംഗ്:',
        'Sports & Athletics:': 'കായിക ഇനങ്ങളും അത്‌ലറ്റിക്സും:',
        'Physical Activity Level:': 'ശാരീരിക പ്രവർത്തന നില:',
        'Normal (Ideal)': 'സാധാരണ (ആദർശം)',
        'Normal': 'സാധാരണ',
        'Overweight': 'അമിതഭാരം',
        'Underweight': 'ഭാരക്കുറവ്',
        'EXCELLENT': 'മികച്ചത് (EXCELLENT)',
        'GOOD': 'നല്ലത് (GOOD)',
        'SATISFACTORY': 'തൃപ്തികരം (SATISFACTORY)',
        'Moderate': 'മിതമായ',
        'Active': 'സജീവമായ',
        'Sports': 'കായികം',
        'Football': 'ഫുട്ബോൾ',
        '3. AI Physical Readiness Prediction': '3. AI ശാരീരിക സന്നദ്ധത പ്രവചനം',
        'Fitness Score': 'ഫിറ്റ്നസ് സ്കോർ',
        'Fitness Status': 'ഫിറ്റ്നസ് അവസ്ഥ',
        'AI Physical Readiness Score:': 'AI ശാരീരിക സന്നദ്ധത സ്കോർ:',
        'Prediction Confidence:': 'പ്രവചന കൃത്യത:',
        'Algorithm:': 'അൽഗോരിതം:',
        'Key Strengths (Positive Indicators):': 'പ്രധാന നേട്ടങ്ങൾ (പോസിറ്റീവ് സൂചകങ്ങൾ):',
        'Priority Action Areas:': 'മെച്ചപ്പെടുത്തേണ്ട പ്രധാന മേഖലകൾ:',
        'Good Fitness': 'നല്ല ഫിറ്റ്നസ് (Good Fitness)',
        'Excellent Readiness': 'മികച്ച സന്നദ്ധത (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "ഉയർന്ന BPET പ്രകടനം: ശാരീരിക സഹിഷ്ണുതാ പരീക്ഷണത്തിൽ 'മികച്ച' ഗ്രേഡിംഗ് നേടി.",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "മെഡിക്കൽ തടസ്സങ്ങളില്ലാത്ത ഷേപ്പ്-1 നിലവാരം.",
        '4. Personalized Dietary & Macronutrient Plan': '4. വ്യക്തിഗത ഭക്ഷണ, പോഷകാഹാര പദ്ധതി',
        'Personalized Recommendations': 'വ്യക്തിഗത നിർദ്ദേശങ്ങൾ',
        'Diet Recommendations': 'ഭക്ഷണ നിർദ്ദേശങ്ങൾ',
        'Daily Energy Target:': 'പ്രതിദിന ഊർജ്ജ ലക്ഷ്യം:',
        'Daily Hydration Target:': 'പ്രതിദിന ജല ലക്ഷ്യം:',
        'Protein Target:': 'പ്രോട്ടീൻ ലക്ഷ്യം:',
        'Carbs / Fats:': 'കാർബോഹൈഡ്രേറ്റ് / കൊഴുപ്പ്:',
        'Carbs:': 'കാർബോഹൈഡ്രേറ്റ്:',
        'Fats:': 'കൊഴുപ്പ്:',
        'Diet Strategy:': 'ഭക്ഷണ തന്ത്രം:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "സ്റ്റാമിന നിലനിർത്തിക്കൊണ്ട് കൊഴുപ്പ് കുറയ്ക്കാൻ മിതമായ കലോറി കുറവ് (ഏകദേശം 450 kcal).",
        '5. Physical Training': '5. കായിക പരിശീലനം',
        'Exercise Recommendations': 'വ്യായാമ നിർദ്ദേശങ്ങൾ',
        'Exercise / Drill': 'വ്യായാമം / ഡ്രിൽ',
        'Exercise Name': 'വ്യായാമത്തിന്റെ പേര്',
        'Sets': 'സെറ്റുകൾ',
        'Reps / Volume': 'എണ്ണം / അളവ്',
        'Duration': 'ദൈർഘ്യം',
        'Frequency': 'ആവൃത്തി',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'ഹൈ-ടെമ്പോ എയറോബിക് ഓട്ടം / ക്രോസ്-കൺട്രി (4 - 6 കി.മീ)',
        'Continuous steady state': 'തുടർച്ചയായ സ്ഥിര വേഗത',
        '35 - 40 mins': '35 - 40 മിനിറ്റ്',
        '4 days/week': 'ആഴ്ചയിൽ 4 ദിവസം',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. പ്രതീക്ഷിക്കുന്ന പുരോഗതിയുടെ നാഴികക്കല്ലുകൾ (30 / 60 / 90 ദിവസങ്ങൾ)',
        'Progression Timeline': 'പുരോഗതി സമയക്രമം',
        'Timeline': 'സമയക്രമം',
        'Projected Weight': 'പ്രതീക്ഷിക്കുന്ന ഭാരം',
        'Projected BMI': 'പ്രതീക്ഷിക്കുന്ന ബിഎംഐ',
        'Estimated Physical Readiness Score': 'പ്രതീക്ഷിക്കുന്ന ഫിറ്റ്നസ് സ്കോർ',
        'Current Baseline': 'നിലവിലെ അടിസ്ഥാനം (Baseline)',
        '30 Days Projected': '30 ദിവസത്തെ പ്രവചനം',
        '60 Days Projected': '60 ദിവസത്തെ പ്രവചനം',
        '90 Days Projected': '90 ദിവസത്തെ പ്രവചനം',
        'UNIT MANAGEMENT SYSTEM': 'യൂണിറ്റ് മാനേജ്മെന്റ് സിസ്റ്റം',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'യൂണിറ്റ് മാനേജ്മെന്റ് സിസ്റ്റം',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'യൂണിറ്റ് മാനേജ്മെന്റ് സിസ്റ്റം',
        'UMS 15 CESR': 'യൂണിറ്റ് മാനേജ്മെന്റ് സിസ്റ്റം',
        '8. Personalized Nutrition Recommendations': '8. വ്യക്തിഗത പോഷകാഹാര ശുപാർശകൾ',
        'Personalized Nutrition Recommendations': 'വ്യക്തിഗത പോഷകാഹാര ശുപാർശകൾ',
        "✔ DO'S (Recommended Protocol):": "✔ ചെയ്യേണ്ടവ (ശുപാർശ ചെയ്യുന്ന പ്രോട്ടോക്കോൾ):",
        "✔ DO'S (Recommended Protocol)": "✔ ചെയ്യേണ്ടവ (ശുപാർശ ചെയ്യുന്ന പ്രോട്ടോക്കോൾ)",
        "DO'S (Recommended Protocol):": "✔ ചെയ്യേണ്ടവ (ശുപാർശ ചെയ്യുന്ന പ്രോട്ടോക്കോൾ):",
        "DO'S (Recommended Protocol)": "✔ ചെയ്യേണ്ടവ (ശുപാർശ ചെയ്യുന്ന പ്രോട്ടോക്കോൾ)",
        "DO'S": "ചെയ്യേണ്ടവ",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ ഒഴിവാക്കേണ്ടവ (ഒഴിവാക്കേണ്ട ശീലങ്ങളും ഇനങ്ങളും):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ ഒഴിവാക്കേണ്ടവ (ഒഴിവാക്കേണ്ട ശീലങ്ങളും ഇനങ്ങളും):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ ഒഴിവാക്കേണ്ടവ (ഒഴിവാക്കേണ്ട ശീലങ്ങളും ഇനങ്ങളും)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ ഒഴിവാക്കേണ്ടവ (ഒഴിവാക്കേണ്ട ശീലങ്ങളും ഇനങ്ങളും)",
        "DON'TS (Items & Habits to Avoid):": "✖ ഒഴിവാക്കേണ്ടവ (ഒഴിവാക്കേണ്ട ശീലങ്ങളും ഇനങ്ങളും):",
        "DONTS (Items & Habits to Avoid):": "✖ ഒഴിവാക്കേണ്ടവ (ഒഴിവാക്കേണ്ട ശീലങ്ങളും ഇനങ്ങളും):",
        "DON'TS": "ഒഴിവാക്കേണ്ടവ",
        "DONTS": "ഒഴിവാക്കേണ്ടവ",
        'Operational Nutrition & Hydration Discipline:': 'പ്രവർത്തനപരമായ പോഷകാഹാരവും ജലാംശ ക്രമീകരണവും:',
        'Operational Nutrition & Hydration Discipline': 'പ്രവർത്തനപരമായ പോഷകാഹാരവും ജലാംശ ക്രമീകരണവും',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'പേശി പ്രോട്ടീൻ നിർമ്മാണത്തിനായി ചിക്കൻ, പുഴുങ്ങിയ മുട്ട, പനീർ',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'സ്ഥിരമായ അമിനോ ആസിഡുകൾക്കായി പയറുവർഗ്ഗങ്ങളും മുളപ്പിച്ച ധാന്യങ്ങളും',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'ഗ്ലൈക്കോജൻ വീണ്ടെടുക്കുന്നതിന് ധാന്യങ്ങൾ (ഓട്സ്, തവിട് അരി, ഗോതമ്പ് റൊട്ടി)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'ഇലക്ട്രോലൈറ്റുകൾക്കും പോഷകങ്ങൾക്കുമായി സീസണൽ പഴങ്ങളും ഇലക്കറികളും',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'പ്രതിദിനം കുറഞ്ഞത് 3.0 മുതൽ 3.5 ലിറ്റർ വരെ ശുദ്ധജലം കുടിക്കുക',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'എണ്ണയിൽ വറുത്ത പലഹാരങ്ങൾ, പക്കോഡകൾ, പ്രോസസ്സ് ചെയ്ത ലഘുഭക്ഷണങ്ങൾ',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'ശുദ്ധീകരിച്ച പഞ്ചസാര, മധുരമുള്ള ചായ/കോഫി, കാർബണേറ്റഡ് പാനീയങ്ങൾ',
        'Excessive table salt, pickles, and high-sodium processed rations': 'അമിതമായ ഉപ്പ്, അച്ചാറുകൾ, ഉയർന്ന സോഡിയം അടങ്ങിയ ഭക്ഷണങ്ങൾ',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'ഭക്ഷണക്രമത്തിലെ ക്രമക്കേടുകൾ അല്ലെങ്കിൽ പ്രഭാത പിടിക്ക് മുമ്പ് പ്രഭാതഭക്ഷണം ഒഴിവാക്കുന്നത്',
        'Heavy meals consumed less than 2 hours before lights out': 'ഉറങ്ങുന്നതിന് (ലൈറ്റ്സ് ഔട്ട്) 2 മണിക്കൂറിൽ താഴെ സമയത്തിനുള്ളിൽ കനത്ത ഭക്ഷണം കഴിക്കുന്നത്',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'കൃത്യമായ ഭക്ഷണ സമയം പാലിക്കുക; ഉറങ്ങുന്നതിന് കുറഞ്ഞത് 2 മണിക്കൂർ മുമ്പെങ്കിലും അത്താഴം കഴിക്കുക.',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'പേശികളുടെ വേഗത്തിലുള്ള വീണ്ടെടുക്കലിനായി പ്രോട്ടീന് (പരിപ്പ്, മുളപ്പിച്ചവ, പനീർ, മുട്ട, ചിക്കൻ) മുൻഗണന നൽകുക.',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'യൂണിറ്റ് കാന്റീനിൽ നിന്നുള്ള എണ്ണയിൽ വറുത്ത പലഹാരങ്ങൾ, മധുരപാനീയങ്ങൾ എന്നിവ ഒഴിവാക്കുക.',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'പ്രത്യേകിച്ച് ഔട്ട്ഡോർ പിടി സെഷനുകളിൽ ദിവസേന 3.5 മുതൽ 4.0 ലിറ്റർ വരെ വെള്ളം കുടിക്കുന്നുവെന്ന് ഉറപ്പാക്കുക.',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'പ്രധാന പോഷകങ്ങൾക്കും ഇലക്ട്രോലൈറ്റുകൾക്കുമായി പച്ചക്കറികളും സിട്രസ് പഴങ്ങളും ഉൾപ്പെടുത്തുക.',
    },
    'or': {

        'Personal Fitness Report': 'ବ୍ୟକ୍ତିଗତ ଫିଟନେସ ରିପୋର୍ଟ',
        'Personnal Fitness Report': 'ବ୍ୟକ୍ତିଗତ ଫିଟନେସ ରିପୋର୍ଟ',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'ବ୍ୟକ୍ତିଗତ ଫିଟନେସ ରିପୋର୍ଟ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '15 କର୍ପ୍ସ / 15 ସିଇଏସଆର — ୟୁନିଟ ପରିଚାଳନା ପ୍ରଣାଳୀ',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'AI/ML ବ୍ୟକ୍ତିଗତ ଫିଟନେସ ପୂର୍ବାନୁମାନ ଏବଂ ରିପୋର୍ଟ',
        'Individual Fitness Report': 'ବ୍ୟକ୍ତିଗତ ଫିଟନେସ ରିପୋର୍ଟ',
        'Report Generated': 'ରିପୋର୍ଟ ତାରିଖ',
        'Model Version': 'ମଡେଲ ସଂସ୍କରଣ',
        'CONFIDENTIAL': 'ଗୋପନୀୟ',
        '1. Soldier Particulars & Service Profile': '1. ସୈନିକଙ୍କ ବିବରଣୀ ଏବଂ ସେବା ପ୍ରୋଫାଇଲ',
        'Personnel Details': 'ସୈନିକ ବିବରଣୀ',
        'Army Number:': 'ଆର୍ମି ନମ୍ବର:',
        'Full Name:': 'ପୂରା ନାମ:',
        'Rank / Trade:': 'ପଦବୀ / ଟ୍ରେଡ୍:',
        'Company / Section:': 'କମ୍ପାନୀ / ବିଭାଗ:',
        'Age / Service:': 'ବୟସ / ସେବା ବର୍ଷ:',
        'Medical Status:': 'ଡାକ୍ତରୀ ସ୍ଥିତି:',
        'Years': 'ବର୍ଷ',
        'SHAPE-1 Cleared': 'ଶେପ-1 ପାସ',
        'Restricted / LMC': 'ପ୍ରତିବନ୍ଧିତ / LMC',
        '2. Physiological Metrics & Physical Performance': '2. ଶାରୀରିକ ମାପଦଣ୍ଡ ଏବଂ କାର୍ଯ୍ୟଦକ୍ଷତା ବିଶ୍ଳେଷଣ',
        'Fitness Assessment': 'ଫିଟନେସ ମୂଲ୍ୟାଙ୍କନ',
        'Current Fitness Level': 'ବର୍ତ୍ତମାନର ଫିଟନେସ ସ୍ତର',
        'Height / Actual Weight:': 'ଉଚ୍ଚତା / ପ୍ରକୃତ ଓଜନ:',
        'Ideal Reference Weight:': 'ଆଦର୍ଶ ମାନକ ଓଜନ:',
        'BMI Index & Category:': 'BMI ସୂଚକାଙ୍କ ଏବଂ ଶ୍ରେଣୀ:',
        'Weight Deviation:': 'ଓଜନ ପାର୍ଥକ୍ୟ:',
        'BPET Grading:': 'BPET ଗ୍ରେଡିଂ:',
        'PPT Grading:': 'PPT ଗ୍ରେଡିଂ:',
        'Sports & Athletics:': 'ଖେଳକୁଦ ଏବଂ ଆଥଲେଟିକ୍ସ:',
        'Physical Activity Level:': 'ଶାରୀରିକ କାର୍ଯ୍ୟକଳାପ ସ୍ତର:',
        'Normal (Ideal)': 'ସାଧାରଣ (ଆଦର୍ଶ)',
        'Normal': 'ସାଧାରଣ',
        'Overweight': 'ଅଧିକ ଓଜନ',
        'Underweight': 'କମ ଓଜନ',
        'EXCELLENT': 'ଉତ୍କୃଷ୍ଟ (EXCELLENT)',
        'GOOD': 'ଭଲ (GOOD)',
        'SATISFACTORY': 'ସନ୍ତୋଷଜନକ (SATISFACTORY)',
        'Moderate': 'ମଧ୍ୟମ',
        'Active': 'ସକ୍ରିୟ',
        'Sports': 'ଖେଳ',
        'Football': 'ଫୁଟବଲ',
        '3. AI Physical Readiness Prediction': '3. AI ଶାରୀରିକ ପ୍ରସ୍ତୁତି ପୂର୍ବାନୁମାନ',
        'Fitness Score': 'ଫିଟନେସ ସ୍କୋର',
        'Fitness Status': 'ଫିଟନେସ ସ୍ଥିତି',
        'AI Physical Readiness Score:': 'AI ଶାରୀରିକ ପ୍ରସ୍ତୁତି ସ୍କୋର:',
        'Prediction Confidence:': 'ପୂର୍ବାନୁମାନ ସଠିକତା:',
        'Algorithm:': 'ଆଲଗୋରିଦମ:',
        'Key Strengths (Positive Indicators):': 'ମୁଖ୍ୟ ଶକ୍ତି (ସକାରାତ୍ମକ ସୂଚକ):',
        'Priority Action Areas:': 'ପ୍ରାଥମିକତା ଉନ୍ନତି କ୍ଷେତ୍ର:',
        'Good Fitness': 'ଭଲ ଫିଟନେସ (Good Fitness)',
        'Excellent Readiness': 'ଉତ୍କୃଷ୍ଟ ପ୍ରସ୍ତୁତି (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "ଉଚ୍ଚ BPET କାର୍ଯ୍ୟଦକ୍ଷତା: ଶାରୀରିକ ସହନଶୀଳତା ପରୀକ୍ଷାରେ 'ଉତ୍କୃଷ୍ଟ' ଗ୍ରେଡିଂ ହାସଲ |",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "ସ୍ୱଚ୍ଛ ମେଡିକାଲ ପ୍ରୋଫାଇଲ: ବ୍ୟାୟାମ ଉପରେ କୌଣସି ପ୍ରତିବନ୍ଧକ ନାହିଁ |",
        '4. Personalized Dietary & Macronutrient Plan': '4. ବ୍ୟକ୍ତିଗତ ଖାଦ୍ୟ ଏବଂ ପୋଷଣ ଯୋଜନା',
        'Personalized Recommendations': 'ବ୍ୟକ୍ତିଗତ ସୁପାରିଶ',
        'Diet Recommendations': 'ଖାଦ୍ୟ ସୁପାରିଶ',
        'Daily Energy Target:': 'ଦୈନିକ ଶକ୍ତି ଲକ୍ଷ୍ୟ:',
        'Daily Hydration Target:': 'ଦୈନିକ ଜଳ ଲକ୍ଷ୍ୟ:',
        'Protein Target:': 'ପ୍ରୋଟିନ ଲକ୍ଷ୍ୟ:',
        'Carbs / Fats:': 'କାର୍ବୋହାଇଡ୍ରେଟ / ଚର୍ବି:',
        'Carbs:': 'କାର୍ବୋହାଇଡ୍ରେଟ:',
        'Fats:': 'ଚର୍ବି:',
        'Diet Strategy:': 'ଖାଦ୍ୟ ରଣନୀତି:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "ସହନଶୀଳତା ବଜାୟ ରଖି ଚର୍ବି ହ୍ରାସ କରିବା ପାଇଁ ମଧ୍ୟମ କ୍ୟାଲୋରୀ ହ୍ରାସ (ପ୍ରାୟ 450 kcal) |",
        '5. Physical Training': '5. ଶାରୀରିକ ତାଲିମ',
        'Exercise Recommendations': 'ବ୍ୟାୟାମ ସୁପାରିଶ',
        'Exercise / Drill': 'ବ୍ୟାୟାମ / ଡ୍ରିଲ',
        'Exercise Name': 'ବ୍ୟାୟାମର ନାମ',
        'Sets': 'ସେଟ୍',
        'Reps / Volume': 'ପରିମାଣ',
        'Duration': 'ସମୟାବଧି',
        'Frequency': 'ଆବୃତ୍ତି',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'ଦ୍ରୁତ ଏରୋବିକ ଦୌଡ଼ / କ୍ରସ-କଣ୍ଟ୍ରି (4 - 6 କିମି)',
        'Continuous steady state': 'ନିରନ୍ତର ସ୍ଥିର ଗତି',
        '35 - 40 mins': '35 - 40 ମିନିଟ୍',
        '4 days/week': 'ସପ୍ତାହରେ 4 ଦିନ',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '6. ପ୍ରତ୍ୟାଶିତ ପ୍ରଗତିର ମାଇଲଖୁଣ୍ଟ (30 / 60 / 90 ଦିନ)',
        'Progression Timeline': 'ପ୍ରଗତି ସମୟରେଖା',
        'Timeline': 'ସମୟରେଖା',
        'Projected Weight': 'ପ୍ରତ୍ୟାଶିତ ଓଜନ',
        'Projected BMI': 'ପ୍ରତ୍ୟାଶିତ BMI',
        'Estimated Physical Readiness Score': 'ପ୍ରତ୍ୟାଶିତ ଫିଟନେସ ସ୍କୋର',
        'Current Baseline': 'ବର୍ତ୍ତମାନର ଆଧାର (Baseline)',
        '30 Days Projected': '30 ଦିନର ପୂର୍ବାନୁମାନ',
        '60 Days Projected': '60 ଦିନର ପୂର୍ବାନୁମାନ',
        '90 Days Projected': '90 ଦିନର ପୂର୍ବାନୁମାନ',
        'UNIT MANAGEMENT SYSTEM': 'ୟୁନିଟ ପରିଚାଳନା ପ୍ରଣାଳୀ',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'ୟୁନିଟ ପରିଚାଳନା ପ୍ରଣାଳୀ',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'ୟୁନିଟ ପରିଚାଳନା ପ୍ରଣାଳୀ',
        'UMS 15 CESR': 'ୟୁନିଟ ପରିଚାଳନା ପ୍ରଣାଳୀ',
        '8. Personalized Nutrition Recommendations': '୮. ବ୍ୟକ୍ତିଗତ ପୁଷ୍ଟିକର ସୁପାରିଶ',
        'Personalized Nutrition Recommendations': 'ବ୍ୟକ୍ତିଗତ ପୁଷ୍ଟିକର ସୁପାରିଶ',
        "✔ DO'S (Recommended Protocol):": "✔ କରଣୀୟ (ସୁପାରିଶ କରାଯାଇଥିବା ନିୟମ):",
        "✔ DO'S (Recommended Protocol)": "✔ କରଣୀୟ (ସୁପାରିଶ କରାଯାଇଥିବା ନିୟମ)",
        "DO'S (Recommended Protocol):": "✔ କରଣୀୟ (ସୁପାରିଶ କରାଯାଇଥିବା ନିୟମ):",
        "DO'S (Recommended Protocol)": "✔ କରଣୀୟ (ସୁପାରିଶ କରାଯାଇଥିବା ନିୟମ)",
        "DO'S": "କରଣୀୟ",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ ବର୍ଜନୀୟ (ଦୂରେଇ ରହିବାକୁ ଥିବା ଅଭ୍ୟାସ ଏବଂ ଜିନିଷ):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ ବର୍ଜନୀୟ (ଦୂରେଇ ରହିବାକୁ ଥିବା ଅଭ୍ୟାସ ଏବଂ ଜିନିଷ):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ ବର୍ଜନୀୟ (ଦୂରେଇ ରହିବାକୁ ଥିବା ଅଭ୍ୟାସ ଏବଂ ଜିନିଷ)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ ବର୍ଜନୀୟ (ଦୂରେଇ ରହିବାକୁ ଥିବା ଅଭ୍ୟାସ ଏବଂ ଜିନିଷ)",
        "DON'TS (Items & Habits to Avoid):": "✖ ବର୍ଜନୀୟ (ଦୂରେଇ ରହିବାକୁ ଥିବା ଅଭ୍ୟାସ ଏବଂ ଜିନିଷ):",
        "DONTS (Items & Habits to Avoid):": "✖ ବର୍ଜନୀୟ (ଦୂରେଇ ରହିବାକୁ ଥିବା ଅଭ୍ୟାସ ଏବଂ ଜିନିଷ):",
        "DON'TS": "ବର୍ଜନୀୟ",
        "DONTS": "ବର୍ଜନୀୟ",
        'Operational Nutrition & Hydration Discipline:': 'ଅପରେସନାଲ ପୋଷଣ ଏବଂ ହାଇଡ୍ରେସନ ଅନୁଶାସନ:',
        'Operational Nutrition & Hydration Discipline': 'ଅପରେସନାଲ ପୋଷଣ ଏବଂ ହାଇଡ୍ରେସନ ଅନୁଶାସନ',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'ମାଂସପେଶୀ ପ୍ରୋଟିନ ଗଠନ ପାଇଁ ଚିକେନ, ସିଝା ଅଣ୍ଡା ଏବଂ ପନିର',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'ନିରନ୍ତର ଆମିନୋ ଏସିଡ୍ ପାଇଁ ଗୋଟା ଡାଲି ଏବଂ ଗଜା ମୁଗ',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'ଗ୍ଲାଇକୋଜେନ ପୂରଣ ପାଇଁ ଶସ୍ୟ (ଓଟସ୍, ବ୍ରାଉନ ରାଇସ, ଗହମ ରୁଟି)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'ଇଲେକ୍ଟ୍ରୋଲାଇଟସ୍ ଏବଂ ପୋଷକ ତତ୍ତ୍ୱ ପାଇଁ ଋତୁକାଳୀନ ତାଜା ଫଳ ଏବଂ ଶାଗ',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'ଦୈନିକ ଅତି କମରେ ୩.୦ ରୁ ୩.୫ ଲିଟର ବିଶୁଦ୍ଧ ପାଣି ପିଇବା',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'ଛଣା ହୋଇଥିବା ଖାଦ୍ୟ, ପକୋଡି ଏବଂ ପ୍ରୋସେସଡ୍ କ୍ୟାଣ୍ଟିନ ଖାଦ୍ୟ',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'ରିଫାଇଣ୍ଡ ଚିନି, ମିଠା ଚାହା/କଫି ଏବଂ କୋଲ୍ଡ ଡ୍ରିଙ୍କସ୍',
        'Excessive table salt, pickles, and high-sodium processed rations': 'ଅତ୍ୟଧିକ ଲୁଣ, ଆଚାର ଏବଂ ଅଧିକ ସୋଡିୟମ ଥିବା ଖାଦ୍ୟ',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'ଅନିୟମିତ ଖାଦ୍ୟ ସମୟ କିମ୍ବା ସକାଳ ପିଟି ପୂର୍ବରୁ ଜଳଖିଆ ଛାଡିବା',
        'Heavy meals consumed less than 2 hours before lights out': 'ଶୋଇବା (ଲାଇଟସ୍ ଆଉଟ୍) ର ୨ ଘଣ୍ଟା ମଧ୍ୟରେ ଭାରୀ ଖାଦ୍ୟ ଖାଇବା',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'ଖାଦ୍ୟର ନିୟମିତ ସମୟ ବଜାୟ ରଖନ୍ତୁ; ଶୋଇବାର ଅତି କମରେ ୨ ଘଣ୍ଟା ପୂର୍ବରୁ ରାତ୍ରୀ ଭୋଜନ ଶେଷ କରନ୍ତୁ |',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'ମାଂସପେଶୀର ଶୀଘ୍ର ପୁନରୁଦ୍ଧାର ପାଇଁ ପ୍ରୋଟିନକୁ (ଡାଲି, ଗଜା ମୁଗ, ପନିର, ଅଣ୍ଡା, ଚିକେନ) ପ୍ରାଥମିକତା ଦିଅନ୍ତୁ |',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'ୟୁନିଟ୍ କ୍ୟାଣ୍ଟିନରୁ ଛଣା ଜଳଖିଆ, ମିଠା ପାନୀୟ ଏବଂ ପ୍ରୋସେସଡ୍ ମିଠା ଖାଇବା ବନ୍ଦ କରନ୍ତୁ |',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'ଦୈନିକ ଅତି କମରେ ୩.୫ ରୁ ୪.୦ ଲିଟର ପାଣି ପିଇବା ନିଶ୍ଚିତ କରନ୍ତୁ, ବିଶେଷ କରି ବାହାର ପିଟି ସମୟରେ |',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'ମହତ୍ତ୍ୱପୂର୍ଣ୍ଣ ପୋଷକ ତତ୍ତ୍ୱ ଏବଂ ଇଲେକ୍ଟ୍ରୋଲାଇଟ୍ସ ପାଇଁ ଶାଗ ଏବଂ ଖଟା ଜାତୀୟ ଫଳ ସାମିଲ କରନ୍ତୁ |',
    },
    'as': {

        'Personal Fitness Report': 'ব্যক্তিগত ফিটনেছ প্ৰতিবেদন',
        'Personnal Fitness Report': 'ব্যক্তিগত ফিটনেছ প্ৰতিবেদন',
        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': 'ব্যক্তিগত ফিটনেছ প্ৰতিবেদন',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': '১৫ কৰ্পছ / ১৫ চিইএছআৰ — ইউনিট ব্যৱস্থাপনা প্ৰণালী',
        'AI/ML INDIVIDUAL FITNESS PREDICTION & PERSONALIZED FITNESS REPORT': 'AI/ML ব্যক্তিগত ফিটনেছ পূৰ্বানুমান আৰু প্ৰতিবেদন',
        'Individual Fitness Report': 'ব্যক্তিগত ফিটনেছ প্ৰতিবেদন',
        'Report Generated': 'প্ৰতিবেদনৰ তাৰিখ',
        'Model Version': 'মডেল সংস্কৰণ',
        'CONFIDENTIAL': 'গোপনীয়',
        '1. Soldier Particulars & Service Profile': '১. সৈনিকৰ বিৱৰণ আৰু সেৱা প্ৰফাইল',
        'Personnel Details': 'সৈনিকৰ বিৱৰণ',
        'Army Number:': 'আৰ্মি নম্বৰ:',
        'Full Name:': 'সম্পূৰ্ণ নাম:',
        'Rank / Trade:': 'পদবী / ট্ৰেড:',
        'Company / Section:': 'কোম্পানী / বিভাগ:',
        'Age / Service:': 'বয়স / সেৱা কাল:',
        'Medical Status:': 'চিকিৎসা স্থিতি:',
        'Years': 'বছৰ',
        'SHAPE-1 Cleared': 'শ্বেপ-১ উত্তীৰ্ণ',
        'Restricted / LMC': 'সীমিত / এলএমচি',
        '2. Physiological Metrics & Physical Performance': '২. শাৰীৰিক পৰিমাপ আৰু প্ৰদৰ্শন বিশ্লেষণ',
        'Fitness Assessment': 'ফিটনেছ মূল্যায়ন',
        'Current Fitness Level': 'বৰ্তমানৰ ফিটনেছ স্তৰ',
        'Height / Actual Weight:': 'উচ্চতা / প্ৰকৃত ওজন:',
        'Ideal Reference Weight:': 'আদৰ্শ মান ওজন:',
        'BMI Index & Category:': 'বিএমআই সূচক আৰু শ্ৰেণী:',
        'Weight Deviation:': 'ওজনৰ পাৰ্থক্য:',
        'BPET Grading:': 'BPET গ্ৰেডিং:',
        'PPT Grading:': 'PPT গ্ৰেডিং:',
        'Sports & Athletics:': 'ক্ৰীড়া আৰু এথলেটিকছ:',
        'Physical Activity Level:': 'শাৰীৰিক কাৰ্যকলাপৰ স্তৰ:',
        'Normal (Ideal)': 'স্বাভাৱিক (আদৰ্শ)',
        'Normal': 'স্বাভাৱিক',
        'Overweight': 'অধিক ওজন',
        'Underweight': 'কম ওজন',
        'EXCELLENT': 'উত্কৃষ্ট (EXCELLENT)',
        'GOOD': 'ভাল (GOOD)',
        'SATISFACTORY': 'সন্তোষজনক (SATISFACTORY)',
        'Moderate': 'মধ্যমীয়া',
        'Active': 'সক্ৰিয়',
        'Sports': 'ক্ৰীড়া',
        'Football': 'ফুটবল',
        '3. AI Physical Readiness Prediction': '৩. AI শাৰীৰিক প্ৰস্তুতি পূৰ্বানুমান',
        'Fitness Score': 'ফিটনেছ স্কোৰ',
        'Fitness Status': 'ফিটনেছ স্থিতি',
        'AI Physical Readiness Score:': 'AI শাৰীৰিক প্ৰস্তুতি স্কোৰ:',
        'Prediction Confidence:': 'পূৰ্বানুমানৰ শুদ্ধতা:',
        'Algorithm:': 'এলগৰিদম:',
        'Key Strengths (Positive Indicators):': 'মুখ্য শক্তি (ইতিবাচক সূচক):',
        'Priority Action Areas:': 'প্ৰাথমিকতাৰ ক্ষেত্ৰ:',
        'Good Fitness': 'ভাল ফিটনেছ (Good Fitness)',
        'Excellent Readiness': 'উত্কৃষ্ট প্ৰস্তুতি (Excellent Readiness)',
        "High BPET Performance: Achieved 'Excellent' grading in physical endurance and obstacle test.": "উচ্চ BPET প্ৰদৰ্শন: শাৰীৰিক সহনশীলতা পৰীক্ষাত 'উত্কৃষ্ট' গ্ৰেডিং লাভ।",
        "Clean Medical Profile: Medically SHAPE-1 with zero exercise contraindications.": "চিকিৎসাৰ দিশৰ পৰা শ্বেপ-১, কোনো ব্যায়ামৰ বাধা নাই।",
        '4. Personalized Dietary & Macronutrient Plan': '৪. ব্যক্তিগত খাদ্য আৰু পুষ্টি পৰিকল্পনা',
        'Personalized Recommendations': 'ব্যক্তিগত পৰামৰ্শ',
        'Diet Recommendations': 'খাদ্য পৰামৰ্শ',
        'Daily Energy Target:': 'দৈনিক শক্তিৰ লক্ষ্য:',
        'Daily Hydration Target:': 'দৈনিক পানীৰ লক্ষ্য:',
        'Protein Target:': 'প্ৰটিনৰ লক্ষ্য:',
        'Carbs / Fats:': 'কাৰ্বহাইড্ৰেট / চৰ্বি:',
        'Carbs:': 'কাৰ্বহাইড্ৰেট:',
        'Fats:': 'চৰ্বি:',
        'Diet Strategy:': 'খাদ্য কৌশল:',
        "Moderate Calorie Deficit (approx. 450 kcal below expenditure) for steady fat loss while preserving military stamina.": "সামৰিক শক্তি অক্ষুণ্ণ ৰাখি চৰ্বি হ্ৰাস কৰিবলৈ মধ্যমীয়া কেলৰি ঘাটি (প্ৰায় ৪৫০ কেলৰি)।",
        '5. Physical Training': '৫. শাৰীৰিক প্ৰশিক্ষণ',
        'Exercise Recommendations': 'ব্যায়াম পৰামৰ্শ',
        'Exercise / Drill': 'ব্যায়াম / ড্ৰিল',
        'Exercise Name': 'ব্যায়ামৰ নাম',
        'Sets': 'ছেট',
        'Reps / Volume': 'পৰিমাণ',
        'Duration': 'সময়সীমা',
        'Frequency': 'পুনৰাবৃত্তি',
        'High-Tempo Aerobic Jog / Cross-Country (4 - 6km)': 'দ্ৰুত এৰোবিক দৌৰ / ক্ৰছ-কান্ট্ৰি (৪ - ৬ কিমি)',
        'Continuous steady state': 'নিৰন্তৰ স্থিৰ গতি',
        '35 - 40 mins': '৩৫ - ৪০ মিনিট',
        '4 days/week': 'সপ্তাহত ৪ দিন',
        '6. Projected Progression Milestones (30 / 60 / 90 Days)': '৬. প্ৰত্যাশিত অগ্ৰগতিৰ মাইলৰ খুঁটি (৩০ / ৬০ / ৯০ দিন)',
        'Progression Timeline': 'অগ্ৰগতিৰ সময়ৰেখা',
        'Timeline': 'সময়ৰেখা',
        'Projected Weight': 'প্ৰত্যাশিত ওজন',
        'Projected BMI': 'প্ৰত্যাশিত বিএমআই',
        'Estimated Physical Readiness Score': 'প্ৰত্যাশিত ফিটনেছ স্কোৰ',
        'Current Baseline': 'বৰ্তমানৰ ভিত্তি (Baseline)',
        '30 Days Projected': '৩০ দিনৰ পূৰ্বানুমান',
        '60 Days Projected': '৬০ দিনৰ পূৰ্বানুমান',
        '90 Days Projected': '৯০ দিনৰ পূৰ্বানুমান',
        'UNIT MANAGEMENT SYSTEM': 'ইউনিট ব্যৱস্থাপনা প্ৰণালী',
        '15 CORPS / 15 CESR — UNIT MANAGEMENT SYSTEM': 'ইউনিট ব্যৱস্থাপনা প্ৰণালী',
        '15 CORPS ENGINEERING SIGNAL REGIMENT': 'ইউনিট ব্যৱস্থাপনা প্ৰণালী',
        'UMS 15 CESR': 'ইউনিট ব্যৱস্থাপনা প্ৰণালী',
        '8. Personalized Nutrition Recommendations': '৮. ব্যক্তিগত পুষ্টিৰ পৰামৰ্শ',
        'Personalized Nutrition Recommendations': 'ব্যক্তিগত পুষ্টিৰ পৰামৰ্শ',
        "✔ DO'S (Recommended Protocol):": "✔ কৰণীয় (পৰামৰ্শিত নিয়ম):",
        "✔ DO'S (Recommended Protocol)": "✔ কৰণীয় (পৰামৰ্শিত নিয়ম)",
        "DO'S (Recommended Protocol):": "✔ কৰণীয় (পৰামৰ্শিত নিয়ম):",
        "DO'S (Recommended Protocol)": "✔ কৰণীয় (পৰামৰ্শিত নিয়ম)",
        "DO'S": "কৰণীয়",
        "✖ DON'TS (Items & Habits to Avoid):": "✖ বৰ্জনীয় (পৰিহাৰ কৰিবলগীয়া অভ্যাস আৰু বস্তু):",
        "✖ DONTS (Items & Habits to Avoid):": "✖ বৰ্জনীয় (পৰিহাৰ কৰিবলগীয়া অভ্যাস আৰু বস্তু):",
        "✖ DON'TS (Items & Habits to Avoid)": "✖ বৰ্জনীয় (পৰিহাৰ কৰিবলগীয়া অভ্যাস আৰু বস্তু)",
        "✖ DONTS (Items & Habits to Avoid)": "✖ বৰ্জনীয় (পৰিহাৰ কৰিবলগীয়া অভ্যাস আৰু বস্তু)",
        "DON'TS (Items & Habits to Avoid):": "✖ বৰ্জনীয় (পৰিহাৰ কৰিবলগীয়া অভ্যাস আৰু বস্তু):",
        "DONTS (Items & Habits to Avoid):": "✖ বৰ্জনীয় (পৰিহাৰ কৰিবলগীয়া অভ্যাস আৰু বস্তু):",
        "DON'TS": "বৰ্জনীয়",
        "DONTS": "বৰ্জনীয়",
        'Operational Nutrition & Hydration Discipline:': 'কাৰ্যকৰী পুষ্টি আৰু হাইড্ৰেচন অনুশাসন:',
        'Operational Nutrition & Hydration Discipline': 'কাৰ্যকৰী পুষ্টি আৰু হাইড্ৰেচন অনুশাসন',
        'Lean poultry, boiled eggs & paneer for muscle protein synthesis': 'পেশী প্ৰ’টিন গঠনৰ বাবে চিকেন, সিজোৱা কণী আৰু পনীৰ',
        'Whole lentils, dal & sprouted beans for sustained amino acids': 'ধাৰাবাহিক এমিনো এচিডৰ বাবে গোটা দাইল আৰু গজালি ওলোৱা মাহ',
        'Whole grains (oats, brown rice, whole wheat roti) for glycogen replenishment': 'গ্লাইকোজেন পূৰণৰ বাবে গোটা শস্য (ওটচ, ব্ৰাউন ৰাইচ, ঘেঁহুৰ ৰুটি)',
        'Seasonal fresh fruits & leafy vegetables for electrolytes and micronutrients': 'ইলেক্ট্ৰ’লাইট আৰু পুষ্টিকৰ উপাদানৰ বাবে ঋতুভিত্তিক ফল আৰু শাক-পাচলি',
        'Consistent hydration with minimum 3.0 to 3.5 Liters of clean water daily': 'দৈনিক কমেও ৩.০ ৰ পৰা ৩.৫ লিটাৰ বিশুদ্ধ পানী খোৱা',
        'Deep-fried mess snacks, pakoras, and processed canteen confectionery': 'তেলত ভজা জলপান, পকোৰা আৰু প্ৰচেছ কৰা কেণ্টিনৰ খাদ্য',
        'Refined sugar, sugary tea/coffee, and carbonated beverages': 'পৰিশোধিত চেনি, মিঠা চাহ/কফি আৰু কাৰ্বনেটেড পানীয়',
        'Excessive table salt, pickles, and high-sodium processed rations': 'অধিক নিমখ, আচাৰ আৰু অধিক চডিয়ামযুক্ত প্ৰচেছ কৰা খাদ্য',
        'Irregular meal timings or skipping breakfast prior to morning PT': 'অনিয়মীয়া আহাৰৰ সময় বা পুৱাৰ পিটিৰ আগতে ৰাতিপুৱাৰ আহাৰ বাদ দিয়া',
        'Heavy meals consumed less than 2 hours before lights out': 'শোৱাৰ (লাইটছ আউট) ২ ঘণ্টাতকৈ কম সময়ৰ আগতে গধুৰ আহাৰ খোৱা',
        'Maintain consistent meal timings; finish dinner at least 2 hours before lights out.': 'আহাৰৰ নিয়মিত সময়সূচী বজাই ৰাখক; শোৱাৰ কমেও ২ ঘণ্টা আগতে ৰাতিৰ আহাৰ গ্ৰহণ কৰক।',
        'Prioritize lean protein (dal, sprouts, paneer, eggs, chicken) to ensure rapid muscle recovery.': 'পেশীৰ দ্ৰুত আৰোগ্যৰ বাবে প্ৰ’টিনক (দাইল, গজালি ওলোৱা মাহ, পনীৰ, কণী, চিকেন) অগ্ৰাধিকাৰ দিয়ক।',
        'Avoid deep-fried snacks, sugary beverages, and processed confectionery from unit canteen.': 'ইউনিট কেণ্টিনৰ পৰা তেলত ভজা খাদ্য, মিঠা পানীয় আৰু প্ৰচেছ কৰা মিঠাই পৰিহাৰ কৰক।',
        'Ensure adequate hydration of at least 3.5 to 4.0 liters daily, especially during outdoor PT sessions.': 'দৈনিক কমেও ৩.৫ ৰ পৰা ৪.০ লিটাৰ পানী খোৱাটো নিশ্চিত কৰক, বিশেষকৈ বাহিৰৰ পিটিৰ সময়ত।',
        'Include green leafy vegetables and seasonal citrus fruits for vital micronutrients and electrolytes.': 'প্ৰয়োজনীয় পুষ্টি আৰু ইলেক্ট্ৰ’লাইটৰ বাবে সেউজীয়া শাক-পাচলি আৰু নেমুজাতীয় ফল অন্তৰ্ভুক্ত কৰক।',
    }
}


def shape_urdu_for_pdf(text):
    """
    Applies arabic_reshaper and bidi.algorithm to shape cursive Urdu letters
    and order Right-to-Left correctly for PDF canvas engines.
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
    Translates dynamic sentences with embedded numeric values and parameters.
    Keeps numbers and metrics completely intact.
    """
    if not text or target_lang == 'en' or not isinstance(text, str):
        return text
        
    text_clean = text.strip()

    # 1. Exact dictionary match
    lang_dict = VOCABULARY.get(target_lang, {})
    if text_clean in lang_dict:
        return lang_dict[text_clean]

    # Pattern 1: Excess Body Weight with dynamic % and kg
    m = re.match(r"Excess Body Weight:\s*Actual weight is ([0-9.]+)% above ideal standard \(\+([0-9.]+) kg deviation\)\.", text_clean, re.I)
    if m:
        pct, diff = m.group(1), m.group(2)
        templates = {
            'hi': f"अधिक शारीरिक वजन: वास्तविक वजन मानक से {pct}% अधिक है (+{diff} किग्रा विचलन)।",
            'ur': f"اضافی جسمانی وزن: اصل وزن مثالی معیار سے {pct}% زیادہ ہے (+{diff} کلوگرام فرق)۔",
            'bn': f"অতিরিক্ত ওজন: প্রকৃত ওজন আদর্শ মানের চেয়ে {pct}% বেশি (+{diff} কেজি পার্থক্য)।",
            'pa': f"ਵਾਧੂ ਸਰੀਰਕ ਭਾਰ: ਅਸਲ ਭਾਰ ਮਿਆਰੀ ਭਾਰ ਨਾਲੋਂ {pct}% ਵੱਧ ਹੈ (+{diff} ਕਿਲੋਗ੍ਰਾਮ ਅੰਤਰ)।",
            'mr': f"जास्त वजन: प्रत्यक्ष वजन आदर्श मानकापेक्षा {pct}% जास्त आहे (+{diff} किलो फरक).",
            'gu': f"વધારાનું વજન: વાસ્તવિક વજન આદર્શ ધોરણ કરતાં {pct}% વધુ છે (+{diff} કિગ્રા તફાવત).",
            'ta': f"அதிக எடை: உண்மையான எடை இலக்கை விட {pct}% அதிகம் (+{diff} கிலோ വ്യത്യാசம்).",
            'te': f"అధిక శరీర బరువు: అసలు బరువు ప్రామాణికం కంటే {pct}% ఎక్కువ (+{diff} కిలోల వ్యత్యాసం).",
            'kn': f"ಹೆಚ್ಚಿನ ತೂಕ: ನೈಜ ತೂಕವು ಪ್ರಮಾಣಿತಕ್ಕಿಂತ {pct}% ಹೆಚ್ಚಾಗಿದೆ (+{diff} ಕೆಜಿ ವ್ಯತ್ಯಾಸ).",
            'ml': f"അമിത ശരീരഭാരം: യഥാർത്ഥ ഭാരം സാധാരണയേക്കാൾ {pct}% കൂടുതലാണ് (+{diff} കിലോ വ്യത്യാസം).",
            'or': f"ଅଧିକ ଶାରୀରିକ ଓଜନ: ପ୍ରକୃତ ଓଜନ ମାନକ ଠାରୁ {pct}% ଅଧିକ (+{diff} କିଗ୍ରା ପାର୍ଥକ୍ୟ) |",
            'as': f"অতিৰিক্ত ওজন: প্ৰকৃত ওজন আদৰ্শ মানৰ তুলনাত {pct}% অধিক (+{diff} কেজি পাৰ্থক্য)।"
        }
        return templates.get(target_lang, templates.get('hi', text_clean))

    # Pattern 2: Healthy BMI Index
    m = re.match(r"Healthy BMI Index:\s*Body Mass Index \(([0-9.]+)\) indicates prime physical conditioning\.", text_clean, re.I)
    if m:
        val = m.group(1)
        templates = {
            'hi': f"स्वस्थ बीएमआई सूचकांक: बॉडी मास इंडेक्स ({val}) उत्कृष्ट शारीरिक स्थिति दर्शाता है।",
            'ur': f"صحت مند بی ایم آئی انڈیکس: باڈی ماس انڈیکس ({val}) بہترین جسمانی حالت کی نشاندہی کرتا ہے۔",
            'bn': f"স্বাস্থ্যকর বিএমআই সূচক: বডি ম্যাস ইনডেক্স ({val}) চমৎকার শারীরিক অবস্থা নির্দেশ করে।",
            'pa': f"ਸਿਹਤਮੰਦ ਬੀਐਮਆਈ ਸੂਚਕਾਂਕ: ਬਾਡੀ ਮਾਸ ਇੰਡੈਕਸ ({val}) ਵਧੀਆ ਸਰੀਰਕ ਸਥਿਤੀ ਦਰਸਾਉਂਦਾ ਹੈ।",
            'mr': f"निरोगी बीएमआय निर्देशांक: बॉडी मास इंडेक्स ({val}) उत्कृष्ट शारीरिक स्थिती दर्शवितो.",
            'gu': f"સ્વસ્થ બીએમઆઈ અનુક્રમણિકા: બોડી માસ ઇન્ડેક્સ ({val}) ઉત્તમ શારીરિક સ્થિતિ દર્શાવે છે.",
            'ta': f"ஆரோக்கியமான பிஎம்ஐ குறியீடு: பிஎம்ഐ ({val}) சிறந்த உடல் தகுதியைக் குறிக்கிறது.",
            'te': f"ఆరోగ్యకరమైన బిఎమ్‌ఐ సూచిక: బాడీ మాస్ ఇండెక్స్ ({val}) అద్భుతమైన శారీరక స్థితిని సూచిస్తుంది.",
            'kn': f"ಆರೋಗ್ಯಕರ ಬಿಎಂಐ ಸೂಚ್ಯಂಕ: ಬಾಡಿ ಮಾಸ್ ಇಂಡೆಕ್ಸ್ ({val}) ಅತ್ಯುತ್ತಮ ದೈಹಿಕ ಸ್ಥಿತಿಯನ್ನು ಸೂಚಿಸುತ್ತದೆ.",
            'ml': f"ആരോഗ്യമുള്ള ബിഎംഐ സൂചിക: ബോഡി മാസ് ഇൻഡക്സ് ({val}) മികച്ച ശാരീരിക അവസ്ഥയെ സൂചിപ്പിക്കുന്നു.",
            'or': f"ସ୍ୱାସ୍ଥ୍ୟକର ବିଏମଆଇ ସୂଚକାଙ୍କ: ବଡି ମାସ ଇଣ୍ଡେକ୍ସ ({val}) ଉତ୍କୃଷ୍ଟ ଶାରୀରିକ ସ୍ଥିତି ଦର୍ଶାଏ |",
            'as': f"স্বাস্থ্যকৰ বিএমআই সূচক: বডি মাচ ইনডেক্স ({val}) উৎকৃষ্ট শাৰীৰিক অৱস্থা নিৰ্দেশ কৰে।"
        }
        return templates.get(target_lang, templates.get('hi', text_clean))

    # Pattern 3: Active Sports Participation
    m = re.match(r"Active Sports Participation:\s*Regularly participates in unit athletic activities \((.+)\)\.", text_clean, re.I)
    if m:
        sport = m.group(1)
        sport_tr = lang_dict.get(sport, sport)
        templates = {
            'hi': f"सक्रिय खेल भागीदारी: यूनिट की खेल गतिविधियों ({sport_tr}) में नियमित रूप से भाग लेता है।",
            'ur': f"کھیلوں میں فعال شرکت: باقاعدگی سے یونٹ کی کھیلوں کی سرگرمیوں ({sport_tr}) میں حصہ لیتا ہے۔",
            'bn': f"সক্রিয় ক্রীড়া অংশগ্রহণ: নিয়মিতভাবে ইউনিটের ক্রীড়া কার্যকলাপে ({sport_tr}) অংশ নেয়।",
            'pa': f"ਖੇਡਾਂ ਵਿੱਚ ਸਰਗਰਮ ਭਾਗੀਦਾਰੀ: ਨਿਯਮਿਤ ਤੌਰ 'ਤੇ ਯੂਨਿਟ ਖੇਡਾਂ ({sport_tr}) ਵਿੱਚ ਹਿੱਸਾ ਲੈਂਦਾ ਹੈ।",
            'mr': f"सक्रिय खेळ सहभाग: युनिटच्या क्रीडा स्पर्धांमध्ये ({sport_tr}) नियमितपणे सहभाग घेतो.",
            'gu': f"રમતોમાં સક્રિય સહભાગિતા: યુનિટની રમતગમત પ્રવૃત્તિઓમાં ({sport_tr}) નિયમિતપણે ભાગ લે છે.",
            'ta': f"செயலில் உள்ள விளையாட்டு பங்கேற்பு: யூனிட் விளையாட்டுகளில் ({sport_tr}) தவறாமல் பங்கேற்கிறார்.",
            'te': f"క్రీడలలో చురుకైన భాగస్వామ్యం: యూనిట్ క్రీడా కార్యకలాపాలలో ({sport_tr}) క్రమం తప్పకుండా పాల్గొంటాడు.",
            'kn': f"ಸಕ್ರಿಯ ಕ್ರೀಡಾ ಪಾಲ್ಗೊಳ್ಳುವಿಕೆ: ಯುನಿಟ್ ಕ್ರೀಡಾ ಚಟುವಟಿಕೆಗಳಲ್ಲಿ ({sport_tr}) ನಿಯಮಿತವಾಗಿ ಭಾಗವಹಿಸುತ್ತಾನೆ.",
            'ml': f"സജീവ കായിക പങ്കാളിത്തം: യൂണിറ്റ് അത്‌ലറ്റിക് പ്രവർത്തനങ്ങളിൽ ({sport_tr}) പതിവായി പങ്കെടുക്കുന്നു.",
            'or': f"ସକ୍ରିୟ ଖେଳ ଅଂଶଗ୍ରହଣ: ନିୟମିତ ଭାବରେ ୟୁନିଟ କ୍ରୀଡ଼ା ({sport_tr}) ରେ ଅଂଶଗ୍ରହଣ କରେ |",
            'as': f"সক্ৰিয় ক্ৰীড়া অংশগ্ৰহণ: ইউনিটৰ ক্ৰীড়া কাৰ্যকলাপত ({sport_tr}) নিয়মীয়াকৈ অংশগ্ৰহণ কৰে।"
        }
        return templates.get(target_lang, templates.get('hi', text_clean))

    # Pattern 4: Optimal Body Weight
    m = re.match(r"Optimal Body Weight:\s*Actual weight is within ([0-9.]+)% of the Indian Army ideal weight benchmark\.", text_clean, re.I)
    if m:
        pct = m.group(1)
        templates = {
            'hi': f"अनुकूलतम शारीरिक वजन: वास्तविक वजन भारतीय सेना के आदर्श वजन मानक के {pct}% के भीतर है।",
            'ur': f"بہترین جسمانی وزن: اصل وزن بھارتی فوج کے مثالی وزن کے معیار کے {pct}% کے اندر ہے۔",
            'bn': f"অনুকূল ওজন: প্রকৃত ওজন ভারতীয় সেনাবাহিনীর আদর্শ ওজনের {pct}% এর মধ্যে রয়েছে।",
            'pa': f"ਸਹੀ ਸਰੀਰਕ ਭਾਰ: ਅਸਲ ਭਾਰ ਭਾਰਤੀ ਫੌਜ ਦੇ ਆਦਰਸ਼ ਭਾਰ ਮਿਆਰ ਦੇ {pct}% ਦੇ ਅੰਦਰ ਹੈ।",
            'mr': f"इष्टतम वजन: प्रत्यक्ष वजन भारतीय लष्कराच्या आदर्श वजन मानकाच्या {pct}% च्या आत आहे.",
            'gu': f"આદર્શ વજન: વાસ્તવિક વજન ભારતીય સેનાના આદર્શ વજન ધોરણના {pct}% ની અંદર છે.",
            'ta': f"உகந்த எடை: உண்மையான எடை இந்திய இராணுவத்தின் சிறந்த எடையின் {pct}% க்குள் உள்ளது.",
            'te': f"ఆదర్శవంతమైన బరువు: అసలు బరువు భారత సైన్యం ఆదర్శ బరువు ప్రమాణంలో {pct}% లోపు ఉంది.",
            'kn': f"ಆದರ್ಶ ತೂಕ: ನೈಜ ತೂಕವು ಭಾರತೀಯ ಸೇನೆಯ ಆದರ್ಶ ತೂಕದ ಮಾನದಂಡದ {pct}% ಒಳಗೆ ಇದೆ.",
            'ml': f"അനുയോജ്യമായ ഭാരം: യഥാർത്ഥ ഭാരം ഇന്ത്യൻ ആർമിയുടെ അനുയോജ്യമായ ഭാരത്തിന്റെ {pct}% പരിധിക്കുള്ളിലാണ്.",
            'or': f"ଅନୁକୂଳ ଓଜନ: ପ୍ରକୃତ ଓଜନ ଭାରତୀୟ ସେନାର ଆଦର୍ଶ ଓଜନ ମାନକର {pct}% ମଧ୍ୟରେ ଅଛି |",
            'as': f"অনুকূল ওজন: প্ৰকৃত ওজন ভাৰতীয় সেনাৰ আদৰ্শ ওজনৰ মানদণ্ডৰ {pct}% ৰ ভিতৰত আছে।"
        }
        return templates.get(target_lang, templates.get('hi', text_clean))

    # Pattern 5: Authorized Weight Range
    m = re.match(r"Authorized Weight Range:\s*Current weight \(\+([0-9.]+)%\) is within permissible military SHAPE-1 authorization\.", text_clean, re.I)
    if m:
        pct = m.group(1)
        if target_lang == 'ur':
            return f"مجاز وزن کی حد: موجودہ وزن (+{pct}%) فوجی شیپ-1 کی مجاز حد کے اندر ہے۔"
        return f"स्वीकृत वजन सीमा: वर्तमान वजन (+{pct}%) सेना के शेप-1 मानदंडों के अंतर्गत अनुमेय है।"

    # Pattern 6: Repetitions (e.g. "15-20 reps", "20 reps")
    m = re.match(r"^([0-9\-]+)\s*reps?$", text_clean, re.I)
    if m:
        val = m.group(1)
        rep_words = {
            'hi': f"{val} बार", 'ur': f"{val} بار", 'mr': f"{val} वेळा", 'ta': f"{val} முறை",
            'bn': f"{val} বার", 'pa': f"{val} ਵਾਰ", 'gu': f"{val} વાર", 'te': f"{val} సార్లు",
            'kn': f"{val} ಬಾರಿ", 'ml': f"{val} തവണ", 'or': f"{val} ଥର", 'as': f"{val} বাৰ"
        }
        return rep_words.get(target_lang, f"{val} reps")

    # Pattern 7: Duration in minutes (e.g. "30-40 mins", "30 mins", "45 min")
    m = re.match(r"^([0-9\-]+)\s*mins?$", text_clean, re.I)
    if m:
        val = m.group(1)
        min_words = {
            'hi': f"{val} मिनट", 'ur': f"{val} منٹ", 'mr': f"{val} मिनिटे", 'ta': f"{val} நிமிடங்கள்",
            'bn': f"{val} মিনিট", 'pa': f"{val} ਮਿੰਟ", 'gu': f"{val} મિનિટ", 'te': f"{val} నిమిషాలు",
            'kn': f"{val} ನಿಮಿಷಗಳು", 'ml': f"{val} മിനിറ്റ്", 'or': f"{val} ମିନିଟ୍", 'as': f"{val} মিনিট"
        }
        return min_words.get(target_lang, f"{val} mins")

    # Pattern 8: Duration in seconds (e.g. "45-60 sec plank", "60 sec")
    m = re.match(r"^([0-9\-]+)\s*sec(?:\s*(.+))?$", text_clean, re.I)
    if m:
        val = m.group(1)
        extra = m.group(2)
        sec_words = {
            'hi': f"{val} सेकंड", 'ur': f"{val} سیکنڈ", 'mr': f"{val} सेकंद", 'ta': f"{val} வினாடிகள்",
            'bn': f"{val} সেকেন্ড", 'pa': f"{val} ਸਕਿੰਟ", 'gu': f"{val} સેકન્ડ", 'te': f"{val} సెకన్లు",
            'kn': f"{val} ಸೆಕೆಂಡುಗಳು", 'ml': f"{val} സെക്കൻഡ്", 'or': f"{val} ସେକେଣ୍ଡ", 'as': f"{val} ছেকেণ্ড"
        }
        base_sec = sec_words.get(target_lang, f"{val} sec")
        if extra:
            extra_tr = lang_dict.get(extra, extra)
            return f"{base_sec} {extra_tr}"
        return base_sec

    # IndicTrans2 fallback attempt if available
    indictrans = get_indictrans()
    if indictrans.is_available():
        res = indictrans.translate_batch([text_clean], src_lang="en", tgt_lang=target_lang)
        if res and res[0]:
            return res[0]

    # Hindi fallback dictionary for missing regional phrases
    if target_lang != 'hi' and 'hi' in VOCABULARY and text_clean in VOCABULARY['hi']:
        return VOCABULARY['hi'][text_clean]

    return text_clean


def translate_text(text, target_lang='en', for_pdf=False):
    """
    Translates a single piece of text into target_lang, respecting cache and PDF shaping.
    """
    if not text or target_lang == 'en' or not isinstance(text, str):
        return text
        
    cache_key = (text, target_lang, for_pdf)
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    translated = translate_dynamic_sentence(text, target_lang)
    if for_pdf and target_lang == 'ur':
        translated = shape_urdu_for_pdf(translated)

    _TRANSLATION_CACHE[cache_key] = translated
    return translated


def get_report_labels(target_lang='en', for_pdf=False):
    """
    Returns localized UI and PDF report labels for all 13 supported languages.
    """
    base_labels = {
        'unit_title': '15 CORPS UNIT MANAGEMENT SYSTEM',
        'report_title': 'Personal Fitness Report',
        'report_generated': 'Report Generated',
        'model_version': 'Model Version',
        'confidential': 'CONFIDENTIAL',
        'sec1_title': '1. Soldier Particulars & Service Profile',
        'name': 'Name',
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
        'ideal_wt_dev': 'Ideal Wt / Deviation',
        'bmi_cat': 'BMI:',
        'weight_dev': 'Weight Deviation:',
        'bpet_grading': 'BPET Grading:',
        'ppt_grading': 'PPT Grading:',
        'bpet_ppt_grading': 'BPET / PPT Grading',
        'sports': 'Sports & Athletics:',
        'activity_level': 'Physical Activity Level:',
        'sec3_title': '3. AI Physical Readiness Prediction',
        'readiness_prediction': 'AI Physical Readiness Prediction',
        'readiness_score': 'AI Physical Readiness Score:',
        'prediction_conf': 'Prediction Confidence:',
        'confidence': 'Confidence',
        'algorithm': 'Algorithm:',
        'key_strengths': 'Key Strengths (Positive Indicators):',
        'key_positive_factors': 'Key Positive Factors:',
        'action_areas': 'Priority Action Areas:',
        'sec4_title': '4. Personalized Dietary & Macronutrient Plan',
        'daily_energy': 'Daily Energy Target:',
        'daily_hydration': 'Daily Hydration Target:',
        'protein_target': 'Protein Target:',
        'carbs_fats': 'Carbs / Fats:',
        'carbs': 'Carbs:',
        'fats': 'Fats:',
        'complex_carbs': 'COMPLEX CARBS',
        'healthy_fats': 'HEALTHY FATS',
        'daily_protein': 'DAILY PROTEIN',
        'hydration': 'HYDRATION',
        'diet_strategy': 'Diet Strategy:',
        'sec5_title': '5. Physical Training',
        'exercise_drill': 'Exercise / Drill',
        'sets': 'Sets',
        'reps_volume': 'Reps / Volume',
        'duration': 'Duration',
        'frequency': 'Frequency',
        'sec6_title': '6. Projected Progression Milestones (30 / 60 / 90 Days)',
        'timeline': 'Timeline',
        'proj_weight': 'Weight',
        'proj_bmi': 'BMI',
        'est_score': 'Estimated Physical Readiness Score',
        'official_preview_title': 'Official Individual Fitness Report Preview',
        'download_pdf': 'Download PDF Document',
        'export_pdf': 'Export PDF',
        'regiment_name': '15 CORPS UNIT MANAGEMENT SYSTEM',
        'military_record_sub': '15 CORPS UNIT MANAGEMENT SYSTEM • OFFICIAL MILITARY RECORD • CONFIDENTIAL',
        'report_header_title': 'Personal Fitness Report',
        'report_id': 'Report ID:',
        'sec1_title': '1. Personal & Fitness Profile',
        'sec2_title': '2. Fitness Analysis',
        'sec3_title': '3. AI Fitness Assessment',
        'sec4_title': '4. AI Fitness Prediction',
        'sec5_title': '5. Fitness Progression',
        'sec6_title': '6. Weight / Fitness Trend',
        'sec7_title': '7. Personalized Exercise Plan',
        'sec8_title': '8. Personalized Nutrition Recommendations',
        'sec10_title': '10. Areas for Improvement',
        'sec11_title': '11. AI Personalized Recommendations',
        'sec12_title': '12. Fitness Goals',
        'sec13_title': '13. Progress Monitoring',
        'sec14_title': '14. AI Fitness Insights',
        'sec15_title': '15. Important Note / Disclaimer',
        'sec16_title': '16. Official Record Authentication',
        'overall_score': 'OVERALL FITNESS SCORE',
        'condition_summary': 'Condition Summary:',
        'trend_status': 'Weight & Conditioning Trend Status:',
        'trend_notice': 'Historical trend data unavailable for this record. Baseline established from latest unit medical inspection; target progression benchmarks are set below.',
        'baseline_weight': 'Weight:',
        'target_benchmark': 'Target:',
        'variance': 'Target:',
        'recommended_nutrition': "✔ DO'S (Recommended Protocol):",
        'limit_nutrition': "✖ DON'TS (Items & Habits to Avoid):",
        'dietary_guidelines_title': 'Operational Nutrition & Hydration Discipline:',
        'priority_1': 'Priority 1:',
        'priority_2': 'Priority 2:',
        'priority_3': 'Priority 3:',
        'short_term_goals': 'Short-Term Goals (1 - 4 Weeks):',
        'medium_term_goals': 'Medium-Term Goals (4 - 8 Weeks):',
        'long_term_goals': 'Long-Term Goals (8 - 12 Weeks):',
        'param': 'Parameter',
        'current_val': 'Current',
        'target_val': 'Target',
        'monitoring_freq': 'Monitoring Frequency',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'quarterly': 'Quarterly',
        'daily': 'Daily',
        'overall_assessment': 'Overall Assessment:',
        'primary_improvements': 'Primary Areas for Improvement:',
        'recommended_focus': 'Recommended Focus:',
        'disclaimer_title': 'Important Note / Medical Disclaimer:',
        'disclaimer_text': 'This report is generated by the UMS AI Fitness System using available personnel and fitness information. AI-generated predictions and recommendations are intended to support fitness planning and should not replace professional medical assessment or advice.',
        'preview_report': 'Preview Report',
        'generate_pdf': 'Generate PDF',
        'view_pdf': 'View PDF',
        'download_pdf_btn': 'Download PDF',
        'kcal_day': 'kcal / Day',
        'liters_day': 'Liters / Day',
        'pts': 'PTS',
        'untested': 'Untested',
        'none': 'None'
    }

    if target_lang == 'en':
        return base_labels

    translated_labels = {}
    lang_dict = VOCABULARY.get(target_lang, {})
    for k, v in base_labels.items():
        translated = lang_dict.get(v, translate_text(v, target_lang=target_lang, for_pdf=False))
        if for_pdf and target_lang == 'ur':
            translated = shape_urdu_for_pdf(translated)
        translated_labels[k] = translated

    return translated_labels


def translate_report_data(soldier, prediction, recommendations, progression, target_lang='en', for_pdf=False):
    """
    Creates a deep-copy of standard report dictionaries and translates only human-readable text.
    STRICTLY preserves:
    - Army Number, Personnel ID, database keys
    - Numeric values (height_cm, actual_weight_kg, ideal_weight_kg, bmi, confidence_score)
    - Scores and Percentages (78.6, 92.4%, dev_pct)
    - Sets, Repetitions, Durations, Dates
    """
    if target_lang == 'en':
        return soldier, prediction, recommendations, progression

    t_soldier = copy.deepcopy(soldier)
    t_pred = copy.deepcopy(prediction)
    t_rec = copy.deepcopy(recommendations)
    t_prog = copy.deepcopy(progression)

    def _tr(val):
        if not val or not isinstance(val, str):
            return val
        res = translate_dynamic_sentence(val, target_lang)
        if for_pdf and target_lang == 'ur':
            return shape_urdu_for_pdf(res)
        return res

    # 1. Soldier demographic descriptions
    if t_soldier.get('rank'):
        t_soldier['rank'] = _tr(t_soldier['rank'])
    if t_soldier.get('trade'):
        t_soldier['trade'] = _tr(t_soldier['trade'])
    if t_soldier.get('company'):
        t_soldier['company'] = _tr(t_soldier['company'])
    if t_soldier.get('section'):
        t_soldier['section'] = _tr(t_soldier['section'])
    if t_soldier.get('weight_status'):
        t_soldier['weight_status'] = _tr(t_soldier['weight_status'])
    if t_soldier.get('bmi_category'):
        t_soldier['bmi_category'] = _tr(t_soldier['bmi_category'])
    if t_soldier.get('bpet_grade'):
        t_soldier['bpet_grade'] = _tr(t_soldier['bpet_grade'])
    if t_soldier.get('ppt_grade'):
        t_soldier['ppt_grade'] = _tr(t_soldier['ppt_grade'])
    if t_soldier.get('physical_activity_level'):
        t_soldier['physical_activity_level'] = _tr(t_soldier['physical_activity_level'])
    if t_soldier.get('sports_list'):
        t_soldier['sports_list'] = _tr(t_soldier['sports_list'])

    # 2. Prediction human-readable categories & bullet factors
    if t_pred.get('category_label'):
        t_pred['category_label'] = _tr(t_pred['category_label'])
    if t_pred.get('strengths'):
        t_pred['strengths'] = [_tr(s) for s in t_pred['strengths']]
    if t_pred.get('improvements'):
        t_pred['improvements'] = [_tr(i) for i in t_pred['improvements']]

    # 3. Dietary strategy description
    if t_rec.get('diet') and isinstance(t_rec['diet'], dict):
        if t_rec['diet'].get('strategy'):
            t_rec['diet']['strategy'] = _tr(t_rec['diet']['strategy'])
        if t_rec['diet'].get('recommended_items'):
            t_rec['diet']['recommended_items'] = [_tr(x) for x in t_rec['diet']['recommended_items']]
        if t_rec['diet'].get('limit_items'):
            t_rec['diet']['limit_items'] = [_tr(x) for x in t_rec['diet']['limit_items']]
        if t_rec['diet'].get('dietary_guidelines'):
            t_rec['diet']['dietary_guidelines'] = [_tr(x) for x in t_rec['diet']['dietary_guidelines']]

    # 4. Exercise regimen title & exercise names
    if t_rec.get('exercise'):
        if t_rec['exercise'].get('title'):
            t_rec['exercise']['title'] = _tr(t_rec['exercise']['title'])
        if t_rec['exercise'].get('focus_area'):
            t_rec['exercise']['focus_area'] = _tr(t_rec['exercise']['focus_area'])
        if t_rec['exercise'].get('exercises'):
            for ex in t_rec['exercise']['exercises']:
                if 'exercise' in ex:
                    ex['exercise'] = _tr(ex['exercise'])
                if 'reps' in ex:
                    ex['reps'] = _tr(ex['reps'])
                if 'duration' in ex:
                    ex['duration'] = _tr(ex['duration'])
                if 'frequency' in ex:
                    ex['frequency'] = _tr(ex['frequency'])

    # 5. Progression timeline period names & chart labels
    if t_prog.get('milestones'):
        for m in t_prog['milestones']:
            if 'period' in m:
                m['period'] = _tr(m['period'])
    if t_prog.get('chart_data') and t_prog['chart_data'].get('labels'):
        t_prog['chart_data']['labels'] = [_tr(lbl) for lbl in t_prog['chart_data']['labels']]

    return t_soldier, t_pred, t_rec, t_prog


def translate_16section_report(report_dict, target_lang='en', for_pdf=False):
    """
    Translates a complete 16-section structured fitness report payload.
    Strictly preserves all numerical values, Army numbers, dates, and scores.
    """
    if target_lang == 'en' or not report_dict or not isinstance(report_dict, dict):
        return report_dict

    t = copy.deepcopy(report_dict)

    def _tr(val):
        if not val or not isinstance(val, str):
            return val
        res = translate_dynamic_sentence(val, target_lang)
        if for_pdf and target_lang == 'ur':
            return shape_urdu_for_pdf(res)
        return res

    # 1. Header
    if 'header' in t and isinstance(t['header'], dict):
        for k in ['title', 'rank', 'company', 'confidential']:
            if t['header'].get(k):
                t['header'][k] = _tr(t['header'][k])

    # 2. Profile
    if 'profile' in t and isinstance(t['profile'], dict):
        for k in ['rank', 'trade', 'company', 'section']:
            if t['profile'].get(k):
                t['profile'][k] = _tr(t['profile'][k])

    # 3. Analysis
    if 'analysis' in t and isinstance(t['analysis'], dict):
        for k in ['weight_status', 'fitness_category', 'medical_status', 'bpet_grade', 'ppt_grade', 'sports_list', 'activity_level', 'condition_summary']:
            if t['analysis'].get(k):
                t['analysis'][k] = _tr(t['analysis'][k])

    # 4. Assessment
    if 'assessment' in t and isinstance(t['assessment'], dict):
        for k in ['category_label', 'readiness_tier']:
            if t['assessment'].get(k):
                t['assessment'][k] = _tr(t['assessment'][k])

    # 5. Prediction
    if 'prediction' in t and isinstance(t['prediction'], dict):
        if t['prediction'].get('predicted_status'):
            t['prediction']['predicted_status'] = _tr(t['prediction']['predicted_status'])
        if t['prediction'].get('strengths'):
            t['prediction']['strengths'] = [_tr(s) for s in t['prediction']['strengths']]
        if t['prediction'].get('improvements'):
            t['prediction']['improvements'] = [_tr(i) for i in t['prediction']['improvements']]

    # 6. Trend
    if 'trend' in t and isinstance(t['trend'], dict):
        if t['trend'].get('notice'):
            t['trend']['notice'] = _tr(t['trend']['notice'])

    # 7. Progression
    if 'progression' in t and isinstance(t['progression'], dict):
        if t['progression'].get('milestones'):
            for m in t['progression']['milestones']:
                if 'period' in m:
                    m['period'] = _tr(m['period'])
        if t['progression'].get('chart_data') and t['progression']['chart_data'].get('labels'):
            t['progression']['chart_data']['labels'] = [_tr(lbl) for lbl in t['progression']['chart_data']['labels']]

    # 8. Exercise Plan
    if 'exercise_plan' in t and isinstance(t['exercise_plan'], dict):
        if t['exercise_plan'].get('title'):
            t['exercise_plan']['title'] = _tr(t['exercise_plan']['title'])
        if t['exercise_plan'].get('focus_area'):
            t['exercise_plan']['focus_area'] = _tr(t['exercise_plan']['focus_area'])
        if t['exercise_plan'].get('exercises'):
            for ex in t['exercise_plan']['exercises']:
                for k in ['exercise', 'reps', 'duration', 'frequency', 'rest', 'progression_note']:
                    if ex.get(k):
                        ex[k] = _tr(ex[k])

    # 9. Nutrition
    if 'nutrition' in t and isinstance(t['nutrition'], dict):
        if t['nutrition'].get('strategy'):
            t['nutrition']['strategy'] = _tr(t['nutrition']['strategy'])
        if t['nutrition'].get('recommended_items'):
            t['nutrition']['recommended_items'] = [_tr(x) for x in t['nutrition']['recommended_items']]
        if t['nutrition'].get('limit_items'):
            t['nutrition']['limit_items'] = [_tr(x) for x in t['nutrition']['limit_items']]
        if t['nutrition'].get('guidelines'):
            t['nutrition']['guidelines'] = [_tr(x) for x in t['nutrition']['guidelines']]
        if t['nutrition'].get('optional_diet_plan') and isinstance(t['nutrition']['optional_diet_plan'], dict):
            if t['nutrition']['optional_diet_plan'].get('title'):
                t['nutrition']['optional_diet_plan']['title'] = _tr(t['nutrition']['optional_diet_plan']['title'])
            if t['nutrition']['optional_diet_plan'].get('description'):
                t['nutrition']['optional_diet_plan']['description'] = _tr(t['nutrition']['optional_diet_plan']['description'])

    # 10. Areas for Improvement
    if t.get('improvement_areas'):
        t['improvement_areas'] = [_tr(x) for x in t['improvement_areas']]

    # 11. Priority Recommendations
    if t.get('priority_recs'):
        for pr in t['priority_recs']:
            if pr.get('priority'):
                pr['priority'] = _tr(pr['priority'])
            if pr.get('title'):
                pr['title'] = _tr(pr['title'])
            if pr.get('detail'):
                pr['detail'] = _tr(pr['detail'])

    # 12. Goals
    if t.get('goals') and isinstance(t['goals'], dict):
        for k in ['short_term', 'medium_term', 'long_term']:
            if t['goals'].get(k):
                t['goals'][k] = _tr(t['goals'][k])

    # 13. Progress Monitoring
    if t.get('monitoring'):
        for row in t['monitoring']:
            if row.get('parameter'):
                row['parameter'] = _tr(row['parameter'])
            if row.get('frequency'):
                row['frequency'] = _tr(row['frequency'])

    # 14. Insights
    if t.get('insights') and isinstance(t['insights'], dict):
        for k in ['overall_assessment', 'recommended_focus']:
            if t['insights'].get(k):
                t['insights'][k] = _tr(t['insights'][k])
        if t['insights'].get('key_strengths'):
            t['insights']['key_strengths'] = [_tr(x) for x in t['insights']['key_strengths']]
        if t['insights'].get('primary_areas'):
            t['insights']['primary_areas'] = [_tr(x) for x in t['insights']['primary_areas']]

    # 15. Disclaimer
    if t.get('disclaimer'):
        t['disclaimer'] = _tr(t['disclaimer'])

    # 16. Footer
    if t.get('footer') and isinstance(t['footer'], dict):
        if t['footer'].get('regiment'):
            t['footer']['regiment'] = _tr(t['footer']['regiment'])
        if t['footer'].get('sub'):
            t['footer']['sub'] = _tr(t['footer']['sub'])

    # Translate soldier & recommendations sub-objects for template compatibility
    if 'soldier' in t and isinstance(t['soldier'], dict):
        t_s, _, t_r, _ = translate_report_data(
            t.get('soldier', {}), t.get('prediction', {}), t.get('recommendations', {}), t.get('progression', {}),
            target_lang=target_lang, for_pdf=for_pdf
        )
        t['soldier'] = t_s
        if 'recommendations' in t:
            t['recommendations'] = t_r

    return t
