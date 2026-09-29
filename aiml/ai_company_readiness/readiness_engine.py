"""
Deterministic / Rule-Based Readiness Engine for UMS AI Company Readiness.
Strictly calculates actual, auditable scores and gaps from database records.
Does NOT perform machine learning or synthetic estimates.
"""

from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import datetime, date

from .models.readiness_models import (
    DEFAULT_DIMENSION_WEIGHTS,
    DimensionScore,
    GapItem,
    ContributingPersonnel,
    CompanyReadiness
)
from .utils import (
    calculate_percentage,
    safe_div,
    get_readiness_status_badge,
    DISPLAY_NAMES
)

# Standard passing physical test grades in military records
PASSING_FITNESS_GRADES = {"EX", "EXCELLENT", "GOOD", "SAT", "SATISFACTORY"}


def _match_qualification(p_civ_qual: Optional[str], target_qual: str) -> bool:
    """Checks if soldier's civ qualifications match the target qualification."""
    if not p_civ_qual:
        return False
    civ_lower = p_civ_qual.lower()
    target_lower = target_qual.lower()
    
    # 12th matching (e.g. '12th', '+2', 'inter', 'intermediate', '12', 'hsc')
    if "12" in target_lower:
        keywords = ["12", "12th", "+2", "inter", "intermediate", "senior secondary", "hsc"]
        return any(k in civ_lower for k in keywords)
    
    # Technical diploma
    if "diploma" in target_lower or "tech" in target_lower:
        keywords = ["diploma", "polytechnic", "iti", "technical", "engineering"]
        return any(k in civ_lower for k in keywords)
        
    # Graduation / Degree
    if "grad" in target_lower or "ba" in target_lower or "degree" in target_lower or "bsc" in target_lower:
        keywords = ["graduate", "graduation", "ba", "b.a", "bsc", "b.sc", "bcom", "b.com", "btech", "degree"]
        return any(k in civ_lower for k in keywords)
        
    return target_lower in civ_lower


def _match_course(course_records: List[Dict[str, Any]], detailed_course_str: Optional[str], target_course: str) -> bool:
    """Checks if soldier has completed the specified military course."""
    target_clean = re.sub(r'[^a-zA-Z0-9]', '', target_course).lower()
    
    # Check structured courses table
    for c in course_records:
        c_name = c.get("course") or ""
        c_clean = re.sub(r'[^a-zA-Z0-9]', '', c_name).lower()
        if target_clean in c_clean or c_clean in target_clean:
            return True
            
    # Check personnel.detailed_course column
    if detailed_course_str:
        det_clean = re.sub(r'[^a-zA-Z0-9]', '', detailed_course_str).lower()
        if target_clean in det_clean:
            return True
            
    return False


