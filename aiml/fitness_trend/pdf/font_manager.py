"""
Font Management Module for Multilingual PDF Generation.
Registers Unicode TrueType fonts (ArialUnicode, Nirmala) from project assets/fonts.
Uses relative paths and provides safe fallbacks.
"""

import os
import logging
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger("fitness_trend.pdf.font_manager")

_REGISTERED_FONTS = set()


class FontManager:
    """
    Manages loading, registration, and assignment of Unicode fonts
    for ReportLab and xhtml2pdf across all 13 supported languages.
    """
    def __init__(self, assets_dir=None):
        if assets_dir is None:
            # Resolve relative to this module's location: ../assets/fonts
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.fonts_dir = os.path.join(base_dir, "assets", "fonts")
        else:
            self.fonts_dir = assets_dir

        self.font_mappings = {
            "arialunicode": "arialuni.ttf",
            "nirmala": "nirmala.ttf",
            "nirmala-bold": "nirmalab.ttf"
        }

    def get_font_path(self, filename):
        """
        Resolves font path using project-relative asset directory first,
        falling back to system fonts if not found in project assets.
        """
        local_path = os.path.join(self.fonts_dir, filename)
        if os.path.exists(local_path):
            return local_path

        # Windows system font fallback
        win_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", filename)
        if os.path.exists(win_path):
            return win_path

        # Linux / container system font fallbacks
        linux_paths = [
            f"/usr/share/fonts/truetype/{filename}",
            f"/usr/share/fonts/opentype/{filename}",
            f"/usr/local/share/fonts/{filename}"
        ]
        for lp in linux_paths:
            if os.path.exists(lp):
                return lp

        return None

    def register_unicode_fonts(self):
        """
        Registers Unicode TrueType fonts with ReportLab and xhtml2pdf.
        Ensures idempotency so fonts are only registered once.
        """
        global _REGISTERED_FONTS

        # 1. Register Arial Unicode MS (Primary pan-Indic & Urdu Unicode font)
        if "ArialUnicode" not in _REGISTERED_FONTS:
            arial_path = self.get_font_path("arialuni.ttf")
            if arial_path:
                try:
                    pdfmetrics.registerFont(TTFont("ArialUnicode", arial_path))
                    try:
                        import xhtml2pdf.default as default_mod
                        default_mod.DEFAULT_FONT['arialunicode'] = 'ArialUnicode'
                    except Exception:
                        pass
                    _REGISTERED_FONTS.add("ArialUnicode")
                    logger.info(f"Registered ArialUnicode from {arial_path}")
                except Exception as e:
                    logger.error(f"Failed to register ArialUnicode font ({arial_path}): {e}")
            else:
                logger.warning(f"ArialUnicode font not found in {self.fonts_dir} or system directories.")

        # 2. Register Nirmala UI (Pan-Indic scripts)
        if "Nirmala" not in _REGISTERED_FONTS:
            nirmala_path = self.get_font_path("nirmala.ttf")
            if nirmala_path:
                try:
                    pdfmetrics.registerFont(TTFont("Nirmala", nirmala_path))
                    try:
                        import xhtml2pdf.default as default_mod
                        default_mod.DEFAULT_FONT['nirmala'] = 'Nirmala'
                    except Exception:
                        pass
                    _REGISTERED_FONTS.add("Nirmala")
                    logger.info(f"Registered Nirmala font from {nirmala_path}")
                except Exception as e:
                    logger.error(f"Failed to register Nirmala font ({nirmala_path}): {e}")

        # 3. Register Nirmala Bold
        if "Nirmala-Bold" not in _REGISTERED_FONTS:
            nirmalab_path = self.get_font_path("nirmalab.ttf")
            if nirmalab_path:
                try:
                    pdfmetrics.registerFont(TTFont("Nirmala-Bold", nirmalab_path))
                    try:
                        import xhtml2pdf.default as default_mod
                        default_mod.DEFAULT_FONT['nirmala-bold'] = 'Nirmala-Bold'
                    except Exception:
                        pass
                    _REGISTERED_FONTS.add("Nirmala-Bold")
                    logger.info(f"Registered Nirmala-Bold font from {nirmalab_path}")
                except Exception as e:
                    logger.error(f"Failed to register Nirmala-Bold font: {e}")

        return len(_REGISTERED_FONTS) > 0

    def get_font_family_for_language(self, lang_code="en"):
        """
        Returns the CSS font-family string suitable for the given language.
        """
        self.register_unicode_fonts()
        if not lang_code or lang_code == "en":
            return "Helvetica, Arial, sans-serif"

        # Non-English languages require Unicode font
        return "arialunicode, nirmala, Arial, sans-serif"


# Global singleton font manager instance
_FONT_MANAGER = None

def get_font_manager():
    global _FONT_MANAGER
    if _FONT_MANAGER is None:
        _FONT_MANAGER = FontManager()
    return _FONT_MANAGER
