from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.db.models.asset import AssetStatus, ModerationStatus
from app.db.models.processing import TaskProcessingStatus
from app.schemas.intelligence import AssetIntelligenceRead


class AssetTagRead(BaseModel):
    id: int
    tag: str
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessingStateRead(BaseModel):
    id: int
    tagging_status: TaskProcessingStatus
    moderation_status: TaskProcessingStatus
    background_removal_status: TaskProcessingStatus
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetPresets(BaseModel):
    delivery: str
    thumbnail: str
    square: str
    landscape: str
    portrait: str


class AssetRead(BaseModel):
    id: int
    public_id: str
    cloudinary_public_id: str
    cloudinary_url: Optional[str] = None
    original_filename: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    status: AssetStatus
    moderation_status: ModerationStatus
    moderation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    decision_at: Optional[datetime] = None
    tags: List[AssetTagRead] = []
    processing_state: Optional[ProcessingStateRead] = None
    presets: Optional[AssetPresets] = None
    intelligence: Optional[AssetIntelligenceRead] = None

    model_config = ConfigDict(from_attributes=True)


class AssetListResponse(BaseModel):
    items: List[AssetRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class AssetTransformRequest(BaseModel):
    width: Optional[int] = Field(None, ge=1, le=4096)
    height: Optional[int] = Field(None, ge=1, le=4096)
    crop: Optional[str] = Field("fill", description="Crop mode e.g. fill, scale, thumb, crop, auto")
    gravity: Optional[str] = Field("auto", description="Gravity e.g. auto, face, center")
    background_removal: bool = False
    format: Optional[str] = Field("auto", description="Target format e.g. auto, webp, avif, png, jpg")
    quality: Optional[str] = Field("auto", description="Quality e.g. auto, auto:best, 80")


class AssetTransformResponse(BaseModel):
    asset_id: str
    transformation_url: str
    applied_parameters: dict
