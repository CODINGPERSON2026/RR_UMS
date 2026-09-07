"""
Translator Service for UMS Individual Fitness Reports.
Exposes a clean, unified offline translation interface for all supported Indian languages.
Strictly local, offline-capable, preserving all numeric metrics, Army numbers, and scores.
"""

import copy
import logging
from ..translation.language_config import (
    SUPPORTED_LANGUAGES as _LANG_CONFIG,
    DEFAULT_LANGUAGE,
    is_supported_language,
    get_language_name,
    is_rtl,
    get_indictrans_code
)
from ..translation.translator import (
    translate_report_data,
    translate_16section_report,
    translate_text,
    get_report_labels,
    shape_urdu_for_pdf
)

logger = logging.getLogger("fitness_trend.reports.translator")

# Centrally defined supported languages dictionary
LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ur": "Urdu",
    "ta": "Tamil",
    "mr": "Marathi",
    "pa": "Punjabi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "or": "Odia",
    "as": "Assamese"
}

# Alias for full backward compatibility
SUPPORTED_LANGUAGES = LANGUAGES


def translate_report(report_data, target_language="en", for_pdf=False):
    """
    Translates structured fitness report data into the selected target language.
    
    Args:
        report_data (dict): Dictionary containing 'soldier', 'prediction',
                            'recommendations', and 'progression' dictionaries.
        target_language (str): Supported ISO language code (e.g., 'mr', 'ta', 'ur', 'hi', 'en').
        for_pdf (bool): If True, applies script shaping (such as Urdu cursive bidi shaping).
        
    Returns:
        dict: A localized deep-copy of the report dictionary with all human-readable
              descriptions translated, numbers strictly preserved, and UI labels attached.
    """
    if not isinstance(report_data, dict):
        logger.warning(f"translate_report received non-dict input: {type(report_data)}")
        return report_data

    # Validate target language with safe fallback to English
    lang = (target_language or DEFAULT_LANGUAGE).lower().strip()
    if not is_supported_language(lang):
        logger.warning(f"Unsupported language '{lang}' requested. Falling back to English ('en').")
        lang = DEFAULT_LANGUAGE

    # If English, return report without unnecessary translation
    if lang == DEFAULT_LANGUAGE:
        result = copy.deepcopy(report_data)
        result['labels'] = get_report_labels('en', for_pdf=for_pdf)
        result['language'] = 'en'
        return result

    # Check if this is a 16-section structured report dictionary
    is_16_section = any(k in report_data for k in ('header', 'profile', 'analysis', 'exercise_plan', 'priority_recs'))

    try:
        if is_16_section:
            result = translate_16section_report(report_data, target_lang=lang, for_pdf=for_pdf)
        else:
            soldier = report_data.get('soldier') or {}
            prediction = report_data.get('prediction') or {}
            recommendations = report_data.get('recommendations') or {}
            progression = report_data.get('progression') or {}

            t_soldier, t_prediction, t_recommendations, t_progression = translate_report_data(
                soldier=soldier,
                prediction=prediction,
                recommendations=recommendations,
                progression=progression,
                target_lang=lang,
                for_pdf=for_pdf
            )

            result = copy.deepcopy(report_data)
            result['soldier'] = t_soldier
            result['prediction'] = t_prediction
            result['recommendations'] = t_recommendations
            result['progression'] = t_progression

        labels = get_report_labels(target_lang=lang, for_pdf=for_pdf)
        result['labels'] = labels
        result['language'] = lang
        result['direction'] = 'rtl' if is_rtl(lang) else 'ltr'
        return result

    except Exception as e:
        logger.error(f"Error translating report into '{lang}': {e}", exc_info=True)
        # Safe fallback: return untranslated English with error handled
        fallback = copy.deepcopy(report_data)
        fallback['labels'] = get_report_labels('en', for_pdf=for_pdf)
        fallback['language'] = 'en'
        fallback['translation_error'] = str(e)
        return fallback


# Re-export key translation functions for modular use
__all__ = [
    'LANGUAGES',
    'SUPPORTED_LANGUAGES',
    'translate_report',
    'translate_report_data',
    'translate_text',
    'get_report_labels',
    'shape_urdu_for_pdf',
    'is_supported_language',
    'get_language_name',
    'is_rtl'
]
