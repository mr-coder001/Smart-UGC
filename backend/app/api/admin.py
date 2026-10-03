from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.security import validate_admin_api_key
from app.db.database import get_db
from app.db.models.asset import AssetStatus, ModerationStatus
from app.db.repositories.asset import AssetRepository
from app.schemas.admin import AdminStatsResponse, ModerationDecisionRequest
from app.schemas.asset import AssetRead
from app.schemas.search import SearchQueryParams, SearchResultResponse
from app.services.asset_service import asset_service
from app.services.metrics_service import metrics_service
from app.services.search_service import search_service

router = APIRouter(
    prefix="/admin",
    tags=["Admin & Moderation"],
    dependencies=[Depends(validate_admin_api_key)],
)


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="Get automation and platform statistics",
)
async def get_admin_stats(db: AsyncSession = Depends(get_db)) -> AdminStatsResponse:
    """
    Returns total assets, pending/approved/rejected counts, tag coverage %, automation rate %,
    and average time-to-decision.
    """
    return await metrics_service.get_admin_metrics(db)


@router.get(
    "/assets",
    response_model=SearchResultResponse,
    summary="List all assets for moderation review",
)
async def list_admin_assets(
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter: PENDING, APPROVED, REJECTED"),
    tag: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
) -> SearchResultResponse:
    """
    Admin catalog: Can view PENDING, APPROVED, and REJECTED assets.
    """
    params = SearchQueryParams(
        query=query,
        tag=tag,
        status=status_filter,
        moderation_status=status_filter,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await search_service.search_database(params=params, db=db, public_only=False)


@router.post(
    "/assets/{asset_id}/approve",
    response_model=AssetRead,
    summary="Approve asset",
)
async def approve_asset(
    asset_id: str,
    payload: Optional[ModerationDecisionRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    repo = AssetRepository(db)
    if asset_id.isdigit():
        asset = await repo.get_by_id(int(asset_id))
    else:
        asset = await repo.get_by_public_id(asset_id)

    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    reason = payload.reason if payload else "Approved by admin"
    updated_asset = await repo.update_moderation(
        asset=asset,
        status=AssetStatus.APPROVED,
        moderation_status=ModerationStatus.APPROVED,
        reason=reason,
    )
    await db.commit()
    await db.refresh(updated_asset)

    try:
        from app.services.intelligence.service import intelligence_service
        await intelligence_service.process_asset(updated_asset, db=db)
    except Exception as e:
        logger.warning(f"Failed to refresh intelligence on approval: {e}")

    await db.refresh(updated_asset)
    return asset_service.enrich_asset_read(updated_asset)


@router.post(
    "/assets/{asset_id}/reject",
    response_model=AssetRead,
    summary="Reject asset with reason",
)
async def reject_asset(
    asset_id: str,
    payload: Optional[ModerationDecisionRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    repo = AssetRepository(db)
    if asset_id.isdigit():
        asset = await repo.get_by_id(int(asset_id))
    else:
        asset = await repo.get_by_public_id(asset_id)

    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    reason = payload.reason if payload and payload.reason else "Rejected by admin"
    updated_asset = await repo.update_moderation(
        asset=asset,
        status=AssetStatus.REJECTED,
        moderation_status=ModerationStatus.REJECTED,
        reason=reason,
    )
    await db.commit()
    await db.refresh(updated_asset)

    try:
        from app.services.intelligence.service import intelligence_service
        await intelligence_service.process_asset(updated_asset, db=db)
    except Exception as e:
        logger.warning(f"Failed to refresh intelligence on rejection: {e}")

    await db.refresh(updated_asset)
    return asset_service.enrich_asset_read(updated_asset)
