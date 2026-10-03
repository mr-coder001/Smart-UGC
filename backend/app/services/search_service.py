import math
from typing import Any, Dict, List, Optional
import cloudinary.search
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.db.models.asset import AssetStatus, ModerationStatus
from app.db.repositories.asset import AssetRepository
from app.schemas.asset import AssetListResponse
from app.schemas.search import SearchQueryParams, SearchResultResponse
from app.services.asset_service import asset_service


class SearchService:
    async def search_database(
        self,
        params: SearchQueryParams,
        db: AsyncSession,
        public_only: bool = True,
    ) -> SearchResultResponse:
        """
        PostgreSQL-backed catalog search.
        If public_only is True, only APPROVED assets are returned.
        """
        repo = AssetRepository(db)

        # Enforce public assets only for normal gallery browsing
        status_filter = AssetStatus(params.status) if params.status else None
        moderation_filter = ModerationStatus(params.moderation_status) if params.moderation_status else None
        if public_only:
            status_filter = AssetStatus.APPROVED
            moderation_filter = ModerationStatus.APPROVED

        assets, total = await repo.list_assets(
            page=params.page,
            page_size=params.page_size,
            status=status_filter,
            moderation_status=moderation_filter,
            tag=params.tag,
            query=params.query,
            min_confidence=params.min_confidence,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            quality_tier=params.quality_tier,
            review_decision=params.review_decision,
            recommended_use=params.recommended_use,
        )

        items = [asset_service.enrich_asset_read(a) for a in assets]
        total_pages = math.ceil(total / params.page_size) if total > 0 else 1

        return SearchResultResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            query=params.query,
            applied_filters=params.model_dump(exclude_none=True),
        )

    async def search_cloudinary(
        self,
        query: str,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """
        Cloudinary Search API abstraction.
        Allows querying directly by Cloudinary expressions (e.g. tags:dog, format:webp).
        """
        if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY:
            logger.info("Cloudinary credentials missing, returning empty search results.")
            return {"total_count": 0, "resources": []}

        try:
            results = (
                cloudinary.search.Search()
                .expression(query)
                .sort_by("created_at", "desc")
                .max_results(max_results)
                .execute()
            )
            return results
        except Exception as e:
            logger.error(f"Error querying Cloudinary search API: {e}")
            return {"total_count": 0, "resources": [], "error": str(e)}


search_service = SearchService()
