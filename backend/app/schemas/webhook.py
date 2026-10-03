from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CloudinaryWebhookPayload(BaseModel):
    notification_type: Optional[str] = None
    public_id: Optional[str] = None
    asset_id: Optional[str] = None
    version: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    resource_type: Optional[str] = None
    created_at: Optional[str] = None
    bytes: Optional[int] = None
    secure_url: Optional[str] = None
    url: Optional[str] = None
    moderation_status: Optional[str] = None
    moderation_kind: Optional[str] = None
    moderation_updated_at: Optional[str] = None
    tags: Optional[List[str]] = None
    raw_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WebhookResponse(BaseModel):
    success: bool
    message: str
    event_type: Optional[str] = None
    asset_id: Optional[str] = None
