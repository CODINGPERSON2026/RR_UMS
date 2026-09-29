"""
Service layer for AI Company Readiness.
Orchestrates database queries, deterministic engine calculations,
ML predictions, and recommendations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date

from db_config import get_db_connection
from .utils import (
    SUPPORTED_COMPANIES,
    normalize_company_name,
    DISPLAY_NAMES,
    get_readiness_status_badge
)
from .models.readiness_models import CompanyReadiness, PredictionResult, ContributingPersonnel
from .queries import (
    fetch_company_requirements,
    fetch_company_personnel,
    fetch_personnel_courses,
    fetch_personnel_weight_info,
    insert_readiness_snapshot,
    fetch_historical_snapshots
)
from .readiness_engine import ReadinessEngine
from .recommendation_engine import RecommendationEngine
from .prediction_service import ReadinessPredictionService
from .ai.model_training import ReadinessModelTrainer


class CompanyReadinessService:
    """High-level application service coordinating readiness features."""

    def __init__(self):
        self.engine = ReadinessEngine()
        self.recommender = RecommendationEngine()
        self.predictor = ReadinessPredictionService()

    def get_company_readiness(self, company_name: str) -> Optional[CompanyReadiness]:
        """Calculates and returns complete readiness evaluation for a company."""
        canonical_coy = normalize_company_name(company_name)
        if not canonical_coy or canonical_coy not in SUPPORTED_COMPANIES:
            return None

        conn = get_db_connection()
        if not conn:
            raise RuntimeError("Database connection failed")

        try:
            reqs = fetch_company_requirements(conn, canonical_coy)
            personnel = fetch_company_personnel(conn, canonical_coy)
            army_numbers = [p["army_number"] for p in personnel if p.get("army_number")]
            
            courses = fetch_personnel_courses(conn, army_numbers)
            weight_info = fetch_personnel_weight_info(conn, army_numbers)

            readiness = self.engine.calculate_company_readiness(
                canonical_company=canonical_coy,
                requirements=reqs,
                personnel=personnel,
                courses=courses,
                weight_info=weight_info
            )

            # Generate ML prediction
            prediction = self.predictor.get_prediction(readiness, personnel, weight_info)

            # Generate explainable recommendations
            recommendations = self.recommender.generate_recommendations(readiness, prediction)
            readiness.recommendations = recommendations

            return readiness
        finally:
            conn.close()

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Calculates readiness for all 3 supported companies and formation totals."""
        conn = get_db_connection()
        if not conn:
            raise RuntimeError("Database connection failed")

        try:
            companies_data: Dict[str, CompanyReadiness] = {}
            predictions_data: Dict[str, PredictionResult] = {}

            total_actual = 0
            total_required = 0
            total_available = 0
            readiness_scores = []

            for canonical_coy in SUPPORTED_COMPANIES:
                reqs = fetch_company_requirements(conn, canonical_coy)
                personnel = fetch_company_personnel(conn, canonical_coy)
                army_numbers = [p["army_number"] for p in personnel if p.get("army_number")]
                
                courses = fetch_personnel_courses(conn, army_numbers)
                weight_info = fetch_personnel_weight_info(conn, army_numbers)

                c_readiness = self.engine.calculate_company_readiness(
                    canonical_company=canonical_coy,
                    requirements=reqs,
                    personnel=personnel,
                    courses=courses,
                    weight_info=weight_info
                )

                c_pred = self.predictor.get_prediction(c_readiness, personnel, weight_info)
                c_recs = self.recommender.generate_recommendations(c_readiness, c_pred)
                c_readiness.recommendations = c_recs

                companies_data[canonical_coy] = c_readiness
                predictions_data[canonical_coy] = c_pred

                total_actual += c_readiness.actual_strength
                total_required += c_readiness.required_strength
                total_available += c_readiness.effective_available_strength
                readiness_scores.append(c_readiness.overall_readiness)

            avg_readiness = round(sum(readiness_scores) / len(readiness_scores), 1) if readiness_scores else 0.0
            formation_badge = get_readiness_status_badge(avg_readiness)

            return {
                "companies": {k: v.to_dict() for k, v in companies_data.items()},
                "predictions": {k: v.to_dict() for k, v in predictions_data.items()},
                "summary": {
                    "average_readiness": avg_readiness,
                    "status_badge": formation_badge,
                    "total_actual_strength": total_actual,
                    "total_required_strength": total_required,
                    "total_available_strength": total_available,
                    "strength_fulfillment": round((total_actual / total_required * 100), 1) if total_required else 100.0,
                    "company_count": len(SUPPORTED_COMPANIES)
                }
            }
        finally:
            conn.close()

    def get_gap_drilldown(
        self,
        company_name: str,
        gap_type: str,
        gap_name: Optional[str] = None
    ) -> List[ContributingPersonnel]:
        """Fetches soldiers contributing to a specific gap."""
        canonical_coy = normalize_company_name(company_name)
        if not canonical_coy:
            return []

        conn = get_db_connection()
        if not conn:
            return []

        try:
            personnel = fetch_company_personnel(conn, canonical_coy)
            army_numbers = [p["army_number"] for p in personnel if p.get("army_number")]
            courses = fetch_personnel_courses(conn, army_numbers)
            weight_info = fetch_personnel_weight_info(conn, army_numbers)

            return self.engine.get_contributing_personnel(
                gap_type=gap_type,
                gap_name=gap_name or gap_type,
                personnel=personnel,
                courses=courses,
                weight_info=weight_info
            )
        finally:
            conn.close()

    def record_current_snapshots(self) -> List[int]:
        """Evaluates all companies and records a snapshot into history table."""
        conn = get_db_connection()
        if not conn:
            return []

        inserted_ids = []
        try:
            today = date.today()
            for canonical_coy in SUPPORTED_COMPANIES:
                reqs = fetch_company_requirements(conn, canonical_coy)
                personnel = fetch_company_personnel(conn, canonical_coy)
                army_numbers = [p["army_number"] for p in personnel if p.get("army_number")]
                courses = fetch_personnel_courses(conn, army_numbers)
                weight_info = fetch_personnel_weight_info(conn, army_numbers)

                r = self.engine.calculate_company_readiness(canonical_coy, reqs, personnel, courses, weight_info)
                
                av_det = r.dimensions["availability"].details
                med_det = r.dimensions["medical"].details

                data = {
                    "company": canonical_coy,
                    "snapshot_date": today,
                    "strength_score": r.dimensions["strength"].score,
                    "qualification_score": r.dimensions["qualification"].score,
                    "course_score": r.dimensions["course"].score,
                    "trade_score": r.dimensions["trade"].score,
                    "fitness_score": r.dimensions["fitness"].score,
                    "medical_score": r.dimensions["medical"].score,
                    "availability_score": r.dimensions["availability"].score,
                    "overall_readiness": r.overall_readiness,
                    "main_gap_type": r.main_gap.gap_type if r.main_gap else "None",
                    "gap_count": r.main_gap.gap if r.main_gap else 0,
                    "actual_strength": r.actual_strength,
                    "required_strength": r.required_strength,
                    "available_strength": r.effective_available_strength,
                    "unfit_count": med_det.get("lmc", 0),
                    "onleave_count": av_det.get("onleave", 0),
                    "detachment_count": av_det.get("detachment", 0),
                    "td_count": av_det.get("td", 0),
                    "oncourse_count": av_det.get("oncourse", 0)
                }
                new_id = insert_readiness_snapshot(conn, data)
                inserted_ids.append(new_id)

            return inserted_ids
        finally:
            conn.close()

    def get_all_requirements(self) -> List[Dict[str, Any]]:
        """Fetches all active baseline requirements across companies."""
        conn = get_db_connection()
        if not conn:
            return []
        try:
            from .queries import fetch_all_active_requirements
            return fetch_all_active_requirements(conn)
        finally:
            conn.close()

    def save_requirement(self, data: Dict[str, Any]) -> int:
        """Saves or updates a requirement."""
        conn = get_db_connection()
        if not conn:
            raise RuntimeError("Database connection failed")
        try:
            from .queries import upsert_requirement
            return upsert_requirement(conn, data)
        finally:
            conn.close()

    def remove_requirement(self, req_id: int) -> bool:
        """Deletes a requirement."""
        conn = get_db_connection()
        if not conn:
            raise RuntimeError("Database connection failed")
        try:
            from .queries import delete_requirement
            return delete_requirement(conn, req_id)
        finally:
            conn.close()
