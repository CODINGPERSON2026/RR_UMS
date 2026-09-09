"""
Translation Module for UMS Fitness Trend Multilingual Reports.
Exposes language configuration, IndicTrans2 wrapper, and master report translator.
"""

from .language_config import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    is_supported_language,
    get_language_config,
    get_language_name,
    is_rtl
)
from .translator import (
    translate_report_data,
    translate_16section_report,
    translate_text,
    get_report_labels,
    shape_urdu_for_pdf
)
from .indictrans2_translator import IndicTrans2Translator

__all__ = [
    'SUPPORTED_LANGUAGES',
    'DEFAULT_LANGUAGE',
    'is_supported_language',
    'get_language_config',
    'get_language_name',
    'is_rtl',
    'translate_report_data',
    'translate_16section_report',
    'translate_text',
    'get_report_labels',
    'shape_urdu_for_pdf',
    'IndicTrans2Translator'
]
