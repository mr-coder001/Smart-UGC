from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import check_rate_limit
from app.db.database import get_db
from app.schemas.asset import (
    AssetListResponse,
    AssetRead,
    AssetTransformRequest,
    AssetTransformResponse,
)
from app.schemas.search import SearchQueryParams, SearchResultResponse
from app.schemas.intelligence import AssetIntelligenceRead
from app.services.asset_service import asset_service
from app.services.intelligence.service import intelligence_engine
from app.services.search_service import search_service
from app.services.transformation_service import transformation_service

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post(
    "",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image asset",
)
async def upload_asset(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    """
    Upload an image (JPEG, PNG, WebP, GIF, AVIF, HEIC).
    Rate-limited to 20 uploads/minute per client. Max size 10MB.
    Starts as PENDING moderation and triggers auto-tagging.
    """
    await check_rate_limit(request)
    return await asset_service.upload_asset(file=file, db=db)


@router.get(
    "",
    response_model=SearchResultResponse,
    summary="List public assets",
)
async def list_assets(
    query: Optional[str] = Query(None, description="Search query"),
    tag: Optional[str] = Query(None, description="Tag filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="asc or desc"),
    quality_tier: Optional[str] = Query(None, description="high, medium, low"),
    review_decision: Optional[str] = Query(None, description="AUTO_APPROVED, AUTO_REJECTED, HUMAN_REVIEW"),
    recommended_use: Optional[str] = Query(None, description="Channel name (e.g. Product Card)"),
    db: AsyncSession = Depends(get_db),
) -> SearchResultResponse:
    """
    Public catalog: Returns only APPROVED assets with optional intelligence filters.
    """
    params = SearchQueryParams(
        query=query,
        tag=tag,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        quality_tier=quality_tier,
        review_decision=review_decision,
        recommended_use=recommended_use,
    )
    return await search_service.search_database(params=params, db=db, public_only=True)


@router.get(
    "/{asset_id}",
    response_model=AssetRead,
    summary="Get asset by ID",
)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    return await asset_service.get_asset(asset_id=asset_id, db=db)


@router.get(
    "/{asset_id}/intelligence",
    response_model=Optional[AssetIntelligenceRead],
    summary="Get asset intelligence details",
)
async def get_asset_intelligence(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> Optional[AssetIntelligenceRead]:
    asset_read = await asset_service.get_asset(asset_id=asset_id, db=db)
    return asset_read.intelligence


@router.post(
    "/{asset_id}/intelligence/analyze",
    response_model=AssetRead,
    summary="Trigger or refresh UGC intelligence analysis for an asset",
)
async def analyze_asset_intelligence(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> AssetRead:
    from app.db.repositories.asset import AssetRepository

    repo = AssetRepository(db)
    asset = (
        await repo.get_by_id(int(asset_id))
        if asset_id.isdigit()
        else await repo.get_by_public_id(asset_id)
    )
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )
    await intelligence_engine.process_asset(asset=asset, db=db)
    await db.commit()
    refreshed = await repo.get_by_id(asset.id)
    return asset_service.enrich_asset_read(refreshed or asset)


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete asset",
)
async def delete_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await asset_service.delete_asset(asset_id=asset_id, db=db)


@router.get(
    "/{asset_id}/transform",
    response_model=AssetTransformResponse,
    summary="Generate custom on-demand transformation URL",
)
async def transform_asset(
    asset_id: str,
    width: Optional[int] = Query(None, ge=1, le=4096),
    height: Optional[int] = Query(None, ge=1, le=4096),
    crop: Optional[str] = Query("fill"),
    gravity: Optional[str] = Query("auto"),
    background_removal: bool = Query(False),
    format: Optional[str] = Query("auto"),
    quality: Optional[str] = Query("auto"),
    db: AsyncSession = Depends(get_db),
) -> AssetTransformResponse:
    params = AssetTransformRequest(
        width=width,
        height=height,
        crop=crop,
        gravity=gravity,
        background_removal=background_removal,
        format=format,
        quality=quality,
    )
    return await transformation_service.generate_transformation(asset_id, params, db)
