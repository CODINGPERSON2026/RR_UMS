# AI Company Readiness - Datasets & Feature Documentation

## Overview
This directory documents the data sources, feature extraction dictionary, and historical snapshot methodology used by the **AI Company Readiness** module in the Unit Management System (UMS).

## Data Sources
1. **`personnel`**: Soldier records containing company, trade, rank, civil qualifications, lacking qualifications, physical grading (BPET/PPT), medical status, leave flags, detachment flags, TD status, and course flags.
2. **`ai_company_requirements`**: Operational baseline specifications for authorized manpower, trades, educational standards, and military courses across:
   * **HQ COY** (Headquarters Company)
   * **COMN COY** (Communication Company)
   * **3 COY** (3 Company)
3. **`courses`**: Completed military specialization courses and gradings.
4. **`weight_info`**: Physical category evaluations (SHAPE-1, temporary LMC, permanent LMC).
5. **`ai_company_readiness_history`**: Periodic snapshot log recording calculated readiness across time for trend modeling and machine learning.

## Feature Dictionary (19 Time-Aligned Features)
All features are evaluated strictly at observation timestamp $T$ with zero access to future records:

| Feature Name | Description | Source | Leakage Prevention |
|---|---|---|---|
| `company_hq` | Binary indicator for HQ COY (1.0 or 0.0) | System | Company constant |
| `company_comn` | Binary indicator for COMN COY (1.0 or 0.0) | System | Company constant |
| `company_3coy` | Binary indicator for 3 COY (1.0 or 0.0) | System | Company constant |
| `authorized_strength` | Authorized total manpower from requirements baseline | `ai_company_requirements` | Pre-configured baseline |
| `actual_strength` | Actual active soldier count in company | `personnel` | Current snapshot count |
| `strength_ratio` | Actual strength divided by authorized strength | Derived | Ratio at time $T$ |
| `leave_rate` | Ratio of soldiers on authorized leave | `personnel.onleave_status` | Status at time $T$ |
| `detachment_rate` | Ratio of soldiers away on detachment | `personnel.detachment_status` | Status at time $T$ |
| `td_rate` | Ratio of soldiers on temporary duty (TD) | `personnel.td_status` | Status at time $T$ |
| `course_away_rate` | Ratio of soldiers away on external courses | `personnel.oncourse_status` | Status at time $T$ |
| `availability_rate` | Effective on-ground personnel ratio | Derived | Ground presence at time $T$ |
| `trade_fulfillment_ratio` | Technical trade staffing fulfillment (0.0 - 1.0) | `ai_company_requirements` vs `personnel.trade` | Current trade inventory |
| `qualification_fulfillment_ratio`| Educational qualification fulfillment (0.0 - 1.0) | `personnel.civ_qualifications` | Current recorded quals |
| `course_fulfillment_ratio` | Military specialization course fulfillment (0.0 - 1.0) | `courses` & `personnel.detailed_course` | Current completed courses |
| `shape1_ratio` | Ratio of soldiers with SHAPE-1 medical classification | `weight_info.status_type` | Current medical category |
| `lmc_ratio` | Ratio of soldiers in Low Medical Category (LMC) | `weight_info.category_type` | Current active restrictions |
| `bpet_pass_ratio` | Ratio of soldiers with passing BPET grades | `personnel.bpet_grading` | Latest test grade at $T$ |
| `ppt_pass_ratio` | Ratio of soldiers with passing PPT grades | `personnel.ppt_grading` | Latest test grade at $T$ |
| `upcoming_recat_ratio` | Ratio of personnel due for medical board in &le; 60 days | `personnel.next_recat_due` | Known scheduled dates |

## Privacy and Non-Sensitive Data Standard
In strict adherence to military software standards, features contain only operational statistics. No personal identifying information (PAN, Aadhaar, bank details, home address, religion, or next-of-kin) is ever fed into the machine learning feature store.
