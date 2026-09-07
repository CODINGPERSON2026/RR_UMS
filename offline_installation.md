# UMS Offline Multilingual AI Fitness Report - Setup & Deployment Guide

## 1. Executive Summary

The Unit Management System (UMS) AI/ML Individual Fitness Prediction & Personalized Fitness Report includes an **Offline Multilingual PDF Export Engine**. 

> [!IMPORTANT]
> **Zero Runtime Internet Required**:
> Internet access is strictly restricted to the initial development / package caching phase. During runtime operations, fitness score prediction, multilingual translation, Urdu cursive shaping, and PDF document generation operate **100% locally and offline**.

---

## 2. Server Architecture Overview

An offline UMS production server is structured as follows:

```text
UMS SERVER (Air-Gapped / Local Network)
│
├── Fitness AI Models
│   ├── aiml/fitness_trend/models/fitness_classifier_v1.joblib
│   ├── aiml/fitness_trend/models/fitness_regressor_v1.joblib
│   ├── aiml/fitness_trend/models/preprocessor_v1.joblib
│   └── aiml/fitness_trend/models/metadata_v1.json
│
├── Offline Translation Engine
│   ├── aiml/fitness_trend/translation/
│   │   ├── indictrans2_translator.py       # IndicTrans2 local model hook
│   │   ├── language_config.py             # Supported language registry & direction
│   │   └── translator.py                  # High-speed memory vocabulary & regex engine
│   └── aiml/fitness_trend/reports/
│       └── translator.py                  # Standardized translate_report() interface
│
├── Unicode & Regional TrueType Fonts
│   ├── aiml/fitness_trend/assets/fonts/
│   │   ├── arialuni.ttf                   # Arial Unicode MS (Pan-Indic & Arabic/Urdu)
│   │   ├── nirmala.ttf                    # Nirmala UI Regular (Devanagari, Tamil, etc.)
│   │   └── nirmalab.ttf                   # Nirmala UI Bold
│   └── System Fallbacks: C:\Windows\Fonts\ (or /usr/share/fonts/ on Linux)
│
└── Flask Application & Blueprints
    ├── app.py                             # Root endpoints (/fitness-trend/report/pdf)
    └── aiml/fitness_trend/routes.py       # REST APIs & PDF streaming controllers
```

---

## 3. Supported Languages

The system centrally defines and supports the following languages:

| Code | Language | Native Name | Script | Direction | Default Font Stack |
|:---:|:---|:---|:---|:---:|:---|
| `en` | English | English | Latin | LTR | Helvetica, Arial, sans-serif |
| `hi` | Hindi | हिन्दी | Devanagari | LTR | Nirmala, ArialUnicode |
| `ur` | Urdu | اردو | Perso-Arabic | **RTL** | ArialUnicode (Arabic reshaped) |
| `mr` | Marathi | मराठी | Devanagari | LTR | Nirmala, ArialUnicode |
| `ta` | Tamil | தமிழ் | Tamil | LTR | Nirmala, ArialUnicode |
| `bn` | Bengali | বাংলা | Bengali | LTR | Nirmala, ArialUnicode |
| `pa` | Punjabi | ਪੰਜਾਬੀ | Gurmukhi | LTR | Nirmala, ArialUnicode |
| `gu` | Gujarati | ગુજરાતી | Gujarati | LTR | Nirmala, ArialUnicode |
| `te` | Telugu | తెలుగు | Telugu | LTR | Nirmala, ArialUnicode |
| `kn` | Kannada | ಕನ್ನಡ | Kannada | LTR | Nirmala, ArialUnicode |
| `ml` | Malayalam | മലയാളം | Malayalam | LTR | Nirmala, ArialUnicode |
| `or` | Odia | ଓଡ଼ିଆ | Odia | LTR | Nirmala, ArialUnicode |
| `as` | Assamese | অসমীয়া | Bengali-Assamese | LTR | Nirmala, ArialUnicode |

---

## 4. Phase 1: Initial Acquisition (Internet Required Once)

Run these steps once on a machine connected to the Internet to bundle wheels, packages, and assets:

### Step 4.1: Download Python Wheel Dependencies
```powershell
# Create offline wheel directory
New-Item -ItemType Directory -Force -Path .\offline_packages

# Download all required dependencies as wheel binaries
python -m pip download -r requirements.txt -d .\offline_packages

# Optional: AI4Bharat IndicTrans2 PyTorch stack (if running 200M dense transformer locally)
python -m pip download torch transformers sentencepiece sacremoses -d .\offline_packages
```

### Step 4.2: Acquire Unicode TrueType Fonts
Ensure the project's asset directory contains the required font files:
`aiml/fitness_trend/assets/fonts/`
- `arialuni.ttf` (Arial Unicode MS, ~23 MB)
- `nirmala.ttf` (Nirmala UI Regular, ~1.5 MB)
- `nirmalab.ttf` (Nirmala UI Bold, ~1.5 MB)

