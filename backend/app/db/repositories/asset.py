from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import (
    and_,
    delete,
    desc,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.asset import Asset, AssetStatus, ModerationStatus
from app.db.models.intelligence import AssetIntelligence
from app.db.models.processing import ProcessingState, TaskProcessingStatus
from app.db.models.tag import AssetTag


class AssetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        public_id: str,
        cloudinary_public_id: str,
        original_filename: str,
        mime_type: str,
        file_size: int,
        width: Optional[int] = None,
        height: Optional[int] = None,
        cloudinary_url: Optional[str] = None,
        status: AssetStatus = AssetStatus.PENDING,
        moderation_status: ModerationStatus = ModerationStatus.PENDING,
    ) -> Asset:
        asset = Asset(
            public_id=public_id,
            cloudinary_public_id=cloudinary_public_id,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            width=width,
            height=height,
            cloudinary_url=cloudinary_url,
            status=status,
            moderation_status=moderation_status,
        )
        self.db.add(asset)
        await self.db.flush()

        # Also initialize the processing state
        processing_state = ProcessingState(
            asset_id=asset.id,
            tagging_status=TaskProcessingStatus.PENDING,
            moderation_status=TaskProcessingStatus.PENDING,
            processing_started_at=datetime.now(timezone.utc),
        )
        self.db.add(processing_state)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def get_by_id(self, asset_id: int) -> Optional[Asset]:
        stmt = (
            select(Asset)
            .where(Asset.id == asset_id)
            .options(
                selectinload(Asset.tags),
                selectinload(Asset.processing_state),
                selectinload(Asset.intelligence),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_public_id(self, public_id: str) -> Optional[Asset]:
        stmt = (
            select(Asset)
            .where(Asset.public_id == public_id)
            .options(
                selectinload(Asset.tags),
                selectinload(Asset.processing_state),
                selectinload(Asset.intelligence),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_cloudinary_public_id(self, cloudinary_public_id: str) -> Optional[Asset]:
        stmt = (
            select(Asset)
            .where(Asset.cloudinary_public_id == cloudinary_public_id)
            .options(
                selectinload(Asset.tags),
                selectinload(Asset.processing_state),
                selectinload(Asset.intelligence),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_assets(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[AssetStatus] = None,
        moderation_status: Optional[ModerationStatus] = None,
        tag: Optional[str] = None,
        query: Optional[str] = None,
        min_confidence: Optional[float] = 0.0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        quality_tier: Optional[str] = None,
        review_decision: Optional[str] = None,
        recommended_use: Optional[str] = None,
    ) -> Tuple[List[Asset], int]:
        filters = []

        if status:
            filters.append(Asset.status == status)
        if moderation_status:
            filters.append(Asset.moderation_status == moderation_status)

        if tag:
            # Join with tag
            tag_subquery = (
                select(AssetTag.asset_id)
                .where(
                    and_(
                        func.lower(AssetTag.tag) == func.lower(tag),
                        AssetTag.confidence >= (min_confidence or 0.0),
                    )
                )
                .scalar_subquery()
            )
            filters.append(Asset.id.in_(tag_subquery))

        if query:
            search_pattern = f"%{query.strip().lower()}%"
            # Match original filename or matching tag
            matching_tags_subquery = (
                select(AssetTag.asset_id)
                .where(func.lower(AssetTag.tag).like(search_pattern))
                .scalar_subquery()
            )
            filters.append(
                or_(
                    func.lower(Asset.original_filename).like(search_pattern),
                    Asset.id.in_(matching_tags_subquery),
                )
            )

        # Intelligence filters
        if quality_tier:
            tier = quality_tier.lower()
            if tier == "high":
                q_sub = select(AssetIntelligence.asset_id).where(AssetIntelligence.quality_score >= 80).scalar_subquery()
                filters.append(Asset.id.in_(q_sub))
            elif tier == "medium":
                q_sub = select(AssetIntelligence.asset_id).where(
                    and_(AssetIntelligence.quality_score >= 50, AssetIntelligence.quality_score < 80)
                ).scalar_subquery()
                filters.append(Asset.id.in_(q_sub))
            elif tier == "low":
                q_sub = select(AssetIntelligence.asset_id).where(AssetIntelligence.quality_score < 50).scalar_subquery()
                filters.append(Asset.id.in_(q_sub))

        if review_decision:
            rd_sub = select(AssetIntelligence.asset_id).where(
                func.lower(AssetIntelligence.review_decision) == func.lower(review_decision)
            ).scalar_subquery()
            filters.append(Asset.id.in_(rd_sub))

        if recommended_use:
            ru_sub = select(AssetIntelligence.asset_id).where(
                func.lower(AssetIntelligence.best_use) == func.lower(recommended_use)
            ).scalar_subquery()
            filters.append(Asset.id.in_(ru_sub))

        # Base statement
        base_stmt = select(Asset).where(*filters)

        # Count total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_count = (await self.db.execute(count_stmt)).scalar() or 0

        # Order by
        order_col = getattr(Asset, sort_by, Asset.created_at)
        if sort_order.lower() == "asc":
            order_expr = order_col.asc()
        else:
            order_expr = order_col.desc()

        stmt = (
            base_stmt.order_by(order_expr)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .options(
                selectinload(Asset.tags),
                selectinload(Asset.processing_state),
                selectinload(Asset.intelligence),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total_count

    async def update_moderation(
        self,
        asset: Asset,
        status: AssetStatus,
        moderation_status: ModerationStatus,
        reason: Optional[str] = None,
    ) -> Asset:
        now = datetime.now(timezone.utc)
        asset.status = status
        asset.moderation_status = moderation_status
        asset.moderation_reason = reason
        asset.decision_at = now

        if moderation_status == ModerationStatus.APPROVED:
            asset.approved_at = now
            asset.rejected_at = None
        elif moderation_status == ModerationStatus.REJECTED:
            asset.rejected_at = now
            asset.approved_at = None

        if asset.processing_state:
            asset.processing_state.moderation_status = TaskProcessingStatus.COMPLETED
            asset.processing_state.processing_completed_at = now

        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def add_tags(self, asset_id: int, tags: List[Tuple[str, float]]) -> List[AssetTag]:
        """
        Idempotently add tags to an asset. Avoids duplicates.
        """
        created_tags = []
        for tag_name, confidence in tags:
            tag_name_clean = tag_name.strip().lower()
            if not tag_name_clean:
                continue

            # Check if tag already exists for this asset
            stmt = select(AssetTag).where(
                and_(
                    AssetTag.asset_id == asset_id,
                    AssetTag.tag == tag_name_clean,
                )
            )
            existing = (await self.db.execute(stmt)).scalars().first()
            if existing:
                # Update confidence if higher
                if confidence > existing.confidence:
                    existing.confidence = confidence
                created_tags.append(existing)
            else:
                new_tag = AssetTag(
                    asset_id=asset_id,
                    tag=tag_name_clean,
                    confidence=confidence,
                )
                self.db.add(new_tag)
                created_tags.append(new_tag)

        await self.db.flush()
        return created_tags

    async def delete(self, asset: Asset) -> None:
        await self.db.delete(asset)
        await self.db.flush()
