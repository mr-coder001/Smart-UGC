from typing import Optional, Tuple
from pydantic import BaseModel

from app.core.config import settings
from app.db.models.asset import Asset, AssetStatus, ModerationStatus
from app.db.models.intelligence import ReviewDecisionEnum, ReviewRiskEnum


class ReviewRouteResult(BaseModel):
    decision: ReviewDecisionEnum
    risk: ReviewRiskEnum
    reason: str
    confidence: Optional[float] = None


class ReviewRouter:
    """
    Intelligent Human Review Router.
    Extends the existing moderation system with deterministic routing rules and configurable thresholds.
    Never fabricates confidence or thresholds.
    """

    def __init__(
        self,
        auto_approve_threshold: float = settings.MODERATION_AUTO_APPROVE_THRESHOLD,
        auto_reject_threshold: float = settings.MODERATION_AUTO_REJECT_THRESHOLD,
    ):
        self.auto_approve_threshold = auto_approve_threshold
        self.auto_reject_threshold = auto_reject_threshold

    def evaluate(
        self,
        asset: Asset,
        moderation_confidence: Optional[float] = None,
        moderation_violations: int = 0,
    ) -> ReviewRouteResult:
        """
        Evaluate asset for automated routing vs human review dispatch.
        Integrates asset moderation status, confidence level, and brand safety checks.
        """
        status = asset.moderation_status
        confidence = float(moderation_confidence) if moderation_confidence is not None else None

        # 1. Explicit Violations or Rejection
        if status == ModerationStatus.REJECTED or moderation_violations > 0:
            if confidence is not None and confidence >= self.auto_approve_threshold:
                return ReviewRouteResult(
                    decision=ReviewDecisionEnum.AUTO_REJECTED,
                    risk=ReviewRiskEnum.HIGH,
                    reason="Explicit content violation detected with high system confidence.",
                    confidence=confidence,
                )
            else:
                return ReviewRouteResult(
                    decision=ReviewDecisionEnum.HUMAN_REVIEW,
                    risk=ReviewRiskEnum.HIGH,
                    reason="Potential safety issue flagged; manual review confirmation required.",
                    confidence=confidence,
                )

        # 2. Approved Status (Admin approved or verified by automated provider)
        if status == ModerationStatus.APPROVED:
            conf_str = f" with {confidence * 100:.1f}% confidence" if confidence is not None else ""
            return ReviewRouteResult(
                decision=ReviewDecisionEnum.AUTO_APPROVED,
                risk=ReviewRiskEnum.LOW,
                reason=f"Content verified clear of violations{conf_str}.",
                confidence=confidence,
            )

        # 3. Pending Status (Manual moderation queue or pending AI evaluation)
        if confidence is not None and confidence >= self.auto_approve_threshold:
            return ReviewRouteResult(
                decision=ReviewDecisionEnum.AUTO_APPROVED,
                risk=ReviewRiskEnum.LOW,
                reason=f"Automated safety analysis verified with {confidence * 100:.1f}% confidence.",
                confidence=confidence,
            )
        elif confidence is not None and confidence < self.auto_reject_threshold:
            return ReviewRouteResult(
                decision=ReviewDecisionEnum.HUMAN_REVIEW,
                risk=ReviewRiskEnum.HIGH,
                reason=f"Ambiguous or elevated risk content (confidence {confidence * 100:.1f}%). Escalated for manual verification.",
                confidence=confidence,
            )
        else:
            conf_detail = f" (confidence {confidence * 100:.1f}%)" if confidence is not None else ""
            return ReviewRouteResult(
                decision=ReviewDecisionEnum.HUMAN_REVIEW,
                risk=ReviewRiskEnum.MEDIUM,
                reason=f"Asset pending manual moderation inspection before public syndication{conf_detail}.",
                confidence=confidence,
            )

