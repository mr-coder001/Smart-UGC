from abc import ABC, abstractmethod
from typing import List, Tuple
from pydantic import BaseModel


class DetectedTag(BaseModel):
    name: str
    confidence: float


class VisionProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the vision provider (e.g. cloudinary, google_vision, aws_rekognition)"""
        pass

    @abstractmethod
    async def extract_tags(self, image_url: str, public_id: str) -> List[DetectedTag]:
        """
        Extract scene/object tags with confidence score.
        """
        pass
