"""
AI Recommendation Engine for UMS AI Company Readiness.
Generates explainable, actionable command recommendations derived from
actual deterministic readiness metrics and predictive models.
"""

from typing import List, Dict, Any, Optional
from .models.readiness_models import (
    CompanyReadiness,
    RecommendationItem,
    GapItem,
    PredictionResult
)


class RecommendationEngine:
    """
    Evaluates detected readiness gaps and operational shortfalls to formulate
    concrete military command recommendations for authorized executive review.
    """

    @staticmethod
    def generate_recommendations(
        readiness: CompanyReadiness,
        prediction: Optional[PredictionResult] = None
    ) -> List[RecommendationItem]:
        """
        Synthesizes company gaps and prediction risks into prioritized,
        explainable recommendations.
        """
        recommendations: List[RecommendationItem] = []
        coy = readiness.company

        # 1. Strength Deficit Recommendation
        dim_str = readiness.dimensions.get("strength")
        if dim_str and dim_str.gap_count > 0:
            recommendations.append(RecommendationItem(
                company=coy,
                issue_type="Strength Shortage",
                priority="Critical" if dim_str.score < 80 else "High",
                title=f"Address Company Strength Deficit ({dim_str.gap_count} Personnel)",
                description=(
                    f"{coy} is operating at {dim_str.score}% authorized strength "
                    f"({dim_str.available_count}/{dim_str.required_count}). "
                    f"A persistent deficit directly impacts company detachment and operational rotation."
                ),
                action_steps=[
                    f"Submit urgent deficiency report to RHQ / Adjutant branch for {dim_str.gap_count} personnel.",
                    "Review incoming unit posting pipeline (dues-in) for pending transfers.",
                    "Evaluate temporary redistribution of non-technical manpower from other companies."
                ],
                impact="Critical"
            ))

        # 2. Availability / Absence Recommendation
        dim_av = readiness.dimensions.get("availability")
        if dim_av and dim_av.score < 85.0:
            details = dim_av.details
            recommendations.append(RecommendationItem(
                company=coy,
                issue_type="Ground Availability",
                priority="High",
                title=f"Regulate Leave and Detachment Outflow ({details.get('unavailable')} Absent)",
                description=(
                    f"Only {dim_av.score}% of assigned personnel are available on ground. "
                    f"{details.get('onleave')} soldiers on leave, {details.get('detachment')} on detachment, "
                    f"and {details.get('td')} on temporary duty."
                ),
                action_steps=[
                    "Implement a phased leave quota cap of 15% maximum company strength per cycle.",
                    "Audit long-standing detachment duties and request replacement from receiving units.",
                    "Consolidate temporary duty (TD) tasks to minimize base garrison drain."
                ],
                impact="High"
            ))

        # 3. Critical Trade Gaps
        trade_gaps = [g for g in readiness.all_gaps if g.gap_type == "Trade" and g.gap > 0]
        if trade_gaps:
            critical_trades = [g.name for g in trade_gaps if g.priority in ("Critical", "High")]
            trades_str = ", ".join(critical_trades) if critical_trades else ", ".join(g.name for g in trade_gaps[:3])
            total_trade_gap = sum(g.gap for g in trade_gaps)
            
            recommendations.append(RecommendationItem(
                company=coy,
                issue_type="Technical Trade Deficit",
                priority="Critical" if any(g.priority == "Critical" for g in trade_gaps) else "High",
                title=f"Replenish Critical Tradesmen ({total_trade_gap} Vacancies in {trades_str})",
                description=(
                    f"Deficits identified in technical roles essential for signal communications: {trades_str}. "
                    f"Trade specialization directly affects equipment uptime and signal center manning."
                ),
                action_steps=[
                    f"Prioritize upcoming posting rosters for {trades_str} appointments.",
                    "Detail eligible lower-category tradesmen for trade advancement/upgrading boards.",
                    "Establish intra-unit on-the-job cross-training (OJT) to establish second-line competency."
                ],
                affected_trades=[g.name for g in trade_gaps],
                impact="High"
            ))

        # 4. Specialization Course Upgrading
        course_gaps = [g for g in readiness.all_gaps if g.gap_type == "Course" and g.gap > 0]
        if course_gaps:
            course_names = ", ".join(g.name for g in course_gaps[:3])
            total_course_gap = sum(g.gap for g in course_gaps)
            recommendations.append(RecommendationItem(
                company=coy,
                issue_type="Military Course Deficit",
                priority="Medium",
                title=f"Detail Personnel for Specialization Courses ({course_names})",
                description=(
                    f"{total_course_gap} course qualifications are pending to achieve authorized baseline in {coy}. "
                    f"Unqualified personnel cannot be confirmed in critical detachment billets."
                ),
                action_steps=[
                    f"Nominate qualified tradesmen meeting course prerequisites for {course_names}.",
                    "Conduct unit-level pre-course training cadres to maximize external course grading results.",
                    "Maintain succession planning register for Class-1 and instructor course quotas."
                ],
                impact="Medium"
            ))

        # 5. Medical Category Management
        dim_med = readiness.dimensions.get("medical")
        if dim_med and dim_med.gap_count > 0:
            recommendations.append(RecommendationItem(
                company=coy,
                issue_type="Medical Limitations",
                priority="High" if dim_med.score < 90 else "Medium",
                title=f"Manage Low Medical Category (LMC) Roster ({dim_med.gap_count} Personnel)",
                description=(
                    f"{dim_med.gap_count} soldiers have active medical limitations or low medical category gradings, "
                    f"restricting severe physical deployment or high-altitude/field tasks."
                ),
                action_steps=[
                    "Monitor next re-categorization medical board dates to ensure timely clinical reviews.",
                    "Align work assignments strictly within medical restrictions to prevent deterioration.",
                    "Coordinate with Senior Medical Officer (SMO) for rehabilitation and physical re-grading."
                ],
                impact="Medium"
            ))

        # 6. Physical Fitness Remedial Action
        dim_fit = readiness.dimensions.get("fitness")
        if dim_fit and dim_fit.gap_count > 0:
            recommendations.append(RecommendationItem(
                company=coy,
                issue_type="Physical Efficiency",
                priority="Medium",
                title=f"Remedial Physical Training for Substandard Personnel ({dim_fit.gap_count} Soldiers)",
                description=(
                    f"{dim_fit.gap_count} soldiers recorded substandard BPET/PPT or overweight status. "
                    f"Formation physical endurance is vital for deployment readiness."
                ),
                action_steps=[
                    "Establish a dedicated morning/evening remedial PT cadre under UBI/APTC instructor.",
                    "Enforce dietary supervision and weekly weight tracking via Weight Management System.",
                    "Schedule mandatory re-tests within 30 days to clear grading deficiencies."
                ],
                impact="Medium"
            ))

        # 7. Predictive Risk Mitigation (if predictive model indicates risk)
        if prediction and prediction.risk_level in ("High", "Critical"):
            recommendations.append(RecommendationItem(
                company=coy,
                issue_type="Predictive Risk Warning",
                priority="High",
                title="Early Mitigation for Projected Readiness Degradation",
                description=(
                    f"AI risk model indicates potential degradation in {prediction.prediction_period}. "
                    f"Leading indicators show increasing vulnerability due to pending medical recats and leave overlap."
                ),
                action_steps=[
                    "Conduct proactive commander review of next month's leave and duty roster.",
                    "Freeze non-essential detachment nominations until personnel buffer recovers."
                ],
                impact="Critical"
            ))

        return recommendations
