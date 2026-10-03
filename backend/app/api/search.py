from typing import Any, Dict
from fastapi import APIRouter, Query

from app.services.search_service import search_service

router = APIRouter(prefix="/assets/search", tags=["Search"])


@router.get(
    "",
    summary="Direct Cloudinary search API abstraction",
)
async def search_cloudinary_assets(
    q: str = Query(..., description="Cloudinary search expression (e.g. 'tags:nature AND format:jpg')"),
    max_results: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    return await search_service.search_cloudinary(query=q, max_results=max_results)