*(On Windows environments, these can also be copied directly from `C:\Windows\Fonts\`)*.

---

## 5. Phase 2: Offline Target Machine Installation (No Internet)

On the secure, air-gapped UMS production server:

### Step 5.1: Install Python Virtual Environment from Local Wheel Cache
```powershell
# Create virtual environment
python -m venv umsvenv

# Install all dependencies without internet access
.\umsvenv\Scripts\python.exe -m pip install --no-index --find-links=.\offline_packages -r requirements.txt
```

### Step 5.2: Verification of Installed Libraries
Ensure the following offline components are functional:
```powershell
.\umsvenv\Scripts\python.exe -c "
import xhtml2pdf, reportlab, pypdf, arabic_reshaper, bidi
print('All offline PDF and RTL packages loaded successfully.')
"
```

---

## 6. Runtime PDF Generation & 16-Section Structure

The PDF report generation engine strictly organizes and renders **16 structured military report sections**:

1. **Report Header / Cover**: Unit crests (15 CESR and 15 Corps), regiment title, soldier overview bar, and unique Report ID (`UMS-FIT-<Date>-<ArmyNo>`).
2. **Personal & Fitness Profile**: Official military dossier (Army No, Name, Rank, Trade, Company, Section, Age, Service Years, Medical Category).
3. **Current Fitness Analysis**: Height, Weight, Ideal Benchmark, Variance, BMI, BPET/PPT grades, Sports, Physical Activity Level, and AI condition summary.
4. **AI Fitness Assessment**: AI Readiness Score (`/ 100 PTS`), Category Pill, Confidence %, and Tactical Readiness Tier.
5. **AI Fitness Prediction**: Model algorithm, version, predicted status, Key Strengths, and Primary Action Areas.
6. **Weight / Fitness Trend**: Baseline vs target benchmark comparison table with localized status.
7. **Fitness Progression**: 30, 60, and 90-day milestone projections.
8. **Personalized Exercise Plan**: Drill routines, sets, repetitions, duration, and weekly frequency.
9. **Personalized Nutrition Recommendations**: Caloric target (`kcal/day`), hydration target (`Liters/day`), macronutrient split, recommended foods, and foods to limit.
10. **Areas for Improvement**: Specific tactical focus areas.
11. **AI Personalized Recommendations**: Priority 1, 2, and 3 structured breakdown.
12. **Fitness Goals**: Short-term (1-4w), Medium-term (4-8w), and Long-term (8-12w) goals.
13. **Progress Monitoring**: Standardized monitoring schedule table (Weight, BMI, BPET, PPT with review frequency).
14. **AI Fitness Insights**: High-level analytical overview and recommended conditioning focus.
15. **Important Note / Disclaimer**: Official medical and military conditioning advisory notice.
16. **Official Record Authentication & Footer**: Authentication signature blocks (Unit PT Instructor, Regimental Medical Officer, Officer Commanding), confidential timestamp, and ReportLab diagonal watermark.

### UI Workflow: Preview, Generate, View & Download
In the UMS Fitness Trend interface:
- **`[ Preview Report ]`**: Instantly launches the printable HTML report view in a dedicated tab (`/fitness/report/preview/<army_number>?lang=<lang>&goal=<goal>`) matching the exact 16 sections and active language.
- **`[ Generate PDF ]`**: Triggers `/api/fitness-trend/export-pdf`, compiles the PDF with official watermarking, and triggers the automatic download.
- **`[ View PDF ]`**: Opens the compiled PDF directly in the browser's PDF viewer.
- **`[ Download PDF ]`**: Allows re-saving the file with the standardized military filename:
  ```text
  UMS_Fitness_Report_<SafeArmyNo>_<LANG>_<YYYYMMDD>.pdf
  Example: UMS_Fitness_Report_A4354237H_MR_20260906.pdf
  ```

---

## 7. Urdu RTL & Bidirectional Shaping Details

Urdu requires specialized handling due to cursive letter connection and Right-to-Left (RTL) reading order:
1. **Letter Shaping**: Characters take different positional forms (isolated, initial, medial, final). We utilize `arabic-reshaper` to bind cursive Urdu characters correctly.
2. **Bi-Directional Ordering**: `python-bidi` reverses visual layout for LTR PDF canvas rendering engines while preserving numeric ordering (e.g., `82%`, `175 cm`).
3. **Template Directionality**: `pdf_template.html` automatically applies `direction: rtl; text-align: right;` and aligns table headers to the right when `is_rtl` is true.

---

## 8. How to Add a New Language

To register a new Indian language (e.g., Maithili `mai`):
1. **Register Language in Configuration**:
   In `aiml/fitness_trend/translation/language_config.py`, add the entry to `SUPPORTED_LANGUAGES`:
   ```python
   "mai": {
       "name": "Maithili",
       "native_name": "मैथिली",
       "direction": "ltr",
       "indictrans_code": "mai_Deva"
   }
   ```
2. **Add Military Vocabulary**:
   In `aiml/fitness_trend/translation/translator.py`, populate the `VOCABULARY['mai']` dictionary with core report terms.
3. **Verify Font Coverage**:
   Ensure `Nirmala.ttf` or `ArialUnicode` covers the target script.
4. **Update Central List**:
   In `aiml/fitness_trend/reports/translator.py`, append `"mai": "Maithili"` to `LANGUAGES`.

---

## 9. Troubleshooting & FAQ

### Q1: The PDF shows square boxes (`□□□`) instead of regional characters.
- **Cause**: Unicode font is missing or not registered with ReportLab.
- **Fix**: Verify that `aiml/fitness_trend/assets/fonts/arialuni.ttf` and `nirmala.ttf` exist. The `FontManager` will automatically register and bind them.

### Q2: Urdu text appears disjointed or reversed.
- **Cause**: Urdu text was rendered without cursive shaping.
- **Fix**: Verify `arabic-reshaper==3.0.0` and `python-bidi==0.6.7` are installed in `umsvenv`. Ensure `for_pdf=True` is passed to the translator when generating PDF payloads.

### Q3: An unrecognized language code was passed to the API.
- **Behavior**: The backend automatically logs a warning and falls back safely to English (`"en"`), generating an English PDF without crashing.

### Q4: Does the server require PyTorch / GPU to run?
- **Answer**: **No.** The system includes a high-performance offline vocabulary and dynamic regex translation engine that runs instantaneously on CPU with minimal memory footprint. If PyTorch and IndicTrans2 model weights are present, the system automatically detects and leverages them; otherwise, it operates smoothly using the built-in military translation engine.