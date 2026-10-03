import traceback
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.asset import Asset
from app.db.models.intelligence import AssetIntelligence, ReviewDecisionEnum, ReviewRiskEnum
from app.schemas.intelligence import DecisionExplanations, ExplanationBlock
from app.services.intelligence.explanation_engine import ExplanationEngine
from app.services.intelligence.pipeline_timeline import PipelineTimelineBuilder
from app.services.intelligence.quality_analyzer import QualityAnalysisResult, QualityAnalyzer
from app.services.intelligence.review_router import ReviewRouteResult, ReviewRouter
from app.services.intelligence.usage_engine import UsageRecommendationEngine, UsageRecommendationResult


class IntelligenceEngine:
    """
    UGC Intelligence Engine Orchestrator.
    Sits after moderation & vision processing, before final delivery.
    Enforces failure isolation: an intelligence analysis failure will NEVER fail the upload or asset delivery.
    """

    def __init__(self):
        self.quality_analyzer = QualityAnalyzer()
        self.usage_engine = UsageRecommendationEngine()
        self.review_router = ReviewRouter()
        self.explanation_engine = ExplanationEngine()
        self.timeline_builder = PipelineTimelineBuilder()

    def calculate_quality_score(self, asset: Asset) -> QualityAnalysisResult:
        """Deterministic Visual Quality Score calculation (0–100)."""
        return self.quality_analyzer.analyze(asset)

    def generate_usage_recommendations(
        self, asset: Asset, quality_score: int
    ) -> UsageRecommendationResult:
        """Deterministic Channel Recommendations."""
        return self.usage_engine.generate_recommendations(asset, quality_score)

    def calculate_review_risk(
        self,
        asset: Asset,
        confidence: Optional[float] = None,
        violations: int = 0,
    ) -> ReviewRouteResult:
        """Deterministic Human Review routing & risk assessment."""
        return self.review_router.evaluate(asset, confidence, violations)

    def generate_decision_explanation(
        self,
        asset: Asset,
        quality_result: QualityAnalysisResult,
        usage_result: UsageRecommendationResult,
        review_result: ReviewRouteResult,
    ) -> DecisionExplanations:
        """Deterministic explainable AI blocks."""
        return self.explanation_engine.generate_explanations(
            asset, quality_result, usage_result, review_result
        )

    async def process_asset(
        self,
        asset: Asset,
        db: AsyncSession,
        stage_timings_ms: Optional[Dict[str, int]] = None,
        moderation_confidence: Optional[float] = None,
        moderation_violations: int = 0,
    ) -> AssetIntelligence:
        """
        Processes an asset through the full intelligence pipeline and persists the record.
        Wrapped with strict FAILURE ISOLATION.
        Enforces a single authoritative moderation state across all intelligence metrics.
        """
        try:
            from datetime import datetime, timezone
            from app.db.models.asset import AssetStatus, ModerationStatus
            from app.db.repositories.processing import ProcessingRepository
            from app.db.models.processing import TaskProcessingStatus

            now = datetime.now(timezone.utc)
            processing_repo = ProcessingRepository(db)

            # 1. Review Routing & Risk (Authoritative moderation state determination)
            review_res = self.calculate_review_risk(
                asset,
                confidence=moderation_confidence,
                violations=moderation_violations,
            )

            # Apply authoritative disposition to asset model BEFORE quality and usage calculations
            if review_res.decision == ReviewDecisionEnum.AUTO_APPROVED:
                asset.status = AssetStatus.APPROVED
                asset.moderation_status = ModerationStatus.APPROVED
                asset.moderation_reason = review_res.reason
                asset.decision_at = now
                asset.approved_at = now
                asset.rejected_at = None
                await processing_repo.update_moderation_status(asset.id, TaskProcessingStatus.COMPLETED)
            elif review_res.decision == ReviewDecisionEnum.AUTO_REJECTED:
                asset.status = AssetStatus.REJECTED
                asset.moderation_status = ModerationStatus.REJECTED
                asset.moderation_reason = review_res.reason
                asset.decision_at = now
                asset.rejected_at = now
                asset.approved_at = None
                await processing_repo.update_moderation_status(asset.id, TaskProcessingStatus.COMPLETED)
            else:
                asset.status = AssetStatus.PENDING
                asset.moderation_status = ModerationStatus.PENDING
                asset.moderation_reason = review_res.reason
                await processing_repo.update_moderation_status(asset.id, TaskProcessingStatus.PENDING)

            # 2. Quality Analysis (Now perfectly aligned with authoritative moderation status)
            quality_res = self.calculate_quality_score(asset)

            # 3. Usage Recommendations (Grounded in updated quality score and authoritative moderation status)
            usage_res = self.generate_usage_recommendations(asset, quality_res.score)

            # 4. Explainable AI
            explanations = self.generate_decision_explanation(
                asset, quality_res, usage_res, review_res
            )

            # 5. Pipeline Decision Timeline
            timeline = self.timeline_builder.build_timeline(asset, stage_timings_ms)

            # Fetch existing intelligence record if present (for re-runs/idempotency)
            stmt = select(AssetIntelligence).where(AssetIntelligence.asset_id == asset.id)
            result = await db.execute(stmt)
            intel_record = result.scalars().first()

            if not intel_record:
                intel_record = AssetIntelligence(asset_id=asset.id)
                db.add(intel_record)

            intel_record.quality_score = quality_res.score
            intel_record.quality_rating = quality_res.rating
            intel_record.quality_factors = [f.model_dump() for f in quality_res.factors]
            intel_record.unavailable_signals = quality_res.unavailable_signals

            intel_record.usage_recommendations = [r.model_dump() for r in usage_res.recommendations]
            intel_record.best_use = usage_res.best_use
            intel_record.recommended_format = usage_res.recommended_format

            intel_record.review_decision = review_res.decision.value
            intel_record.review_risk = review_res.risk.value
            intel_record.review_reason = review_res.reason
            intel_record.review_confidence = review_res.confidence

            intel_record.explanations = explanations.model_dump()
            intel_record.pipeline_timeline = [t.model_dump() for t in timeline]
            intel_record.status = "COMPLETED"
            intel_record.error_message = None

            await db.flush()
            logger.info(
                f"[IntelligenceEngine] Processed asset id={asset.id} score={quality_res.score} decision={review_res.decision.value} status={asset.status.value}"
            )
            return intel_record

        except Exception as exc:
            # FAILURE ISOLATION GUARANTEE: Never bubble up exceptions that would break asset upload/delivery
            logger.error(
                f"[IntelligenceEngine] Analysis failed for asset id={asset.id}: {str(exc)}\n{traceback.format_exc()}"
            )
            try:
                stmt = select(AssetIntelligence).where(AssetIntelligence.asset_id == asset.id)
                result = await db.execute(stmt)
                intel_record = result.scalars().first()

                fallback_explanations = DecisionExplanations(
                    moderation=ExplanationBlock(summary="Intelligence analysis encountered a partial error.", points=[]),
                    tags=ExplanationBlock(summary="Insufficient metadata to explain this decision.", points=[]),
                    crop=ExplanationBlock(summary="Insufficient metadata to explain this decision.", points=[]),
                    recommendations=ExplanationBlock(summary="Insufficient metadata to explain this decision.", points=[]),
                    quality=ExplanationBlock(summary="Insufficient metadata to explain this decision.", points=[]),
                )

                if not intel_record:
                    intel_record = AssetIntelligence(asset_id=asset.id)
                    db.add(intel_record)

                intel_record.quality_score = 50
                intel_record.quality_rating = "Partially Available"
                intel_record.quality_factors = []
                intel_record.unavailable_signals = []
                intel_record.usage_recommendations = []
                intel_record.best_use = "General Display"
                intel_record.recommended_format = "Standard"
                intel_record.review_decision = ReviewDecisionEnum.HUMAN_REVIEW.value
                intel_record.review_risk = ReviewRiskEnum.MEDIUM.value
                intel_record.review_reason = "Intelligence analysis partially available; escalated for manual review."
                intel_record.review_confidence = 0.50
                intel_record.explanations = fallback_explanations.model_dump()
                intel_record.pipeline_timeline = [t.model_dump() for t in self.timeline_builder.build_timeline(asset, stage_timings_ms)]
                intel_record.status = "PARTIAL"
                intel_record.error_message = str(exc)

                await db.flush()
                return intel_record
            except Exception as inner_exc:
                logger.error(f"[IntelligenceEngine] Could not persist fallback record: {inner_exc}")
                return None


intelligence_engine = IntelligenceEngine()
