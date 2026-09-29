# UMS AI Company Readiness (AIML) Module

## 1. Feature Purpose
The **AI Company Readiness** module provides transparent, auditable operational readiness analysis, gap identification, soldier-level drill-down, forward-looking machine learning predictions, and explainable command recommendations for the Unit Management System (UMS).

The feature operates exclusively for three company formations:
* **HQ COY** (Headquarters Company)
* **COMN COY** (Communication Company)
* **3 COY** (3 Company)

---

## 2. Database Dependencies
* **Engine**: MySQL 8.0+ / MariaDB.
* **Driver**: `mysql-connector-python` using connection pooling via [`db_config.py`](file:///e:/UMS-LATEST/db_config.py).
* **ORM / Querying**: Parameterized direct SQL queries with `%s` escaping to prevent SQL injection.

---

## 3. Existing Tables Used
The module reuses the following core database tables without creating duplicate entities:
* `personnel` (476 rows): Formations, trades, ranks, civil qualifications, lacking qualifications, BPET/PPT gradings, medical category, restrictions, absence flags (`onleave_status`, `detachment_status`, `td_status`, `oncourse_status`).
* `courses` (54 rows): Military training course attendance, institutes, and gradings.
* `weight_info` (479 rows): Physical category assessments, SHAPE-1 status, temporary/permanent LMC classifications.
* `leave_details` / `leave_history` (909 rows): Leave duration records.
* `ai_company_requirements` (32 rows): Authorized baseline requirements for Strength, Trades, Qualifications, and Military Courses across the 3 companies.

---

## 4. New Tables
To support periodic trend auditing and genuine ML model training without duplicating soldier records:
* **`ai_company_readiness_history`**:
  * Records periodic snapshots of calculated readiness dimensions (`strength_score`, `availability_score`, `trade_score`, `qualification_score`, `course_score`, `fitness_score`, `medical_score`, `overall_readiness`, `main_gap_type`, `gap_count`).

---

## 5. Readiness Calculation (Deterministic Engine)
Readiness scores are **100% deterministic and auditable**, calculated directly from the database. The system never labels deterministic counts as Machine Learning.

### Dimensions & Configurable Default Weights:
$$\text{Overall Readiness} = \sum_{i=1}^{7} (\text{Score}_i \times \text{Weight}_i)$$

1. **Strength (Weight: 20%)**: $\min\left(100, \frac{\text{Actual Personnel}}{\text{Required Personnel}} \times 100\right)$
2. **Availability (Weight: 20%)**: $\frac{\text{Actual} - (\text{Leave} + \text{Detachment} + \text{TD} + \text{Courses Away})}{\text{Actual}} \times 100$
3. **Trade (Weight: 15%)**: Weighted fulfillment across all authorized trade quotas (TTC, LMN, EFS, OCC, CLK SD, etc.).
4. **Qualification (Weight: 15%)**: Compliance ratio for mandatory civil educational standards (12th, Technical Diploma, Graduation).
5. **Course (Weight: 10%)**: Compliance ratio for specialization courses (TTC Class-1, Class-1, Signals Course).
6. **Fitness (Weight: 10%)**: BPET and PPT pass ratio from `personnel.bpet_grading` and `ppt_grading`.
7. **Medical (Weight: 10%)**: SHAPE-1 compliance vs Low Medical Category (LMC) ratios.

---

## 6. Machine Learning Target
* **Target**: Future Readiness Degradation Risk (Binary Classification).
  * Class 1: Formation faces high probability of readiness degradation ($\ge 5\%$ drop or score $< 80\%$) in the upcoming 30/60-day operational horizon.
  * Class 0: Formation remains within stable operational parameters.

---

## 7. ML Features (19 Time-Aligned Features)
All features are strictly evaluated at observation moment $T$ with zero future data leakage:
* Formation one-hot indicators (`company_hq`, `company_comn`, `company_3coy`).
* Strength and availability rates (`strength_ratio`, `leave_rate`, `detachment_rate`, `td_rate`, `course_away_rate`, `availability_rate`).
* Compliance ratios (`trade_fulfillment_ratio`, `qualification_fulfillment_ratio`, `course_fulfillment_ratio`).
* Physical & medical health (`shape1_ratio`, `lmc_ratio`, `bpet_pass_ratio`, `ppt_pass_ratio`).
* Lead vulnerability indicator (`upcoming_recat_ratio`: upcoming medical recategorizations due in $\le 60$ days).

---

## 8. Models Used & Comparison Framework
The training pipeline compares:
1. **Logistic Regression** (with feature scaling) as an explainable linear baseline.
2. **Random Forest Classifier** (ensemble decision trees).
3. **Gradient Boosting Classifier** (gradient boosted trees).

---

## 9. Evaluation Metrics
* **Classification**: Accuracy, Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix.
* Split: 80% Training / 20% Testing with stratification.

---

## 10. Training Process
* Pipeline: Extract features $\rightarrow$ Impute/Clean $\rightarrow$ Scale $\rightarrow$ Train/Test Split $\rightarrow$ Multi-Model Cross-Validation $\rightarrow$ Evaluate on Test Set $\rightarrow$ Export Artifacts to `models/`.
* **Minimum Threshold**: Requires at least 50 genuine historical snapshot records before training triggers. Synthetic fake data is strictly prohibited.

---

## 11. Prediction Process & Anti-Fabrication Standard
* When model artifacts exist: Loads model and scaler, computes class prediction, calibrated probability confidence, and extracts feature importances.
* When training data is insufficient: Transparently returns status code `UNDER_DEVELOPMENT` with notice:
  > *"ML prediction is under development because sufficient historical training data is not yet available."*
  Never outputs fake confidence or fabricated risk scores.

---

## 12. API Routes
* `GET /ai-company-readiness`: Main 3-company dashboard.
* `GET /ai-company-readiness/company/<company>`: Company dimension breakdown and gaps.
* `GET /ai-company-readiness/company/<company>/gaps`: Gaps listing and drill-down page.
* `GET /ai-company-readiness/company/<company>/prediction`: ML prediction and explainability view.
* `GET /ai-company-readiness/api/dashboard`: REST endpoint for dashboard data.
* `GET /ai-company-readiness/api/company/<company>`: REST endpoint for company data.
* `GET /ai-company-readiness/company/<company>/personnel`: AJAX endpoint for contributing personnel.
* `POST /ai-company-readiness/api/snapshot`: Records current readiness snapshot into history table.

---

## 13. UI Structure
* Adheres to UMS CSS theme variables (`--primary-color`, `--card-bg-solid`, `--text-primary`, `--border-color`).
* Dark, Light, Ocean, Sunset, and Purple theme compatible.
* Responsive desktop rail navigation and mobile bottom nav.
* Interactive AJAX modal for personnel drill-down with live search.

---

## 14. Known Limitations
1. Historical snapshots are initially starting from the current operational baseline; predictive models require continuous accumulation of snapshots over operational cycles.
2. Soldier civil qualifications in legacy records contain free-text variations which are mapped via keyword rules.

---

## 15. Future Improvements
1. Automated daily cron job triggering `api_save_snapshot` to automatically build long-term multi-season training data.
2. Integration of seasonal leave patterns (harvest/monsoon season leave surges) into the predictive time-series feature extractor.
3. Automated drafting of posting requisition signals when critical trade deficits exceed command thresholds.
