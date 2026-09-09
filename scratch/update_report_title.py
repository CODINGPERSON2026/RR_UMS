# -*- coding: utf-8 -*-
import os
import sys

target_path = r"e:\UMS-LATEST\aiml\fitness_trend\translation\translator.py"

with open(target_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update base_labels
content = content.replace(
    "'report_title': 'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT',",
    "'report_title': 'Personal Fitness Report',"
)
content = content.replace(
    "'report_header_title': 'UMS AI FITNESS & PERSONALIZED FITNESS REPORT',",
    "'report_header_title': 'Personal Fitness Report',"
)

# Translations for Personal Fitness Report across all 12 languages
TITLES = {
    'hi': 'व्यक्तिगत फिटनेस रिपोर्ट',
    'ur': 'ذاتی فٹنس رپورٹ',
    'bn': 'ব্যক্তিগত ফিটনেস রিপোর্ট',
    'pa': 'ਨਿੱਜੀ ਫਿਟਨੈਸ ਰਿਪੋਰਟ',
    'mr': 'वैयक्तिक तंदुरुस्ती अहवाल',
    'gu': 'વ્યક્તિગત ફિટનેસ રિપોર્ટ',
    'ta': 'தனிநபர் உடற்தகுதி அறிக்கை',
    'te': 'వ్యక్తిగత ఫిట్‌నెస్ నివేదిక',
    'kn': 'ವೈಯಕ್ತಿಕ ಫಿಟ್‌ನೆಸ್ ವರದಿ',
    'ml': 'വ്യക്തിഗത ഫിറ്റ്നസ് റിപ്പോർട്ട്',
    'or': 'ବ୍ୟକ୍ତିଗତ ଫିଟନେସ ରିପୋର୍ଟ',
    'as': 'ব্যক্তিগত ফিটনেছ প্ৰতিবেদন'
}

for lang, native in TITLES.items():
    lang_header = f"'{lang}': {{"
    pos_start = content.find(lang_header)
    if pos_start == -1:
        print(f"Lang '{lang}' header not found")
        continue

    insertion = (
        f"        'Personal Fitness Report': '{native}',\n"
        f"        'Personnal Fitness Report': '{native}',\n"
        f"        'AI INDIVIDUAL FITNESS PREDICTION & READINESS REPORT': '{native}',\n"
    )

    # Insert right after the lang_header
    content = content[:pos_start + len(lang_header) + 1] + "\n" + insertion + content[pos_start + len(lang_header) + 1:]
    print(f"Inserted report title entries for '{lang}'")

with open(target_path, "w", encoding="utf-8") as f:
    f.write(content)

print("translator.py updated with report title translations.")
