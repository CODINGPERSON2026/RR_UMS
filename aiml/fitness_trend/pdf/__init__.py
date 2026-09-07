"""
PDF Generation Module for UMS Fitness Trend.
Exposes multilingual PDF report generator and font manager.
"""

from .font_manager import FontManager, get_font_manager
from .report_generator import generate_multilingual_fitness_pdf

__all__ = [
    'FontManager',
    'get_font_manager',
    'generate_multilingual_fitness_pdf'
]
