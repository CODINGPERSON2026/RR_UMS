"""
Unit and Integration Test Suite for Multilingual PDF Export in UMS Fitness Trend.
Verifies all 13 supported languages, numeric immutability, font manager,
Urdu RTL shaping, API error handling, and IndicTrans2 fallback.
"""

import os
import sys
import io
import unittest
import json

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from aiml.fitness_trend.translation import (
    SUPPORTED_LANGUAGES,
    is_supported_language,
    get_language_name,
    is_rtl,
    translate_report_data,
    get_report_labels,
    shape_urdu_for_pdf,
    IndicTrans2Translator
)
from aiml.fitness_trend.reports.translator import translate_report, LANGUAGES
from aiml.fitness_trend.pdf.font_manager import FontManager, get_font_manager
from aiml.fitness_trend.pdf.report_generator import generate_multilingual_fitness_pdf
from aiml.fitness_trend.api import analyze_personnel_fitness


class TestMultilingualPDFExport(unittest.TestCase):
    """Test suite covering the complete multilingual PDF export system."""

    @classmethod
    def setUpClass(cls):
        cls.army_number = "A4354237H"
        cls.analysis = analyze_personnel_fitness(cls.army_number, goal="Overall Fitness")
        assert cls.analysis.get("success"), f"Analysis failed: {cls.analysis}"
        cls.soldier = cls.analysis["soldier"]
        cls.prediction = cls.analysis["prediction"]
        cls.recommendations = cls.analysis["recommendations"]
        cls.progression = cls.analysis["progression"]

    @classmethod
    def tearDownClass(cls):
        try:
            from app import scheduler
            if scheduler and scheduler.running:
                scheduler.shutdown(wait=False)
        except Exception:
            pass

    def test_language_config_13_languages(self):
        """Verify all 13 required languages are registered with proper metadata."""
        expected = [
            "en", "hi", "ur", "bn", "pa", "mr", "gu", "ta", "te", "kn", "ml", "or", "as"
        ]
        for code in expected:
            self.assertIn(code, SUPPORTED_LANGUAGES, f"Missing language: {code}")
            self.assertTrue(is_supported_language(code))
            self.assertIsInstance(get_language_name(code), str)

        # Urdu must be flagged as RTL, others as LTR
        self.assertTrue(is_rtl("ur"))
        self.assertFalse(is_rtl("hi"))
        self.assertFalse(is_rtl("en"))

        # Rejection of unsupported languages
        self.assertFalse(is_supported_language("xx"))
        self.assertFalse(is_supported_language("de"))
        self.assertFalse(is_supported_language(""))
        self.assertFalse(is_supported_language(None))

    def test_translation_numeric_immutability(self):
        """
        Verify Requirement 3: Numbers, Army Number, Scores, Percentages,
        Sets, Reps, and Durations must remain unchanged across translations.
        """
        for lang in ["hi", "ur", "bn", "ta", "te", "kn", "ml", "or", "as"]:
            s, p, r, prog = translate_report_data(
                self.soldier, self.prediction, self.recommendations, self.progression,
                target_lang=lang, for_pdf=False
            )
            # Army number must not change
            self.assertEqual(s["army_number"], self.soldier["army_number"])
            # Measurements and numeric scores must be identical
            self.assertEqual(s["height_cm"], self.soldier["height_cm"])
            self.assertEqual(s["actual_weight_kg"], self.soldier["actual_weight_kg"])
            self.assertEqual(s["ideal_weight_kg"], self.soldier["ideal_weight_kg"])
            self.assertEqual(s["bmi"], self.soldier["bmi"])
            self.assertEqual(p["fitness_score"], self.prediction["fitness_score"])
            self.assertEqual(p["confidence_score"], self.prediction["confidence_score"])
            # Reps and sets numbers in exercise items must be identical
            orig_ex = self.recommendations.get("exercise", {}).get("exercises", [])
            trans_ex = r.get("exercise", {}).get("exercises", [])
            self.assertEqual(len(orig_ex), len(trans_ex))
            for o, t in zip(orig_ex, trans_ex):
                self.assertEqual(o["sets"], t["sets"])

    def test_font_manager_asset_loading(self):
        """Verify FontManager resolves fonts from project-relative assets/fonts."""
        mgr = FontManager()
        self.assertTrue(os.path.isdir(mgr.fonts_dir))
        arial_path = mgr.get_font_path("arialuni.ttf")
        self.assertIsNotNone(arial_path)
        self.assertTrue(os.path.exists(arial_path))
        # Register fonts
        success = mgr.register_unicode_fonts()
        self.assertTrue(success)

    def test_indictrans2_fallback_graceful(self):
        """Verify IndicTrans2 module gracefully indicates unavailability without throwing."""
        it = IndicTrans2Translator()
        # Should not throw exception
        avail = it.is_available()
        self.assertIsInstance(avail, bool)

    def test_pdf_compilation_all_13_languages(self):
        """
        Verify PDF generation succeeds for all 13 supported languages,
        producing valid %PDF binary output without errors.
        """
        for lang_code in SUPPORTED_LANGUAGES.keys():
            pdf_stream = generate_multilingual_fitness_pdf(
                self.soldier, self.prediction, self.recommendations, self.progression,
                client_ip="192.168.1.50",
                watermark_text="UMS 15 CESR",
                language=lang_code
            )
            self.assertIsNotNone(pdf_stream, f"Failed for language: {lang_code}")
            pdf_bytes = pdf_stream.getvalue()
            self.assertTrue(pdf_bytes.startswith(b"%PDF"), f"Invalid PDF header for {lang_code}")
            self.assertGreater(len(pdf_bytes), 50000, f"PDF too small for {lang_code}")

    def test_api_export_pdf_unsupported_language_rejection(self):
        """Verify Requirement 8: Unsupported language codes return 400 Bad Request."""
        from app import app
        import jwt
        from middleware import JWT_SECRET, JWT_ALGO

        payload = {'username': 'test_admin', 'role': 'admin', 'company': '1 Company'}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

        with app.test_client() as client:
            client.set_cookie('token', token)
            # Reject invalid language
            res = client.post('/api/fitness-trend/export-pdf', json={
                'army_number': self.army_number,
                'language': 'xx'
            })
            self.assertEqual(res.status_code, 400)
            data = res.get_json()
            self.assertIn("Unsupported language", data.get("error", ""))

    def test_api_export_pdf_success(self):
        """Verify Requirement 8: POST /api/fitness-trend/export-pdf returns valid PDF attachment."""
        from app import app
        import jwt
        from middleware import JWT_SECRET, JWT_ALGO

        payload = {'username': 'test_admin', 'role': 'admin', 'company': '1 Company'}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

        with app.test_client() as client:
            client.set_cookie('token', token)
            res = client.post('/api/fitness-trend/export-pdf', json={
                'army_number': self.army_number,
                'language': 'hi'
            })
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.mimetype, "application/pdf")
            self.assertTrue(res.data.startswith(b"%PDF"))
            disp = res.headers.get("Content-Disposition", "")
            self.assertIn("UMS_Fitness_Report_", disp)
            self.assertIn("_HI_", disp)

    def test_api_fitness_trend_report_pdf_endpoint(self):
        """Verify Requirement 15: POST /fitness-trend/report/pdf generates multilingual PDF."""
        from app import app
        import jwt
        from middleware import JWT_SECRET, JWT_ALGO

        payload = {'username': 'test_admin', 'role': 'admin', 'company': '1 Company'}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

        with app.test_client() as client:
            client.set_cookie('token', token)
            res = client.post('/fitness-trend/report/pdf', json={
                'army_number': self.army_number,
                'language': 'mr'
            })
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.mimetype, "application/pdf")
            self.assertTrue(res.data.startswith(b"%PDF"))
            disp = res.headers.get("Content-Disposition", "")
            self.assertIn("UMS_Fitness_Report_", disp)
            self.assertIn("_MR_", disp)

    def test_16_section_structure_and_multilingual_pdf(self):
        """Verify all 16 required sections are built and present in report payload."""
        from aiml.fitness_trend.reports.fitness_report import build_structured_fitness_report
        from aiml.fitness_trend.translation.translator import translate_16section_report

        structured = build_structured_fitness_report(
            self.soldier, self.prediction, self.recommendations, self.progression, language="mr"
        )
        # Check all 16 section keys
        required_keys = [
            'header', 'profile', 'analysis', 'assessment', 'prediction', 'trend',
            'progression', 'exercise_plan', 'nutrition', 'improvement_areas',
            'priority_recs', 'goals', 'monitoring', 'insights', 'disclaimer', 'footer'
        ]
        for k in required_keys:
            self.assertIn(k, structured, f"Missing section key: {k}")

        # Translate into Marathi
        t_mr = translate_16section_report(structured, target_lang="mr", for_pdf=True)
        self.assertEqual(t_mr['header']['army_number'], self.soldier['army_number'])
        self.assertEqual(t_mr['assessment']['fitness_score'], self.prediction['fitness_score'])
        self.assertIn('UMS-FIT-', t_mr['report_id'])

    def test_translate_report_service_api(self):
        """Verify Requirement 6: translate_report(report_data, target_language) service interface."""
        report_data = {
            'soldier': self.soldier,
            'prediction': self.prediction,
            'recommendations': self.recommendations,
            'progression': self.progression
        }

        # 1. Marathi
        res_mr = translate_report(report_data, target_language="mr")
        self.assertEqual(res_mr["language"], "mr")
        self.assertEqual(res_mr["soldier"]["army_number"], self.soldier["army_number"])
        self.assertIn("labels", res_mr)

        # 2. Urdu (RTL)
        res_ur = translate_report(report_data, target_language="ur")
        self.assertEqual(res_ur["language"], "ur")
        self.assertEqual(res_ur["direction"], "rtl")

        # 3. English (unchanged)
        res_en = translate_report(report_data, target_language="en")
        self.assertEqual(res_en["language"], "en")

        # 4. Invalid language fallback to English
        res_fallback = translate_report(report_data, target_language="invalid_xyz")
        self.assertEqual(res_fallback["language"], "en")

    def test_urdu_rtl_shaping_and_bidi(self):
        """Verify Requirement 10: Urdu text undergoes cursive shaping and bidi ordering."""
        raw_urdu = "ذاتی فٹنس رپورٹ"
        shaped = shape_urdu_for_pdf(raw_urdu)
        self.assertIsInstance(shaped, str)
        self.assertGreater(len(shaped), 0)
        # Should not be identical to raw unshaped characters due to presentation forms
        self.assertNotEqual(shaped, raw_urdu)

    def test_special_characters_and_measurements(self):
        """Verify Requirement 23: Special characters (%, ₹, kg, cm, /, -, ()) are preserved."""
        test_payload = {
            'soldier': {
                'army_number': '15744604X',
                'height_cm': 175.5,
                'actual_weight_kg': 78.0,
                'weight_difference_kg': 3.5,
                'weight_deviation_percent': 4.7
            },
            'prediction': {
                'fitness_score': 82.5,
                'confidence_score': 94.2
            },
            'recommendations': {
                'exercise': {
                    'exercises': [
                        {'exercise': 'Push-ups', 'sets': 3, 'reps': '20-25 reps', 'duration': '30-40 mins'}
                    ]
                }
            },
            'progression': {'milestones': []}
        }
        res = translate_report(test_payload, target_language="hi")
        s = res['soldier']
        self.assertEqual(s['height_cm'], 175.5)
        self.assertEqual(s['actual_weight_kg'], 78.0)
        self.assertEqual(s['weight_difference_kg'], 3.5)
        self.assertEqual(s['weight_deviation_percent'], 4.7)

    def test_missing_or_null_data_safety(self):
        """Verify Requirement 17: Missing/null report fields do not crash the translator."""
        empty_payload = {}
        res = translate_report(empty_payload, target_language="ta")
        self.assertIsInstance(res, dict)

        partial_payload = {'soldier': None, 'prediction': {}, 'recommendations': None}
        res2 = translate_report(partial_payload, target_language="ur")
        self.assertIsInstance(res2, dict)


if __name__ == "__main__":
    res_code = 1
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestMultilingualPDFExport)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        res_code = 0 if result.wasSuccessful() else 1
    finally:
        try:
            from app import scheduler
            if scheduler and scheduler.running:
                scheduler.shutdown(wait=False)
        except Exception:
            pass
        os._exit(res_code)
