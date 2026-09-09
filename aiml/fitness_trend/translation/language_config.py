"""
Centralized Language Configuration for Multilingual Fitness Reports.
Defines supported languages, reading direction (LTR/RTL), and translation metadata.
"""

SUPPORTED_LANGUAGES = {
    "en": {
        "name": "English",
        "native_name": "English",
        "direction": "ltr",
        "indictrans_code": "eng_Latn"
    },
    "hi": {
        "name": "Hindi",
        "native_name": "हिन्दी",
        "direction": "ltr",
        "indictrans_code": "hin_Deva"
    },
    "ur": {
        "name": "Urdu",
        "native_name": "اردو",
        "direction": "rtl",
        "indictrans_code": "urd_Arab"
    },
    "bn": {
        "name": "Bengali",
        "native_name": "বাংলা",
        "direction": "ltr",
        "indictrans_code": "ben_Beng"
    },
    "pa": {
        "name": "Punjabi",
        "native_name": "ਪੰਜਾਬੀ",
        "direction": "ltr",
        "indictrans_code": "pan_Guru"
    },
    "mr": {
        "name": "Marathi",
        "native_name": "मराठी",
        "direction": "ltr",
        "indictrans_code": "mar_Deva"
    },
    "gu": {
        "name": "Gujarati",
        "native_name": "ગુજરાતી",
        "direction": "ltr",
        "indictrans_code": "guj_Gujr"
    },
    "ta": {
        "name": "Tamil",
        "native_name": "தமிழ்",
        "direction": "ltr",
        "indictrans_code": "tam_Taml"
    },
    "te": {
        "name": "Telugu",
        "native_name": "తెలుగు",
        "direction": "ltr",
        "indictrans_code": "tel_Telu"
    },
    "kn": {
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "direction": "ltr",
        "indictrans_code": "kan_Knda"
    },
    "ml": {
        "name": "Malayalam",
        "native_name": "മലയാളം",
        "direction": "ltr",
        "indictrans_code": "mal_Mlym"
    },
    "or": {
        "name": "Odia",
        "native_name": "ଓଡ଼ିଆ",
        "direction": "ltr",
        "indictrans_code": "ory_Orya"
    },
    "as": {
        "name": "Assamese",
        "native_name": "অসমীয়া",
        "direction": "ltr",
        "indictrans_code": "asm_Beng"
    }
}

DEFAULT_LANGUAGE = "en"


def is_supported_language(lang_code):
    """Checks if a language code is in the supported languages configuration."""
    if not lang_code or not isinstance(lang_code, str):
        return False
    return lang_code.lower().strip() in SUPPORTED_LANGUAGES


def get_language_config(lang_code):
    """Returns configuration dictionary for the given language code, defaulting to English."""
    code = (lang_code or DEFAULT_LANGUAGE).lower().strip()
    return SUPPORTED_LANGUAGES.get(code, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE])


def get_language_name(lang_code):
    """Returns the English name of the language."""
    return get_language_config(lang_code).get("name", "English")


def is_rtl(lang_code):
    """Returns True if the language uses Right-to-Left writing direction."""
    return get_language_config(lang_code).get("direction") == "rtl"


def get_indictrans_code(lang_code):
    """Returns the IndicTrans2 language tag for the given language code."""
    return get_language_config(lang_code).get("indictrans_code", "eng_Latn")