class ReadinessEngine:
    """
    Deterministic evaluation engine calculating real-time readiness dimensions,
    operational gaps, and personnel drill-down lists.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_DIMENSION_WEIGHTS.copy()
        # Ensure weights normalize to 1.0
        total_w = sum(self.weights.values())
        if total_w > 0 and abs(total_w - 1.0) > 0.001:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    def evaluate_strength(self, requirements: List[Dict[str, Any]], personnel: List[Dict[str, Any]]) -> Tuple[DimensionScore, List[GapItem]]:
        """Calculates strength fulfillment against authorized requirement."""
        req_item = next((r for r in requirements if r["requirement_type"] == "Strength"), None)
        req_count = req_item["required_count"] if req_item else len(personnel)
        actual_count = len(personnel)
        gap = max(0, req_count - actual_count)
        score = calculate_percentage(actual_count, req_count)
        
        gaps = []
        if gap > 0:
            priority = req_item.get("priority", "Critical") if req_item else "Critical"
            gaps.append(GapItem(
                gap_type="Strength",
                name="Total Personnel",
                required=req_count,
                available=actual_count,
                gap=gap,
                priority=priority,
                percentage_met=score,
                action_needed=f"Request unit posting reinforcement of {gap} personnel.",
                contributing_personnel_count=gap
            ))
            
        dim = DimensionScore(
            dimension="strength",
            score=score,
            weight=self.weights.get("strength", 0.20),
            weighted_score=round(score * self.weights.get("strength", 0.20), 2),
            required_count=req_count,
            available_count=actual_count,
            gap_count=gap,
            status="Met" if gap == 0 else ("Warning" if score >= 80 else "Critical"),
            details={"actual": actual_count, "required": req_count, "gap": gap}
        )
        return dim, gaps

    def evaluate_trade(self, requirements: List[Dict[str, Any]], personnel: List[Dict[str, Any]]) -> Tuple[DimensionScore, List[GapItem]]:
        """Calculates technical trade distribution and deficits."""
        trade_reqs = [r for r in requirements if r["requirement_type"] == "Trade"]
        if not trade_reqs:
            # If no trade requirements configured, default to full score
            return DimensionScore(
                dimension="trade", score=100.0, weight=self.weights.get("trade", 0.15),
                weighted_score=round(100.0 * self.weights.get("trade", 0.15), 2),
                required_count=0, available_count=len(personnel), gap_count=0, status="Met"
            ), []

        # Count actual personnel by trade (case-insensitive)
        actual_trade_counts: Dict[str, int] = {}
        for p in personnel:
            tr = (p.get("trade") or "General").strip().upper()
            actual_trade_counts[tr] = actual_trade_counts.get(tr, 0) + 1

        total_req = sum(r["required_count"] for r in trade_reqs)
        total_avail_for_req = 0
        total_gap = 0
        gaps = []

        for req in trade_reqs:
            t_name = req["requirement_name"].strip()
            t_count = req["required_count"]
            t_upper = t_name.upper()
            
            avail = actual_trade_counts.get(t_upper, 0)
            # Check partial match if exact match missing
            if avail == 0:
                avail = sum(cnt for tr, cnt in actual_trade_counts.items() if t_upper in tr or tr in t_upper)

            gap = max(0, t_count - avail)
            total_avail_for_req += min(t_count, avail)
            total_gap += gap

            if gap > 0:
                pct = calculate_percentage(avail, t_count)
                gaps.append(GapItem(
                    gap_type="Trade",
                    name=t_name,
                    required=t_count,
                    available=avail,
                    gap=gap,
                    priority=req.get("priority", "High"),
                    percentage_met=pct,
                    action_needed=f"Allot {gap} {t_name} tradesmen or detail eligible soldiers for re-mustering.",
                    contributing_personnel_count=gap
                ))

        score = calculate_percentage(total_avail_for_req, total_req)
        dim = DimensionScore(
            dimension="trade",
            score=score,
            weight=self.weights.get("trade", 0.15),
            weighted_score=round(score * self.weights.get("trade", 0.15), 2),
            required_count=total_req,
            available_count=total_avail_for_req,
            gap_count=total_gap,
            status="Met" if total_gap == 0 else ("Warning" if score >= 80 else "Critical"),
            details={"trades_evaluated": len(trade_reqs), "total_gap": total_gap}
        )
        return dim, gaps

    def evaluate_qualification(self, requirements: List[Dict[str, Any]], personnel: List[Dict[str, Any]]) -> Tuple[DimensionScore, List[GapItem]]:
        """Calculates educational & technical qualification compliance."""
        qual_reqs = [r for r in requirements if r["requirement_type"] == "Qualification"]
        if not qual_reqs:
            return DimensionScore(
                dimension="qualification", score=100.0, weight=self.weights.get("qualification", 0.15),
                weighted_score=round(100.0 * self.weights.get("qualification", 0.15), 2),
                required_count=0, available_count=len(personnel), gap_count=0, status="Met"
            ), []

        total_req = sum(r["required_count"] for r in qual_reqs)
        total_avail = 0
        total_gap = 0
        gaps = []

        for req in qual_reqs:
            q_name = req["requirement_name"]
            q_count = req["required_count"]

            avail = sum(1 for p in personnel if _match_qualification(p.get("civ_qualifications"), q_name))
            gap = max(0, q_count - avail)
            total_avail += min(q_count, avail)
            total_gap += gap

            if gap > 0:
                pct = calculate_percentage(avail, q_count)
                gaps.append(GapItem(
                    gap_type="Qualification",
                    name=q_name,
                    required=q_count,
                    available=avail,
                    gap=gap,
                    priority=req.get("priority", "Medium"),
                    percentage_met=pct,
                    action_needed=f"Sponsor or schedule {gap} personnel for {q_name} certification.",
                    contributing_personnel_count=gap
                ))

        score = calculate_percentage(total_avail, total_req)
        dim = DimensionScore(
            dimension="qualification",
            score=score,
            weight=self.weights.get("qualification", 0.15),
            weighted_score=round(score * self.weights.get("qualification", 0.15), 2),
            required_count=total_req,
            available_count=total_avail,
            gap_count=total_gap,
            status="Met" if total_gap == 0 else ("Warning" if score >= 80 else "Critical"),
            details={"qualifications_evaluated": len(qual_reqs)}
        )
        return dim, gaps

    def evaluate_course(self, requirements: List[Dict[str, Any]], personnel: List[Dict[str, Any]], courses: List[Dict[str, Any]]) -> Tuple[DimensionScore, List[GapItem]]:
        """Calculates military specialization course completion."""
        course_reqs = [r for r in requirements if r["requirement_type"] == "Course"]
        if not course_reqs:
            return DimensionScore(
                dimension="course", score=100.0, weight=self.weights.get("course", 0.10),
                weighted_score=round(100.0 * self.weights.get("course", 0.10), 2),
                required_count=0, available_count=len(personnel), gap_count=0, status="Met"
            ), []

        # Group courses by army_number
        courses_by_army: Dict[str, List[Dict[str, Any]]] = {}
        for c in courses:
            ano = c.get("army_number")
            if ano:
                courses_by_army.setdefault(ano, []).append(c)

        total_req = sum(r["required_count"] for r in course_reqs)
        total_avail = 0
        total_gap = 0
        gaps = []

        for req in course_reqs:
            c_name = req["requirement_name"]
            c_count = req["required_count"]

            avail = 0
            for p in personnel:
                ano = p.get("army_number") or ""
                p_courses = courses_by_army.get(ano, [])
                if _match_course(p_courses, p.get("detailed_course"), c_name):
                    avail += 1

            gap = max(0, c_count - avail)
            total_avail += min(c_count, avail)
            total_gap += gap

            if gap > 0:
                pct = calculate_percentage(avail, c_count)
                gaps.append(GapItem(
                    gap_type="Course",
                    name=c_name,
                    required=c_count,
                    available=avail,
                    gap=gap,
                    priority=req.get("priority", "High"),
                    percentage_met=pct,
                    action_needed=f"Detail {gap} eligible tradesmen for {c_name} in next training cycle.",
                    contributing_personnel_count=gap
                ))

        score = calculate_percentage(total_avail, total_req)
        dim = DimensionScore(
            dimension="course",
            score=score,
            weight=self.weights.get("course", 0.10),
            weighted_score=round(score * self.weights.get("course", 0.10), 2),
            required_count=total_req,
            available_count=total_avail,
            gap_count=total_gap,
            status="Met" if total_gap == 0 else ("Warning" if score >= 80 else "Critical"),
            details={"courses_evaluated": len(course_reqs)}
        )
        return dim, gaps

    def evaluate_fitness(self, personnel: List[Dict[str, Any]], weight_info: Dict[str, Dict[str, Any]]) -> Tuple[DimensionScore, List[GapItem]]:
        """Evaluates physical fitness standard based on BPET, PPT, and weight categories."""
        total_count = len(personnel)
        if total_count == 0:
            return DimensionScore(
                dimension="fitness", score=100.0, weight=self.weights.get("fitness", 0.10),
                weighted_score=round(100.0 * self.weights.get("fitness", 0.10), 2),
                required_count=0, available_count=0, gap_count=0, status="Met"
            ), []

        fit_count = 0
        unfit_count = 0

        for p in personnel:
            ano = p.get("army_number") or ""
            bpet = (p.get("bpet_grading") or "").strip().upper()
            ppt = (p.get("ppt_grading") or "").strip().upper()
            winfo = weight_info.get(ano)

            # Check if permanent low medical category from weight info
            is_perm_lmc = winfo and winfo.get("category_type") == "permanent"
            
            # Passing requires satisfactory grades in tests (or standard pass when tested)
            bpet_pass = not bpet or any(g in bpet for g in PASSING_FITNESS_GRADES)
            ppt_pass = not ppt or any(g in ppt for g in PASSING_FITNESS_GRADES)

            if bpet_pass and ppt_pass and not is_perm_lmc and "LMC" not in bpet:
                fit_count += 1
            else:
                unfit_count += 1

        score = calculate_percentage(fit_count, total_count)
        gaps = []
        if unfit_count > 0:
            gaps.append(GapItem(
                gap_type="Fitness",
                name="Physical Efficiency (BPET / PPT)",
                required=total_count,
                available=fit_count,
                gap=unfit_count,
                priority="High" if (unfit_count / total_count) > 0.15 else "Medium",
                percentage_met=score,
                action_needed=f"Implement remedial physical training for {unfit_count} substandard personnel.",
                contributing_personnel_count=unfit_count
            ))

        dim = DimensionScore(
            dimension="fitness",
            score=score,
            weight=self.weights.get("fitness", 0.10),
            weighted_score=round(score * self.weights.get("fitness", 0.10), 2),
            required_count=total_count,
            available_count=fit_count,
            gap_count=unfit_count,
            status="Met" if unfit_count == 0 else ("Warning" if score >= 80 else "Critical"),
            details={"fit_count": fit_count, "unfit_count": unfit_count}
        )
        return dim, gaps

    def evaluate_medical(self, personnel: List[Dict[str, Any]], weight_info: Dict[str, Dict[str, Any]]) -> Tuple[DimensionScore, List[GapItem]]:
        """Evaluates medical category standard (SHAPE-1 compliance)."""
        total_count = len(personnel)
        if total_count == 0:
            return DimensionScore(
                dimension="medical", score=100.0, weight=self.weights.get("medical", 0.10),
                weighted_score=round(100.0 * self.weights.get("medical", 0.10), 2),
                required_count=0, available_count=0, gap_count=0, status="Met"
            ), []

        shape1_count = 0
        lmc_count = 0

        for p in personnel:
            ano = p.get("army_number") or ""
            med_cat = (p.get("med_cat") or "No").strip().lower()
            winfo = weight_info.get(ano)

            is_lmc_weight = winfo and winfo.get("status_type") == "category"
            has_med_prob = med_cat == "yes" or (p.get("medical_problem") and len(p.get("medical_problem").strip()) > 3)

            if not has_med_prob and not is_lmc_weight:
                shape1_count += 1
            else:
                lmc_count += 1

        score = calculate_percentage(shape1_count, total_count)
        gaps = []
        if lmc_count > 0:
            gaps.append(GapItem(
                gap_type="Medical",
                name="Medical Category (LMC / Restrictions)",
                required=total_count,
                available=shape1_count,
                gap=lmc_count,
                priority="Critical" if (lmc_count / total_count) > 0.12 else "High",
                percentage_met=score,
                action_needed=f"Track recat boards and clinical re-evaluations for {lmc_count} LMC personnel.",
                contributing_personnel_count=lmc_count
            ))

        dim = DimensionScore(
            dimension="medical",
            score=score,
            weight=self.weights.get("medical", 0.10),
            weighted_score=round(score * self.weights.get("medical", 0.10), 2),
            required_count=total_count,
            available_count=shape1_count,
            gap_count=lmc_count,
            status="Met" if lmc_count == 0 else ("Warning" if score >= 85 else "Critical"),
            details={"shape1": shape1_count, "lmc": lmc_count}
        )
        return dim, gaps

    def evaluate_availability(self, personnel: List[Dict[str, Any]]) -> Tuple[DimensionScore, List[GapItem]]:
        """Evaluates operational presence on ground vs away on leave/detachment/TD/course."""
        total_count = len(personnel)
        if total_count == 0:
            return DimensionScore(
                dimension="availability", score=100.0, weight=self.weights.get("availability", 0.20),
                weighted_score=round(100.0 * self.weights.get("availability", 0.20), 2),
                required_count=0, available_count=0, gap_count=0, status="Met"
            ), []

        available_count = 0
        onleave_cnt = 0
        det_cnt = 0
        td_cnt = 0
        course_cnt = 0

        for p in personnel:
            is_onleave = bool(p.get("onleave_status"))
            is_det = bool(p.get("detachment_status"))
            is_td = bool(p.get("td_status"))
            is_course = bool(p.get("oncourse_status"))

            if is_onleave:
                onleave_cnt += 1
            if is_det:
                det_cnt += 1
            if is_td:
                td_cnt += 1
            if is_course:
                course_cnt += 1

            if not (is_onleave or is_det or is_td or is_course):
                available_count += 1

        unavailable_count = total_count - available_count
        score = calculate_percentage(available_count, total_count)
        
        gaps = []
        if unavailable_count > 0:
            gaps.append(GapItem(
                gap_type="Availability",
                name="Effective Ground Availability",
                required=total_count,
                available=available_count,
                gap=unavailable_count,
                priority="High" if (unavailable_count / total_count) > 0.20 else "Medium",
                percentage_met=score,
                action_needed=f"Regulate leave roster and recall {unavailable_count} non-essential detached/TD personnel.",
                contributing_personnel_count=unavailable_count
            ))

        dim = DimensionScore(
            dimension="availability",
            score=score,
            weight=self.weights.get("availability", 0.20),
            weighted_score=round(score * self.weights.get("availability", 0.20), 2),
            required_count=total_count,
            available_count=available_count,
            gap_count=unavailable_count,
            status="Met" if unavailable_count == 0 else ("Warning" if score >= 80 else "Critical"),
            details={
                "available": available_count,
                "unavailable": unavailable_count,
                "onleave": onleave_cnt,
                "detachment": det_cnt,
                "td": td_cnt,
                "oncourse": course_cnt
            }
        )
        return dim, gaps

    def calculate_company_readiness(
        self,
        canonical_company: str,
        requirements: List[Dict[str, Any]],
        personnel: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        weight_info: Dict[str, Dict[str, Any]]
    ) -> CompanyReadiness:
        """
        Orchestrates full deterministic readiness calculation across all dimensions,
        gaps, and explainable insights.
        """
        all_gaps: List[GapItem] = []

        dim_str, gaps_str = self.evaluate_strength(requirements, personnel)
        all_gaps.extend(gaps_str)

        dim_tr, gaps_tr = self.evaluate_trade(requirements, personnel)
        all_gaps.extend(gaps_tr)

        dim_qu, gaps_qu = self.evaluate_qualification(requirements, personnel)
        all_gaps.extend(gaps_qu)

        dim_cr, gaps_cr = self.evaluate_course(requirements, personnel, courses)
        all_gaps.extend(gaps_cr)

        dim_fit, gaps_fit = self.evaluate_fitness(personnel, weight_info)
        all_gaps.extend(gaps_fit)

        dim_med, gaps_med = self.evaluate_medical(personnel, weight_info)
        all_gaps.extend(gaps_med)

        dim_av, gaps_av = self.evaluate_availability(personnel)
        all_gaps.extend(gaps_av)

        dimensions = {
            "strength": dim_str,
            "availability": dim_av,
            "trade": dim_tr,
            "qualification": dim_qu,
            "course": dim_cr,
            "fitness": dim_fit,
            "medical": dim_med,
        }

        # Calculate weighted sum
        overall_readiness = sum(dim.weighted_score for dim in dimensions.values())
        overall_readiness = round(min(100.0, max(0.0, overall_readiness)), 1)

        # Identify Main Gap (sort by priority and gap deficit magnitude)
        priority_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        sorted_gaps = sorted(
            all_gaps,
            key=lambda g: (priority_order.get(g.priority, 1), g.gap),
            reverse=True
        )
        main_gap = sorted_gaps[0] if sorted_gaps else None

        # Build explainable AI Insights
        insights: List[str] = []
        if main_gap:
            insights.append(f"{main_gap.gap_type} is currently the largest readiness gap ({main_gap.name}: shortage of {main_gap.gap}).")
        
        av_details = dim_av.details
        if av_details.get("unavailable", 0) > 0:
            insights.append(
                f"{av_details.get('unavailable')} personnel currently absent from ground duties "
                f"({av_details.get('onleave')} on leave, {av_details.get('detachment')} on detachment, "
                f"{av_details.get('td')} on TD, {av_details.get('oncourse')} on courses)."
            )
            
        if dim_cr.gap_count > 0:
            insights.append(f"Military course completion has an accumulated deficit of {dim_cr.gap_count} qualifications.")
            
        if dim_med.gap_count > 0:
            insights.append(f"{dim_med.gap_count} personnel currently held in low medical category (LMC).")

        if overall_readiness >= 85.0:
            insights.append("Formation is operating within optimal operational readiness parameters.")
        elif overall_readiness >= 70.0:
            insights.append("Formation displays moderate readiness; proactive personnel replenishment advised.")
        else:
            insights.append("Formation is operating under critical operational gaps requiring command intervention.")

        status_badge = get_readiness_status_badge(overall_readiness)

        return CompanyReadiness(
            company=canonical_company,
            display_name=DISPLAY_NAMES.get(canonical_company, canonical_company),
            overall_readiness=overall_readiness,
            status_badge=status_badge,
            weights_used=self.weights,
            dimensions=dimensions,
            main_gap=main_gap,
            all_gaps=sorted_gaps,
            recommendations=[],  # Populated by RecommendationEngine
            insights=insights,
            actual_strength=len(personnel),
            required_strength=dim_str.required_count,
            effective_available_strength=dim_av.available_count,
            evaluation_time=datetime.now()
        )

    def get_contributing_personnel(
        self,
        gap_type: str,
        gap_name: str,
        personnel: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        weight_info: Dict[str, Dict[str, Any]]
    ) -> List[ContributingPersonnel]:
        """
        Drill-down: Returns personnel contributing to a specific gap.
        Filters soldiers based on actual condition causing the shortfall.
        """
        results: List[ContributingPersonnel] = []
        gap_type_lower = gap_type.lower()

        # 1. Strength Gap
        if gap_type_lower == "strength":
            for p in personnel:
                if p.get("onleave_status") or p.get("detachment_status") or p.get("td_status"):
                    reason = []
                    solutions = []
                    if p.get("onleave_status"):
                        reason.append("On Leave")
                        solutions.append("Schedule leave recall / Await rejoining")
                    if p.get("detachment_status"):
                        reason.append("On Detachment")
                        solutions.append("Issue detachment de-muster order")
                    if p.get("td_status"):
                        reason.append("On TD")
                        solutions.append("Relieve from temporary duty to parent unit")
                    results.append(ContributingPersonnel(
                        army_number=p.get("army_number") or "-",
                        name=p.get("name") or "Unknown",
                        rank=p.get("rank") or "-",
                        trade=p.get("trade") or "-",
                        company=p.get("company") or "-",
                        gap_category="Strength & Presence",
                        reason=", ".join(reason),
                        status_details=p.get("personnel_status") or "Active",
                        solution="; ".join(solutions) if solutions else "Muster to parent unit"
                    ))

        # 2. Trade Gap
        elif gap_type_lower == "trade":
            target_trade = gap_name.upper()
            for p in personnel:
                p_trade = (p.get("trade") or "").upper()
                # Check for secondary trade or missing qualifications in this trade
                if target_trade in p_trade or p_trade == target_trade:
                    results.append(ContributingPersonnel(
                        army_number=p.get("army_number") or "-",
                        name=p.get("name") or "Unknown",
                        rank=p.get("rank") or "-",
                        trade=p.get("trade") or "-",
                        company=p.get("company") or "-",
                        gap_category=f"Trade: {gap_name}",
                        reason="Assigned Trade Match",
                        current_value=p.get("trade"),
                        missing_value=gap_name,
                        status_details=p.get("personnel_status") or "Active",
                        solution=f"Nominate for {gap_name} trade cadre / assign as secondary trade"
                    ))

        # 3. Qualification Gap
        elif gap_type_lower == "qualification":
            for p in personnel:
                civ_qual = p.get("civ_qualifications") or ""
                lacking = p.get("lacking_qualifications") or ""
                has_qual = _match_qualification(civ_qual, gap_name)
                if not has_qual or gap_name.lower() in lacking.lower():
                    results.append(ContributingPersonnel(
                        army_number=p.get("army_number") or "-",
                        name=p.get("name") or "Unknown",
                        rank=p.get("rank") or "-",
                        trade=p.get("trade") or "-",
                        company=p.get("company") or "-",
                        gap_category="Qualification Deficiency",
                        reason=f"Lacks required certification: {gap_name}",
                        current_value=civ_qual or "None Recorded",
                        missing_value=gap_name,
                        status_details="Eligible for Certification",
                        solution=f"Enroll in upcoming {gap_name} certification cadre"
                    ))

        # 4. Course Gap
        elif gap_type_lower == "course":
            courses_by_army: Dict[str, List[Dict[str, Any]]] = {}
            for c in courses:
                ano = c.get("army_number")
                if ano:
                    courses_by_army.setdefault(ano, []).append(c)

            for p in personnel:
                ano = p.get("army_number") or ""
                p_courses = courses_by_army.get(ano, [])
                has_c = _match_course(p_courses, p.get("detailed_course"), gap_name)
                if not has_c:
                    results.append(ContributingPersonnel(
                        army_number=ano,
                        name=p.get("name") or "Unknown",
                        rank=p.get("rank") or "-",
                        trade=p.get("trade") or "-",
                        company=p.get("company") or "-",
                        gap_category="Course Deficit",
                        reason=f"Has not completed military course: {gap_name}",
                        current_value=p.get("detailed_course") or "None",
                        missing_value=gap_name,
                        status_details="Nominate for Upcoming Course",
                        solution=f"Nominate soldier for upcoming {gap_name} course panel"
                    ))

        # 5. Fitness Gap
        elif gap_type_lower == "fitness":
            for p in personnel:
                ano = p.get("army_number") or ""
                bpet = (p.get("bpet_grading") or "").strip().upper()
                ppt = (p.get("ppt_grading") or "").strip().upper()
                winfo = weight_info.get(ano)

                bpet_pass = not bpet or any(g in bpet for g in PASSING_FITNESS_GRADES)
                ppt_pass = not ppt or any(g in ppt for g in PASSING_FITNESS_GRADES)
                is_cat = winfo and winfo.get("status_type") == "category"

                if not bpet_pass or not ppt_pass or "LMC" in bpet or is_cat:
                    reasons = []
                    solutions = []
                    if not bpet_pass or "LMC" in bpet:
                        reasons.append(f"BPET: {bpet or 'Missing'}")
                        solutions.append("Detail for BPET remedial training & re-test")
                    if not ppt_pass:
                        reasons.append(f"PPT: {ppt or 'Missing'}")
                        solutions.append("Detail for PPT physical cadre & re-evaluation")
                    if is_cat:
                        reasons.append(f"Weight Category: {winfo.get('category_type') or 'LMC'}")
                        solutions.append("Enroll in Unit Weight Reduction & Fitness Monitoring cadre")
                    if not solutions:
                        solutions.append("Enroll in Remedial Physical Training (PT)")

                    results.append(ContributingPersonnel(
                        army_number=ano,
                        name=p.get("name") or "Unknown",
                        rank=p.get("rank") or "-",
                        trade=p.get("trade") or "-",
                        company=p.get("company") or "-",
                        gap_category="Fitness Deficiency",
                        reason=", ".join(reasons),
                        current_value=f"BPET: {bpet}, PPT: {ppt}",
                        missing_value="Standard Passing Grade",
                        restrictions=winfo.get("restrictions") if winfo else None,
                        status_details="Requires Remedial Physical Training",
                        solution="; ".join(solutions)
                    ))

        # 6. Medical Gap
        elif gap_type_lower == "medical":
            for p in personnel:
                ano = p.get("army_number") or ""
                med_cat = (p.get("med_cat") or "No").strip().lower()
                med_prob = p.get("medical_problem") or ""
                winfo = weight_info.get(ano)
                is_cat = winfo and winfo.get("status_type") == "category"

                if med_cat == "yes" or len(med_prob.strip()) > 3 or is_cat:
                    reasons = []
                    solutions = []
                    if med_cat == "yes":
                        reasons.append("Low Medical Category")
                        solutions.append("Schedule for periodic Medical Board review")
                    if med_prob:
                        reasons.append(f"Diagnosis: {med_prob}")
                        solutions.append(f"Follow up treatment & consultation for {med_prob}")
                    if is_cat:
                        reasons.append(f"Physical Cat: {winfo.get('category_type')}")
                        solutions.append("Review physical category & deployability clearance")
                    if not solutions:
                        solutions.append("Review medical status & assess deployability")

                    results.append(ContributingPersonnel(
                        army_number=ano,
                        name=p.get("name") or "Unknown",
                        rank=p.get("rank") or "-",
                        trade=p.get("trade") or "-",
                        company=p.get("company") or "-",
                        gap_category="Medical Limitation",
                        reason=", ".join(reasons),
                        current_value="LMC",
                        missing_value="SHAPE-1",
                        restrictions=p.get("restrictions") or (winfo.get("restrictions") if winfo else None),
                        status_details=f"Next Recat Due: {p.get('next_recat_due') or 'N/A'}",
                        solution="; ".join(solutions)
                    ))

        # 7. Availability Gap
        elif gap_type_lower == "availability":
            for p in personnel:
                is_onleave = bool(p.get("onleave_status"))
                is_det = bool(p.get("detachment_status"))
                is_td = bool(p.get("td_status"))
                is_course = bool(p.get("oncourse_status"))

                if is_onleave or is_det or is_td or is_course:
                    reasons = []
                    solutions = []
                    if is_onleave:
                        reasons.append("On Leave")
                        solutions.append("Schedule leave recall / Await rejoining")
                    if is_det:
                        reasons.append("On Detachment")
                        solutions.append("Issue detachment de-muster order")
                    if is_td:
                        reasons.append("On TD")
                        solutions.append("Relieve from temporary duty to parent unit")
                    if is_course:
                        reasons.append("On External Course")
                        solutions.append("Monitor external course completion")

                    results.append(ContributingPersonnel(
                        army_number=p.get("army_number") or "-",
                        name=p.get("name") or "Unknown",
                        rank=p.get("rank") or "-",
                        trade=p.get("trade") or "-",
                        company=p.get("company") or "-",
                        gap_category="Temporary Unavailability",
                        reason=", ".join(reasons),
                        current_value="Absent from Base",
                        missing_value="Present On Ground",
                        status_details=p.get("personnel_status") or "Active",
                        solution="; ".join(solutions) if solutions else "Review availability status"
                    ))

        return results
