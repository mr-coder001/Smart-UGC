from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

from app.db.models.asset import Asset, ModerationStatus


class ModerationResult(BaseModel):
    status: ModerationStatus
    reason: Optional[str] = None
    confidence: Optional[float] = None
    provider_name: str


class ModerationProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the moderation provider (e.g. manual, aws_rekognition, webpurify)"""
        pass

    @abstractmethod
    async def moderate(self, asset: Asset) -> ModerationResult:
        """
        Evaluate an asset for moderation compliance.
        """
        pass
