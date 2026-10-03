from typing import Dict, Optional
from pydantic import BaseModel, Field


class ModerationDecisionRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Optional or mandatory reason for moderation decision")


class AdminStatsResponse(BaseModel):
    total_assets: int
    pending_count: int
    approved_count: int
    rejected_count: int
    tag_coverage_percentage: float
    automation_rate: float
    average_decision_time_seconds: Optional[float] = None
    processing_status_counts: Dict[str, int]
    # UGC Intelligence Analytics
    average_quality_score: Optional[float] = None
    auto_approved_percentage: Optional[float] = None
    human_review_percentage: Optional[float] = None
    production_ready_percentage: Optional[float] = None
    most_common_review_reason: Optional[str] = None
    total_intelligence_analyzed: int = 0
