from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.asset import AssetRead


class SearchQueryParams(BaseModel):
    query: Optional[str] = Field(None, description="Text query across filename or tags")
    tag: Optional[str] = Field(None, description="Exact tag filter")
    status: Optional[str] = Field(None, description="Filter by status")
    moderation_status: Optional[str] = Field(None, description="Filter by moderation status")
    min_confidence: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    quality_tier: Optional[str] = Field(None, description="Filter by quality tier (high, medium, low)")
    review_decision: Optional[str] = Field(None, description="Filter by review decision (AUTO_APPROVED, AUTO_REJECTED, HUMAN_REVIEW)")
    recommended_use: Optional[str] = Field(None, description="Filter by recommended channel use")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", description="Field to sort by (created_at, file_size, width, height)")
    sort_order: str = Field("desc", description="Sort direction (asc, desc)")


class SearchResultResponse(BaseModel):
    items: List[AssetRead]
    total: int
    page: int
    page_size: int
    total_pages: int
    query: Optional[str] = None
    applied_filters: dict
