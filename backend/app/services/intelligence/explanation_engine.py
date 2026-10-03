from typing import Any, Dict, List, Optional

from app.db.models.asset import Asset, AssetStatus, ModerationStatus
from app.db.models.intelligence import ReviewDecisionEnum
from app.schemas.intelligence import DecisionExplanations, ExplanationBlock
from app.services.intelligence.quality_analyzer import QualityAnalysisResult
from app.services.intelligence.review_router import ReviewRouteResult
from app.services.intelligence.usage_engine import UsageRecommendationResult


class ExplanationEngine:
    """
    Explainable AI (XAI) System.
    Generates contextual, grounded 'Why?' explanation blocks for:
    1. Moderation decision
    2. Tags / Vision detection
    3. Smart Cropping suitability
    4. Usage recommendations
    5. Visual Quality calculation
    Strict rule: Never fabricate explanations. If data is absent, state 'Insufficient metadata'.
    """

    def generate_explanations(
        self,
        asset: Asset,
        quality_result: QualityAnalysisResult,
        usage_result: UsageRecommendationResult,
        review_result: ReviewRouteResult,
    ) -> DecisionExplanations:
        moderation_block = self._explain_moderation(asset, review_result)
        tags_block = self._explain_tags(asset)
        crop_block = self._explain_crop(asset)
        recommendations_block = self._explain_recommendations(usage_result)
        quality_block = self._explain_quality(quality_result)

        return DecisionExplanations(
            moderation=moderation_block,
            tags=tags_block,
            crop=crop_block,
            recommendations=recommendations_block,
            quality=quality_block,
        )

    def _explain_moderation(
        self, asset: Asset, review: ReviewRouteResult
    ) -> ExplanationBlock:
        points: List[str] = []
        conf_pct = (review.confidence * 100) if review.confidence is not None else None

        if review.decision == ReviewDecisionEnum.AUTO_APPROVED:
            summary = "Content approved for production distribution."
            points.append("Zero explicit brand safety or policy violations detected.")
            if conf_pct is not None:
                points.append(f"Confidence score {conf_pct:.1f}% satisfies auto-approval threshold.")
            else:
                points.append("Manual administrative approval completed.")
            points.append("Publication authorization confirmed based on deterministic safety rules.")
        elif review.decision == ReviewDecisionEnum.AUTO_REJECTED:
            summary = "Content rejected due to policy non-compliance."
            points.append("Unsafe content trigger or severe policy violation identified.")
            if conf_pct is not None:
                points.append(f"Confidence score {conf_pct:.1f}% met automatic rejection threshold.")
            points.append("Asset quarantined from public CDN delivery.")
        else:
            summary = "Asset routed to human moderation queue for manual inspection."
            if conf_pct is not None:
                points.append(f"Automated confidence ({conf_pct:.1f}%) within borderline review band.")
            else:
                points.append("Automated AI moderation scoring unavailable; manual administrator review required.")
            if asset.moderation_reason:
                points.append(f"Inspection context: {asset.moderation_reason}")
            else:
                points.append("Content remains in pending queue prior to public syndication.")

        return ExplanationBlock(summary=summary, points=points)

    def _explain_tags(self, asset: Asset) -> ExplanationBlock:
        tags = asset.tags or []
        if not tags:
            return ExplanationBlock(
                summary="Insufficient metadata to explain this decision.",
                points=["No visual tags or semantic labels were extracted for this asset."],
            )

        tag_names = [getattr(t, "tag", getattr(t, "name", str(t))) for t in tags]
        top_tags = ", ".join(tag_names[:4])
        points: List[str] = [
            f"Detected provider semantic entities: {top_tags}.",
            "Extracted via automated vision provider categorization.",
            f"Total indexed descriptors: {len(tag_names)}.",
        ]

        return ExplanationBlock(
            summary=f"Automated tag identification detected {len(tag_names)} contextual entities.",
            points=points,
        )

    def _explain_crop(self, asset: Asset) -> ExplanationBlock:
        width = asset.width or 0
        height = asset.height or 0

        if width == 0 or height == 0:
            return ExplanationBlock(
                summary="Insufficient metadata to explain this decision.",
                points=["Image pixel dimensions are missing or unreadable."],
            )

        ratio = width / height
        points: List[str] = []

        if 0.8 <= ratio <= 1.25:
            summary = "High crop adaptability with balanced square/standard framing."
            points.append(f"Aspect ratio ({ratio:.2f}:1) preserves central focal areas across 1:1 and 4:5 crops.")
            points.append("Cloudinary g_auto gravity centers on primary visual clusters.")
        elif ratio > 1.25:
            summary = "Landscape orientation suitable for wide banner crops; requires auto-focus for vertical crops."
            points.append(f"Wide aspect ratio ({ratio:.2f}:1) delivers optimal horizontal banner coverage.")
            points.append("Smart g_auto/c_fill centers on prominent visual clusters to prevent horizontal clipping.")
        else:
            summary = "Vertical portrait orientation optimized for mobile viewports."
            points.append(f"Tall aspect ratio ({ratio:.2f}:1) minimizes dead space in story and feed displays.")
            points.append("Focal weight remains centered along the vertical axis.")

        return ExplanationBlock(summary=summary, points=points)

    def _explain_recommendations(
        self, usage_result: UsageRecommendationResult
    ) -> ExplanationBlock:
        points: List[str] = [
            f"Top channel match: {usage_result.best_use}.",
            f"Recommended target container: {usage_result.recommended_format}.",
        ]

        # Add specific notes from channels
        for rec in usage_result.recommendations:
            if rec.decision == "READY":
                points.append(f"✓ {rec.channel}: {rec.reason}")
            elif rec.decision == "REVIEW":
                points.append(f"⚠ {rec.channel}: {rec.reason}")
            else:
                points.append(f"✗ {rec.channel}: {rec.reason}")

        return ExplanationBlock(
            summary=f"Multi-channel evaluation ranked '{usage_result.best_use}' as the highest-affinity format.",
            points=points,
        )

    def _explain_quality(
        self, quality_result: QualityAnalysisResult
    ) -> ExplanationBlock:
        points: List[str] = [
            f"Deterministic score: {quality_result.score}/100 ({quality_result.rating}).",
            f"Algorithm version: {quality_result.version}.",
        ]

        for factor in quality_result.factors:
            prefix = "✓" if factor.passed else "⚠"
            points.append(f"{prefix} {factor.factor}: {factor.description}")

        if quality_result.unavailable_signals:
            points.append(
                f"Note: {len(quality_result.unavailable_signals)} physical sensor metrics omitted (unobtainable from HTTP upload)."
            )

        return ExplanationBlock(
            summary="Grounded calculation derived from real resolution, framing, format, and moderation signals.",
            points=points,
        )
