# AI NEW ARRIVAL RECOMMENDATION (Unit 15 CESR)

A production-grade, two-stage AI/ML recommendation engine for placement and appointment allocation of new joinees within Unit 15 CESR.

---

## 1. Feature Architecture

```
aiml/
└── ai_new_joinee_recommendation/
    ├── __init__.py               # Blueprint export
    ├── routes.py                 # REST APIs, RBAC guards (CO, Adjutant, 2IC), Decision pipeline
    ├── recommendation.py         # Two-stage inference pipeline & rule-based fresh joinee engine
    ├── preprocessing.py          # Data cleaning, feature extraction, military trade normalizer
    ├── training.py               # 70/30 Stratified Split, SMOTE on Train, RF vs XGBoost
    ├── evaluation.py             # Accuracy, Top-1/2/3 Accuracies, Confusion Matrix, Metrics
    ├── explainability.py         # SHAP TreeExplainer & Natural Language force translation
    ├── position_mapping.py       # Unit 15 CESR Company -> Section -> Position hierarchy master
    ├── model/                    # Model weights, feature names, metadata, evaluation reports
    ├── templates/                # Feature-specific templates (e.g. visualization.html)
    ├── static/                   # Assets
    └── README.md                 # Technical Documentation
```

---

## 2. Unit 15 CESR Organizational Hierarchy Master

The model and position ranking engine strictly adhere to the following hierarchy:

```
UNIT: 15 CESR
├── HQ Coy (HQ Company)
│   ├── QM: Ration NCO, Fresh NCO, Clothing NCO, MES NCO, SKT
│   ├── RHQ: O1, O2, O3, TRG Clerk, Clerk, Warrant Clerk, Part One Clerk, Dispatcher Clerk, A-Sigma Clerk, PA
│   ├── RP: Adm NCO, Strict Orderly, Runner, RP NCO, Guest Room NCO
│   ├── TM: TM
│   ├── MT: MT
│   ├── LRW: LRW
│   ├── CHQ: Buddy, Office, Mess Hav, All Tradesmen, JCO Mess Cdr
│   └── GENERAL DUTY: CHM, CQMH, RHM, GD
├── Comn Coy (COMN Company)
│   └── COMMUNICATION / TECHNICAL: Multimedia, IT, System, Radio RR, MCCS Exchange, Communication Clerk, Strip Clerk, ICN, NFS, Server
└── 3 Coy (3 Company)
    └── TECHNICAL / CORPS HQ: VC, Corps HQ, System, Branch
```

---

## 3. Two-Stage Recommendation Architecture

1. **Stage 1 (Company Recommendation)**:
   - Evaluates personnel military trade, multi-specialty indicators, rank seniority, service experience, and past posting histories.
   - Supervised ML model (`RandomForestClassifier` / `XGBClassifier`) predicts calibrated probability distribution across `HQ Coy`, `Comn Coy`, and `3 Coy`.
   - Generates SHAP explainability feature attributions and positive/negative forces.

2. **Stage 2 (Conditional Position Recommendation)**:
   - Evaluates positions **exclusively** within the predicted Company.
   - Computes compatibility score based on specialty affinity matrices, rank alignment, and past duty matching.
   - Ranks the primary appointment and top alternative appointments within that Company.

3. **Fresh Joinee Engine (0 Previous Postings)**:
   - For personnel with no previous postings, applies 100% rule-based mapping.
   - Labeled clearly as `"Fresh Joinee – Rule-Based Specialty/Position Mapping"`.

---

## 4. REST API Endpoints

| Method | Endpoint | Description | Auth Roles |
|---|---|---|---|
| `POST` | `/api/ai/company-recommendation/predict` | Generate real-time 2-stage recommendation | Logged In |
| `POST` | `/api/ai/company-recommendation/save-history` | Persist recommendation to MySQL DB | Logged In |
| `GET` | `/api/ai/company-recommendation/insights` | Paginated, searchable recommendation table | `CO`, `ADJUTANT`, `2IC` |
| `GET` | `/api/ai/company-recommendation/insights/<id>` | Full recommendation detail payload | `CO`, `ADJUTANT`, `2IC` |
| `POST` | `/api/ai/company-recommendation/decision` | Record Accept / Reject / Update decision | `CO`, `ADJUTANT`, `2IC` |
| `GET` | `/api/ai/company-recommendation/retrain-status` | Check training status and new joinee counts | Logged In |
| `POST` | `/api/ai/company-recommendation/retrain` | Trigger model retraining pipeline | `CO`, `ADJUTANT`, `2IC` |
| `GET` | `/api/ai/company-recommendation/insights-count` | Get counts for dashboard notification badges | Logged In |
| `GET` | `/api/ai/company-recommendation/visualization/<id>` | Probability & SHAP chart in new tab | Logged In |

---

## 5. Decision Workflow Format

Decisions recorded by executives store:
- `decision_type`: `'pending'`, `'accepted'`, `'rejected'`
- `decided_by`: Format `ROLE - USER_ID` (e.g. `CO - 102`, `ADJUTANT - 205`, `2IC - 301`)
- `decided_at`: Timestamp
- `final_company`: Authority-approved company
- `final_position`: Authority-approved appointment
- `decision_remarks`: Executive comments
