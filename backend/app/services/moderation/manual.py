from app.db.models.asset import Asset, ModerationStatus
from app.services.moderation.base import ModerationProvider, ModerationResult


class ManualModerationProvider(ModerationProvider):
    @property
    def name(self) -> str:
        return "manual"

    async def moderate(self, asset: Asset) -> ModerationResult:
        """
        In manual moderation, every new asset stays PENDING until an admin reviews it.
        """
        return ModerationResult(
            status=ModerationStatus.PENDING,
            reason="Awaiting manual review by administrator.",
            confidence=None,
            provider_name=self.name,
        )
