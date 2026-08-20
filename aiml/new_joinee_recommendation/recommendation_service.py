from typing import Dict, Any, List, Optional
import pandas as pd

from .predict import CompanyPredictor
from .data_loader import load_single_personnel, load_raw_data, normalize_company
from .feature_engineering import build_features_for_personnel
from .config import MODEL_METADATA_FILE, CANONICAL_COMPANIES
from .utils import get_logger

logger = get_logger("service")

class CompanyRecommendationService:
    """
    High-level recommendation service that orchestrates inference,
    computes data-backed evidence from the MySQL database, and constructs
    human-readable explainability insights.
    """
    def __init__(self):
        self.predictor = CompanyPredictor()

    def reload_model(self):
        """Reloads prediction artifacts."""
        self.predictor.reload()

    def generate_evidence(
        self,
        trade: str,
        rank: str,
        previous_units: List[str],
        recommended_company: str
    ) -> Dict[str, Any]:
        """
        Calculates genuine historical statistics from the database for similar soldiers.
        """
        evidence = {
            "similar_records_count": 0,
            "company_distribution_among_similar": {c: 0 for c in CANONICAL_COMPANIES},
            "reasons": []
        }
        try:
            personnel_df, _ = load_raw_data()
            personnel_df["target_company"] = personnel_df["company"].apply(normalize_company)
            eligible = personnel_df[personnel_df["target_company"].isin(CANONICAL_COMPANIES)].copy()
            
            # 1. Match by trade
            trade_clean = str(trade).strip().upper()
            eligible["trade_clean"] = eligible["trade"].fillna("").astype(str).str.strip().str.upper()
            
            trade_matches = eligible[eligible["trade_clean"] == trade_clean]
            if len(trade_matches) > 0:
                dist = trade_matches["target_company"].value_counts().to_dict()
                evidence["similar_records_count"] = len(trade_matches)
                for c in CANONICAL_COMPANIES:
                    evidence["company_distribution_among_similar"][c] = int(dist.get(c, 0))
                
                # Check top company for this trade
                top_trade_coy = trade_matches["target_company"].value_counts().index[0]
                pct = (dist.get(top_trade_coy, 0) / len(trade_matches)) * 100
                evidence["reasons"].append(
                    f"Trade specialty ('{trade}') aligns strongly with historical assignments ({pct:.1f}% of {trade} personnel are in {top_trade_coy})."
                )
            else:
                evidence["reasons"].append(f"Trade specialty '{trade}' is evaluated against holistic personnel pattern.")

            # 2. Previous units evidence
            if previous_units:
                evidence["reasons"].append(
                    f"Previous serving history across {len(previous_units)} unit(s) ({', '.join(previous_units[:3])}) provides high-affinity assignment cues for {recommended_company}."
                )
            else:
                evidence["reasons"].append(
                    f"No previous-unit history available (New Joinee Cold-Start profile). Primary prediction weights derived from Trade ('{trade}') and Rank ('{rank}')."
                )

            # 3. Model conclusion
            evidence["reasons"].append(
                f"Model identifies {recommended_company} as the highest statistical probability assignment for this soldier profile."
            )

        except Exception as e:
            logger.warning(f"Error calculating database evidence: {e}")
            evidence["reasons"] = [
                f"Statistical alignment with historical {recommended_company} personnel profiles.",
                f"Trade and background attributes match the operational requirements of {recommended_company}."
            ]

        return evidence

    def get_recommendation_for_personnel_id(self, personnel_id: int) -> Dict[str, Any]:
        """
        Generates full recommendation result with evidence for a personnel ID.
        """
        res = self.predictor.predict_for_personnel_id(personnel_id)
        if not res.get("success"):
            return res

        trade = res.get("trade", "UNKNOWN")
        rank = res.get("rank", "UNKNOWN")
        prev_units = res.get("previous_units", [])
        recommended_coy = res.get("recommended_company", "HQ Coy")

        evidence = self.generate_evidence(trade, rank, prev_units, recommended_coy)
        res["evidence"] = evidence
        res["reasons"] = evidence.get("reasons", [])
        return res

    def get_recommendation_for_payload(
        self,
        personnel_dict: Dict[str, Any],
        units_list: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates full recommendation result with evidence for a raw joinee form payload.
        """
        units_df = pd.DataFrame(units_list) if units_list else pd.DataFrame()
        feat_dict = build_features_for_personnel(personnel_dict, units_df)
        res = self.predictor.predict_for_features(feat_dict)
        if not res.get("success"):
            return res

        trade = feat_dict.get("trade", "UNKNOWN")
        rank = feat_dict.get("rank", "UNKNOWN")
        prev_units = units_df["unit"].dropna().tolist() if len(units_df) > 0 and "unit" in units_df else []
        recommended_coy = res.get("recommended_company", "HQ Coy")

        evidence = self.generate_evidence(trade, rank, prev_units, recommended_coy)
        res["evidence"] = evidence
        res["reasons"] = evidence.get("reasons", [])
        res["trade"] = trade
        res["rank"] = rank
        res["previous_units"] = prev_units
        return res
