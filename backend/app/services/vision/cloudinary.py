from typing import List
import cloudinary.api

from app.core.config import settings
from app.core.logging import logger
from app.services.vision.base import DetectedTag, VisionProvider


class CloudinaryVisionProvider(VisionProvider):
    @property
    def name(self) -> str:
        return "cloudinary"

    async def extract_tags(self, image_url: str, public_id: str) -> List[DetectedTag]:
        """
        Query Cloudinary asset details for actual AI generated tags (google_tagging/imagga),
        or standard tags assigned to the asset.
        Never fabricates AI tags or AI confidence if provider tagging is unavailable.
        """
        if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY:
            logger.info("Cloudinary API credentials not present; no vision provider tags available.")
            return []

        try:
            # Query Cloudinary Admin API for the asset's tags and categorization info
            details = cloudinary.api.resource(public_id, image_metadata=True, tags=True)
            tags_list: List[DetectedTag] = []

            # 1. Check categorized tags (info.categorization: google_tagging, imagga_tagging, aws_rek_tagging)
            categorization = details.get("info", {}).get("categorization", {})
            for engine, data in categorization.items():
                for tag_info in data.get("data", []):
                    tag_name = tag_info.get("tag")
                    # Cloudinary categorization returns confidence between 0.0 and 1.0
                    raw_conf = tag_info.get("confidence")
                    confidence = float(raw_conf) if raw_conf is not None else 1.0
                    if tag_name:
                        tags_list.append(DetectedTag(name=tag_name.lower().strip(), confidence=confidence))

            # 2. Check standard tags list assigned on Cloudinary
            if not tags_list and "tags" in details and details["tags"]:
                for t in details["tags"]:
                    if t and isinstance(t, str):
                        # Standard tags do not have an automated AI confidence score
                        tags_list.append(DetectedTag(name=t.lower().strip(), confidence=1.0))

            # If provider returned real tags, return them. Otherwise return empty list (no fabrication).
            return tags_list

        except Exception as e:
            logger.warning(f"Cloudinary tagging query for {public_id}: {e}; returning empty tag list.")
            return []
