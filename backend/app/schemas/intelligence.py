from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QualityFactor(BaseModel):
    factor: str
    passed: bool
    impact: str  # positive, neutral, negative
    description: str
    signal_used: str

    model_config = ConfigDict(from_attributes=True)


class UsageRecommendation(BaseModel):
    channel: str  # "Product Card" | "Website Hero" | "Social Feed" | "Story / Vertical" | "Marketplace Listing"
    decision: str  # "READY" | "REVIEW" | "NOT_RECOMMENDED"
    reason: str
    signals: List[str] = []
    rules_triggered: List[str] = []
    supporting_metadata: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class ExplanationBlock(BaseModel):
    summary: str
    points: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class DecisionExplanations(BaseModel):
    moderation: ExplanationBlock
    tags: ExplanationBlock
    crop: ExplanationBlock
    recommendations: ExplanationBlock
    quality: ExplanationBlock

    model_config = ConfigDict(from_attributes=True)


class TimelineStage(BaseModel):
    stage: str  # "UPLOAD" | "MODERATION" | "VISION" | "QUALITY_ANALYSIS" | "TRANSFORM" | "DELIVERY"
    status: str  # "COMPLETED" | "PENDING" | "PROCESSING" | "FAILED"
    duration_ms: Optional[int] = None
    details: str

    model_config = ConfigDict(from_attributes=True)


class AssetIntelligenceRead(BaseModel):
    quality_score: int = Field(..., ge=0, le=100)
    quality_rating: str
    quality_factors: List[QualityFactor] = []
    unavailable_signals: List[str] = []
    usage_recommendations: List[UsageRecommendation] = []
    best_use: Optional[str] = None
    recommended_format: Optional[str] = None
    review_decision: str  # "AUTO_APPROVED" | "AUTO_REJECTED" | "HUMAN_REVIEW"
    review_risk: str  # "LOW" | "MEDIUM" | "HIGH"
    review_reason: Optional[str] = None
    review_confidence: Optional[float] = None
    explanations: DecisionExplanations
    pipeline_timeline: List[TimelineStage] = []
    version: str = "1.0.0"
    status: str = "COMPLETED"
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
