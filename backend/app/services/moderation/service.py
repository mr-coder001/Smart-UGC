from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.asset import Asset, AssetStatus, ModerationStatus
from app.db.repositories.asset import AssetRepository
from app.services.moderation.base import ModerationProvider, ModerationResult
from app.services.moderation.manual import ManualModerationProvider


class ModerationService:
    def __init__(self, provider: Optional[ModerationProvider] = None):
        # Default to manual moderation provider as required by specification
        self.provider = provider or ManualModerationProvider()

    def set_provider(self, provider: ModerationProvider) -> None:
        self.provider = provider
        logger.info(f"Switched ModerationProvider to: {provider.name}")

    async def evaluate_asset(self, asset: Asset, db: AsyncSession) -> ModerationResult:
        result = await self.provider.moderate(asset)
        repo = AssetRepository(db)

        # Update asset status based on moderation evaluation
        if result.status == ModerationStatus.APPROVED:
            await repo.update_moderation(asset, AssetStatus.APPROVED, ModerationStatus.APPROVED, reason=result.reason)
        elif result.status == ModerationStatus.REJECTED:
            await repo.update_moderation(asset, AssetStatus.REJECTED, ModerationStatus.REJECTED, reason=result.reason)
        else:
            await repo.update_moderation(asset, AssetStatus.PENDING, ModerationStatus.PENDING, reason=result.reason)

        return result


moderation_service = ModerationService()
