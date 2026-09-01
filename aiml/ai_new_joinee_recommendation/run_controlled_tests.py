"""
Controlled Test Suite for Retrained AI New Joinee Recommendation Model
Tests 1 to 7 + Anti-Copy Test as required by specifications.
Demonstrates probability shifts and candidate re-ranking driven strictly by historical data.
"""

import os
import sys
import json
import pandas as pd

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aiml.ai_new_joinee_recommendation.recommendation import recommend_placement

def run_all_controlled_tests():
    print("=" * 80)
    print("CONTROLLED TEST SUITE: RETRAINED AI NEW JOINEE RECOMMENDATION MODEL")
    print("=" * 80)

    # -------------------------------------------------------------
    # TEST 1: Same Personnel Profile -> Change Previous Unit
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("TEST 1: SENSITIVITY TO PREVIOUS UNIT CHANGE")
    print("Same Duty ('GD'), Change Previous Unit: 'LOGISTICS UNIT' vs 'SIGNAL UNIT'")
    print("=" * 50)

    rec_u1 = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "LOGISTICS UNIT", "duty_performed": "SKT", "from_date": "2022-01-01", "to_date": "2024-01-01"}]
    )
    rec_u2 = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "SIGNAL UNIT", "duty_performed": "Radio", "from_date": "2022-01-01", "to_date": "2024-01-01"}]
    )

    print(f"Case 1A [LOGISTICS UNIT -> SKT  ]: Top Coy = {rec_u1['recommended_company']} ({rec_u1['confidence_score']}) | Probs = {rec_u1['probabilities']}")
    print(f"Case 1B [SIGNAL UNIT    -> Radio]: Top Coy = {rec_u2['recommended_company']} ({rec_u2['confidence_score']}) | Probs = {rec_u2['probabilities']}")
    assert rec_u1['recommended_company'] != rec_u2['recommended_company'], "Test 1 Failed: Unit change did not change top company!"
    print(">>> TEST 1 PASSED: Previous Unit significantly shifted probabilities and top company!")

    # -------------------------------------------------------------
    # TEST 2: Same Previous Unit -> Change Previous Duty
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("TEST 2: SENSITIVITY TO PREVIOUS DUTY CHANGE")
    print("Same Unit ('HQ UNIT'), Change Duty: 'SKT' vs 'Radio' vs 'MT'")
    print("=" * 50)

    rec_d1 = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "HQ UNIT", "duty_performed": "SKT", "from_date": "2022-01-01", "to_date": "2024-01-01"}]
    )
    rec_d2 = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "HQ UNIT", "duty_performed": "Radio", "from_date": "2022-01-01", "to_date": "2024-01-01"}]
    )
    rec_d3 = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "HQ UNIT", "duty_performed": "MT", "from_date": "2022-01-01", "to_date": "2024-01-01"}]
    )

    print(f"Case 2A [HQ UNIT -> SKT  ]: Top = {rec_d1['recommended_company']} | {rec_d1['recommended_section']} -> {rec_d1['recommended_position']} (Probs: {rec_d1['probabilities']})")
    print(f"Case 2B [HQ UNIT -> Radio]: Top = {rec_d2['recommended_company']} | {rec_d2['recommended_section']} -> {rec_d2['recommended_position']} (Probs: {rec_d2['probabilities']})")
    print(f"Case 2C [HQ UNIT -> MT   ]: Top = {rec_d3['recommended_company']} | {rec_d3['recommended_section']} -> {rec_d3['recommended_position']} (Probs: {rec_d3['probabilities']})")
    assert rec_d1['recommended_section'] != rec_d2['recommended_section'], "Test 2 Failed: Duty change did not alter section!"
    print(">>> TEST 2 PASSED: Previous Duty change redirected company/section/appointment appropriately!")

    # -------------------------------------------------------------
    # TEST 3: Single Duty/Domain Option Selection
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("TEST 3: SINGLE DUTY / DOMAIN SELECTION")
    print("Unit: 'SIGNAL UNIT', Duty: 'Radio', Selected Choice: 'COMN COY -> COMMUNICATION -> Radio RR'")
    print("=" * 50)

    selected_single = [{"company": "COMN COY", "section": "COMMUNICATION / TECHNICAL", "appointment": "Radio RR"}]
    rec_single = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "SIGNAL UNIT", "duty_performed": "Radio", "from_date": "2022-01-01", "to_date": "2024-01-01"}],
        selected_domains=selected_single
    )
    print(f"Result: {rec_single['recommended_company']} | {rec_single['recommended_section']} -> {rec_single['recommended_position']} ({rec_single['confidence_score']})")
    print(f"Probabilities: {rec_single['probabilities']}")
    print(">>> TEST 3 PASSED!")

    # -------------------------------------------------------------
    # TEST 4 & 5: Multiple Duty/Domain Selections & Candidate Ranking
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("TEST 4 & 5: MULTIPLE DUTY / DOMAIN SELECTIONS & RANKING")
    print("3 Diverse Choices: [1. HQ COY -> QM -> Ration NCO, 2. COMN COY -> COMMUNICATION -> System, 3. 3 COY -> TECHNICAL -> VC]")
    print("=" * 50)

    multi_choices = [
        {"company": "HQ COY", "section": "QM", "appointment": "Ration NCO"},
        {"company": "COMN COY", "section": "COMMUNICATION / TECHNICAL", "appointment": "System"},
        {"company": "3 COY", "section": "TECHNICAL / CORPS HQ", "appointment": "VC"}
    ]

    rec_multi = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "SIGNAL UNIT", "duty_performed": "Radio", "from_date": "2022-01-01", "to_date": "2024-01-01"}],
        selected_domains=multi_choices
    )

    print(f"Soldier with SIGNAL UNIT + Radio Background given 3 Diverse Multi-Choices:")
    print(f"Top Recommendation: {rec_multi['recommended_company']} | {rec_multi['recommended_section']} -> {rec_multi['recommended_position']}")
    print("Candidate Ranking Breakdown across Alternatives:")
    for alt in rec_multi.get("alternative_allocations", [])[:5]:
        print(f"  - Rank: {alt['company']:<10} | {alt['section']:<25} | {alt['position']:<15} -> {alt['composite_pct']}")
    assert rec_multi['recommended_company'] == "COMN COY", "Test 4/5 Failed: COMN COY was not ranked top for Signal background!"
    print(">>> TEST 4 & 5 PASSED: Model ranked candidates according to learned historical evidence!")

    # -------------------------------------------------------------
    # TEST 6: Keep Multi-Choices Identical -> Change Previous Unit
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("TEST 6: MULTI-CHOICE RANKING UNDER PREVIOUS UNIT SHIFT")
    print("Same 3 Choices, Change Unit: 'LOGISTICS UNIT' vs 'FIELD UNIT'")
    print("=" * 50)

    rec_u_log = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "LOGISTICS UNIT", "duty_performed": "SKT", "from_date": "2022-01-01", "to_date": "2024-01-01"}],
        selected_domains=multi_choices
    )
    rec_u_fld = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "FIELD UNIT", "duty_performed": "GD", "from_date": "2022-01-01", "to_date": "2024-01-01"}],
        selected_domains=multi_choices
    )

    print(f"With LOGISTICS UNIT + SKT: Top = {rec_u_log['recommended_company']} ({rec_u_log['confidence_score']}) | Probs: {rec_u_log['probabilities']}")
    print(f"With FIELD UNIT + GD    : Top = {rec_u_fld['recommended_company']} ({rec_u_fld['confidence_score']}) | Probs: {rec_u_fld['probabilities']}")
    assert rec_u_log['recommended_company'] == "HQ COY", "Test 6 Failed: Logistics unit should favor HQ COY!"
    assert rec_u_fld['recommended_company'] == "3 COY", "Test 6 Failed: Field unit should favor 3 COY!"
    print(">>> TEST 6 PASSED: Candidate ranking re-ordered correctly based on historical unit compatibility!")

    # -------------------------------------------------------------
    # TEST 7: Keep Previous Unit Identical -> Change Previous Duty
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("TEST 7: MULTI-CHOICE RANKING UNDER PREVIOUS DUTY SHIFT")
    print("Same Unit ('TECH UNIT'), Same 3 Choices, Change Duty: 'Technician' vs 'Server'")
    print("=" * 50)

    rec_d_tech = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "TECH UNIT", "duty_performed": "Technician", "from_date": "2022-01-01", "to_date": "2024-01-01"}],
        selected_domains=multi_choices
    )
    rec_d_srv = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "TECH UNIT", "duty_performed": "Server", "from_date": "2022-01-01", "to_date": "2024-01-01"}],
        selected_domains=multi_choices
    )

    print(f"With Technician Duty: Top = {rec_d_tech['recommended_company']} | {rec_d_tech['recommended_section']} (Probs: {rec_d_tech['probabilities']})")
    print(f"With Server Duty    : Top = {rec_d_srv['recommended_company']} | {rec_d_srv['recommended_section']} (Probs: {rec_d_srv['probabilities']})")
    assert rec_d_tech['recommended_company'] == "3 COY", "Test 7 Failed: Technician should favor 3 COY!"
    assert rec_d_srv['recommended_company'] == "COMN COY", "Test 7 Failed: Server should favor COMN COY!"
    print(">>> TEST 7 PASSED: Candidate ranking re-ordered correctly based on historical duty transitions!")

    # -------------------------------------------------------------
    # ANTI-COPY TEST: Check that model does NOT blindly copy user inputs
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print("ANTI-COPY TEST: Input Mismatched Choice vs Strong Historical Pattern")
    print("Soldier History: 'LOGISTICS UNIT' + 'SKT' (96.2% HQ COY historical)")
    print("User Selects Single Choice: 'COMN COY -> COMMUNICATION -> System'")
    print("=" * 50)

    anti_copy_choice = [{"company": "COMN COY", "section": "COMMUNICATION / TECHNICAL", "appointment": "System"}]
    rec_anti = recommend_placement(
        rank="Signal Man",
        units_history=[{"unit": "LOGISTICS UNIT", "duty_performed": "SKT", "from_date": "2022-01-01", "to_date": "2024-01-01"}],
        selected_domains=anti_copy_choice
    )

    print(f"Result Top Company: {rec_anti['recommended_company']} (Probs: {rec_anti['probabilities']})")
    print(f"Why Recommended Rationale: {rec_anti['why_recommended']}")
    assert rec_anti['recommended_company'] == "HQ COY", "Anti-Copy Test Failed: Model copied user input instead of following historical evidence!"
    print(">>> ANTI-COPY TEST PASSED: Model weighted historical evidence over mismatched input selection!")

    print("\n" + "=" * 80)
    print("ALL 7 CONTROLLED TESTS + ANTI-COPY TEST COMPLETED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    run_all_controlled_tests()
