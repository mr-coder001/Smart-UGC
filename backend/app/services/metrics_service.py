from datetime import datetime
from typing import Dict
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.asset import Asset, AssetStatus, ModerationStatus
from app.db.models.processing import ProcessingState, TaskProcessingStatus
from app.db.models.tag import AssetTag
from app.schemas.admin import AdminStatsResponse


class MetricsService:
    async def get_admin_metrics(self, db: AsyncSession) -> AdminStatsResponse:
        """
        Aggregate operational and automation metrics across assets and AI tasks.
        """
        # 1. Total assets
        total_assets = (await db.execute(select(func.count(Asset.id)))).scalar() or 0

        # 2. Counts by moderation status
        pending_count = (
            await db.execute(
                select(func.count(Asset.id)).where(Asset.moderation_status == ModerationStatus.PENDING)
            )
        ).scalar() or 0

        approved_count = (
            await db.execute(
                select(func.count(Asset.id)).where(Asset.moderation_status == ModerationStatus.APPROVED)
            )
        ).scalar() or 0

        rejected_count = (
            await db.execute(
                select(func.count(Asset.id)).where(Asset.moderation_status == ModerationStatus.REJECTED)
            )
        ).scalar() or 0

        # 3. AI tag coverage: % of assets having at least 1 tag
        tagged_assets_count = (
            await db.execute(
                select(func.count(func.distinct(AssetTag.asset_id)))
            )
        ).scalar() or 0

        tag_coverage_percentage = (
            round((tagged_assets_count / total_assets) * 100, 2) if total_assets > 0 else 0.0
        )

        # 4. Processing status counts
        proc_status_counts: Dict[str, int] = {}
        proc_results = (
            await db.execute(
                select(ProcessingState.tagging_status, func.count(ProcessingState.id)).group_by(
                    ProcessingState.tagging_status
                )
            )
        ).all()
        for status, count in proc_results:
            proc_status_counts[f"tagging_{status.value if hasattr(status, 'value') else status}"] = count

        # 5. Automation rate (% of completed background processing tasks)
        completed_tasks = (
            await db.execute(
                select(func.count(ProcessingState.id)).where(
                    ProcessingState.tagging_status == TaskProcessingStatus.COMPLETED
                )
            )
        ).scalar() or 0

        automation_rate = (
            round((completed_tasks / total_assets) * 100, 2) if total_assets > 0 else 0.0
        )

        # 6. Average time-to-decision (in seconds) for reviewed assets
        avg_decision_seconds = None
        try:
            avg_decision_stmt = select(
                func.avg(
                    func.extract("epoch", Asset.decision_at) - func.extract("epoch", Asset.created_at)
                )
            ).where(Asset.decision_at.is_not(None))
            res = (await db.execute(avg_decision_stmt)).scalar()
            if res is not None:
                avg_decision_seconds = round(float(res), 2)
        except Exception:
            # SQLite fallback: calculate difference in Python
            try:
                decisions = (
                    await db.execute(
                        select(Asset.created_at, Asset.decision_at).where(Asset.decision_at.is_not(None))
                    )
                ).all()
                if decisions:
                    diffs = [
                        (d.timestamp() - c.timestamp())
                        for c, d in decisions
                        if c is not None and d is not None
                    ]
                    if diffs:
                        avg_decision_seconds = round(sum(diffs) / len(diffs), 2)
            except Exception:
                avg_decision_seconds = None

        # 7. UGC Intelligence Analytics
        from app.db.models.intelligence import AssetIntelligence, ReviewDecisionEnum

        total_intel_count = (await db.execute(select(func.count(AssetIntelligence.id)))).scalar() or 0

        avg_quality_score = None
        auto_approved_pct = None
        human_review_pct = None
        prod_ready_pct = None
        most_common_reason = None

        if total_intel_count > 0:
            # Average quality score
            avg_res = (await db.execute(select(func.avg(AssetIntelligence.quality_score)))).scalar()
            if avg_res is not None:
                avg_quality_score = round(float(avg_res), 1)

            # Auto approved count
            auto_appr_count = (
                await db.execute(
                    select(func.count(AssetIntelligence.id)).where(
                        AssetIntelligence.review_decision == ReviewDecisionEnum.AUTO_APPROVED.value
                    )
                )
            ).scalar() or 0
            auto_approved_pct = round((auto_appr_count / total_intel_count) * 100, 1)

            # Human review count
            human_rev_count = (
                await db.execute(
                    select(func.count(AssetIntelligence.id)).where(
                        AssetIntelligence.review_decision == ReviewDecisionEnum.HUMAN_REVIEW.value
                    )
                )
            ).scalar() or 0
            human_review_pct = round((human_rev_count / total_intel_count) * 100, 1)

            # Production ready count (quality_score >= 80)
            prod_ready_count = (
                await db.execute(
                    select(func.count(AssetIntelligence.id)).where(
                        AssetIntelligence.quality_score >= 80
                    )
                )
            ).scalar() or 0
            prod_ready_pct = round((prod_ready_count / total_intel_count) * 100, 1)

            # Most common review reason
            top_reason_stmt = (
                select(AssetIntelligence.review_reason, func.count(AssetIntelligence.id).label("cnt"))
                .where(AssetIntelligence.review_reason.is_not(None))
                .group_by(AssetIntelligence.review_reason)
                .order_by(desc("cnt"))
                .limit(1)
            )
            top_reason_res = (await db.execute(top_reason_stmt)).first()
            if top_reason_res and top_reason_res[0]:
                most_common_reason = top_reason_res[0]

        return AdminStatsResponse(
            total_assets=total_assets,
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            tag_coverage_percentage=tag_coverage_percentage,
            automation_rate=automation_rate,
            average_decision_time_seconds=avg_decision_seconds,
            processing_status_counts=proc_status_counts,
            average_quality_score=avg_quality_score,
            auto_approved_percentage=auto_approved_pct,
            human_review_percentage=human_review_pct,
            production_ready_percentage=prod_ready_pct,
            most_common_review_reason=most_common_reason,
            total_intelligence_analyzed=total_intel_count,
        )


metrics_service = MetricsService()
