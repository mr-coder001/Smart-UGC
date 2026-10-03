from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.asset import Asset
from app.db.models.processing import TaskProcessingStatus
from app.db.repositories.asset import AssetRepository
from app.db.repositories.processing import ProcessingRepository
from app.services.vision.base import VisionProvider
from app.services.vision.cloudinary import CloudinaryVisionProvider


class VisionService:
    def __init__(self, provider: Optional[VisionProvider] = None):
        self.provider = provider or CloudinaryVisionProvider()

    def set_provider(self, provider: VisionProvider) -> None:
        self.provider = provider
        logger.info(f"Switched VisionProvider to: {provider.name}")

    async def process_asset_tags(self, asset: Asset, db: AsyncSession) -> List[Tuple[str, float]]:
        """
        Extract vision tags from provider and persist them into the asset's database record.
        """
        asset_repo = AssetRepository(db)
        processing_repo = ProcessingRepository(db)

        await processing_repo.update_tagging_status(asset.id, TaskProcessingStatus.PROCESSING)

        try:
            detected_tags = await self.provider.extract_tags(
                image_url=asset.cloudinary_url or "",
                public_id=asset.cloudinary_public_id,
            )

            tag_tuples = [(t.name, t.confidence) for t in detected_tags]
            await asset_repo.add_tags(asset.id, tag_tuples)
            await processing_repo.update_tagging_status(asset.id, TaskProcessingStatus.COMPLETED)
            return tag_tuples
        except Exception as e:
            logger.error(f"Failed to process vision tags for asset {asset.id}: {e}")
            await processing_repo.update_tagging_status(
                asset.id, TaskProcessingStatus.FAILED, error_message=str(e)
            )
            return []


vision_service = VisionService()
