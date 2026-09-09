# -*- coding: utf-8 -*-
import os
import sys
import io

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from aiml.fitness_trend.api import analyze_personnel_fitness
from aiml.fitness_trend.reports.fitness_report import build_structured_fitness_report
from aiml.fitness_trend.translation.translator import (
    translate_16section_report,
    get_report_labels,
    translate_report_data
)
from aiml.fitness_trend.pdf.report_generator import generate_multilingual_fitness_pdf

def test_verification():
    print("=" * 60)
    print("RUNNING VERIFICATION: Fitness Report Translations & Unit Name")
    print("=" * 60)

    # 1. Analyze soldier
    army_no = "JC-394045P"
    analysis = analyze_personnel_fitness(army_no, goal="Overall Fitness")
    if not analysis.get("success"):
        print(f"Soldier {army_no} not found in DB, using fallback profile A4354237H...")
        army_no = "A4354237H"
        analysis = analyze_personnel_fitness(army_no, goal="Overall Fitness")

    assert analysis.get("success"), f"Analysis failed: {analysis}"
    soldier = analysis["soldier"]
    prediction = analysis["prediction"]
    recommendations = analysis["recommendations"]
    progression = analysis["progression"]
    print(f"Loaded soldier: {soldier.get('name')} ({soldier.get('army_number')})")

    # 2. Build structured report
    structured = build_structured_fitness_report(
        soldier_features=soldier,
        prediction_result=prediction,
        recommendations=recommendations,
        progression_data=progression,
        client_ip="127.0.0.1",
        language="ur"
    )

    # 3. Check header & footer unit titles
    print("\n--- Checking Header & Footer Titles ---")
    print("Structured header title:", structured["header"]["title"])
    print("Structured footer regiment:", structured["footer"]["regiment"])
    assert "15 CESR" not in structured["header"]["title"], "15 CESR still in header title!"
    assert "15 CORPS" not in structured["header"]["title"], "15 CORPS still in header title!"
    assert "15 CESR" not in structured["footer"]["regiment"], "15 CESR still in footer regiment!"
    assert "15 CORPS" not in structured["footer"]["regiment"], "15 CORPS still in footer regiment!"
    print("PASS: Header & Footer default titles are free of 15 CESR / 15 Corps.")

    # 4. Check Urdu Labels
    print("\n--- Checking Urdu Labels ---")
    ur_labels = get_report_labels("ur", for_pdf=False)
    print("ur unit_title:", ur_labels.get("unit_title"))
    print("ur recommended_nutrition:", ur_labels.get("recommended_nutrition"))
    print("ur limit_nutrition:", ur_labels.get("limit_nutrition"))
    print("ur dietary_guidelines_title:", ur_labels.get("dietary_guidelines_title"))
    
    assert "15" not in ur_labels.get("unit_title", ""), "15 found in ur unit_title!"
    assert "DO'S" not in ur_labels.get("recommended_nutrition", ""), "DO'S was not translated in Urdu!"
    assert "DON'TS" not in ur_labels.get("limit_nutrition", ""), "DON'TS was not translated in Urdu!"
    assert "Discipline" not in ur_labels.get("dietary_guidelines_title", ""), "Guidelines title was not translated!"
    print("PASS: Urdu labels successfully translated!")

    # 5. Check 16-section report translation in Urdu
    print("\n--- Checking 16-Section Urdu Translation ---")
    t_report = translate_16section_report(structured, target_lang="ur", for_pdf=False)
    
    nutrition = t_report.get("nutrition", {})
    rec_items = nutrition.get("recommended_items", [])
    limit_items = nutrition.get("limit_items", [])
    guidelines = nutrition.get("guidelines", [])

    print(f"Recommended items count: {len(rec_items)}")
    for i, item in enumerate(rec_items):
        print(f"  DO {i+1}: {item}")
        assert "poultry" not in item.lower(), f"English word 'poultry' found in DO'S: {item}"
        assert "lentils" not in item.lower(), f"English word 'lentils' found in DO'S: {item}"

    print(f"\nLimit items count: {len(limit_items)}")
    for i, item in enumerate(limit_items):
        print(f"  DON'T {i+1}: {item}")
        assert "deep-fried" not in item.lower(), f"English word 'deep-fried' found in DON'TS: {item}"
        assert "refined" not in item.lower(), f"English word 'refined' found in DON'TS: {item}"

    print(f"\nGuidelines count: {len(guidelines)}")
    for i, g in enumerate(guidelines):
        print(f"  Guideline {i+1}: {g}")
        assert "maintain" not in g.lower(), f"English word 'maintain' found in guidelines: {g}"
        assert "protein" not in g.lower(), f"English word 'protein' found in guidelines: {g}"

    print("PASS: DO'S, DON'TS, and Nutritional Guidelines successfully translated into Urdu!")

    # 6. Check Hindi translation as well
    print("\n--- Checking Hindi Translation ---")
    hi_report = translate_16section_report(structured, target_lang="hi", for_pdf=False)
    hi_labels = get_report_labels("hi", for_pdf=False)
    print("hi unit_title:", hi_labels.get("unit_title"))
    print("hi recommended_nutrition:", hi_labels.get("recommended_nutrition"))
    print("hi limit_nutrition:", hi_labels.get("limit_nutrition"))
    assert "DO'S" not in hi_labels.get("recommended_nutrition", "")
    assert "DON'TS" not in hi_labels.get("limit_nutrition", "")
    for item in hi_report["nutrition"]["recommended_items"]:
        assert "poultry" not in item.lower()
    print("PASS: Hindi translations verified successfully!")

    # 7. Generate full PDF with Urdu
    print("\n--- Generating Multilingual Urdu PDF ---")
    pdf_stream = generate_multilingual_fitness_pdf(
        soldier_features=soldier,
        prediction_result=prediction,
        recommendations=recommendations,
        progression_data=progression,
        client_ip="127.0.0.1",
        watermark_text="UNIT MANAGEMENT SYSTEM",
        language="ur"
    )
    assert pdf_stream is not None, "PDF stream generation returned None!"
    pdf_bytes = pdf_stream.getvalue()
    print(f"Generated PDF bytes size: {len(pdf_bytes)} bytes")
    assert pdf_bytes.startswith(b"%PDF"), "Invalid PDF binary stream"

    # Save to scratch directory for inspection
    out_pdf_path = os.path.join(PROJECT_ROOT, "scratch", "test_urdu_report_verified.pdf")
    with open(out_pdf_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Saved generated test PDF to: {out_pdf_path}")

    # 8. Inspect PDF text using pypdf
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(pdf_bytes))
    print(f"Total pages in PDF: {len(reader.pages)}")
    full_pdf_text = ""
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        full_pdf_text += text
    
    assert "15 CESR" not in full_pdf_text, "Found '15 CESR' in generated PDF text!"
    assert "15 CORPS" not in full_pdf_text, "Found '15 CORPS' in generated PDF text!"
    print("PASS: Zero occurrences of '15 CESR' or '15 CORPS' in the generated PDF!")

    print("\n" + "=" * 60)
    print("ALL VERIFICATION CHECKS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_verification()
