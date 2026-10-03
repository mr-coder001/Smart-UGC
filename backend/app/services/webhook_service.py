from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.models.asset import AssetStatus, ModerationStatus
from app.db.models.processing import TaskProcessingStatus
from app.db.repositories.asset import AssetRepository
from app.db.repositories.processing import ProcessingRepository
from app.schemas.webhook import CloudinaryWebhookPayload, WebhookResponse


class WebhookService:
    async def process_cloudinary_event(
        self,
        payload: Dict[str, Any],
        db: AsyncSession,
    ) -> WebhookResponse:
        """
        Handle incoming Cloudinary webhooks idempotently.
        """
        notification_type = payload.get("notification_type") or "unknown"
        public_id = payload.get("public_id")
        asset_id = payload.get("asset_id")

        logger.info(f"Received Cloudinary webhook event: type={notification_type}, public_id={public_id}")

        if not public_id:
            return WebhookResponse(
                success=True,
                message="Ignored webhook without public_id",
                event_type=notification_type,
            )

        asset_repo = AssetRepository(db)
        processing_repo = ProcessingRepository(db)

        # Lookup asset by cloudinary_public_id or internal public_id
        asset = await asset_repo.get_by_cloudinary_public_id(public_id)
        if not asset and "/" in public_id:
            short_id = public_id.split("/")[-1]
            asset = await asset_repo.get_by_public_id(short_id)

        if not asset:
            logger.warning(f"Webhook received for unknown asset: {public_id}")
            return WebhookResponse(
                success=True,
                message=f"No matching asset found for {public_id}. Handled idempotently.",
                event_type=notification_type,
            )

        # 1. Handle auto-tagging or categorization completion
        tags = payload.get("tags") or []
        if tags:
            tag_tuples = [(t, 0.95) for t in tags]
            await asset_repo.add_tags(asset.id, tag_tuples)
            await processing_repo.update_tagging_status(asset.id, TaskProcessingStatus.COMPLETED)

        # 2. Handle Cloudinary add-on moderation event (e.g. webpurify or aws_rek)
        moderation_status_str = payload.get("moderation_status")
        if moderation_status_str:
            if moderation_status_str.lower() == "approved":
                await asset_repo.update_moderation(
                    asset, AssetStatus.APPROVED, ModerationStatus.APPROVED, reason="Approved via webhook"
                )
            elif moderation_status_str.lower() == "rejected":
                await asset_repo.update_moderation(
                    asset, AssetStatus.REJECTED, ModerationStatus.REJECTED, reason="Rejected via webhook"
                )

        await db.commit()

        return WebhookResponse(
            success=True,
            message="Webhook event processed successfully.",
            event_type=notification_type,
            asset_id=asset.public_id,
        )


webhook_service = WebhookService()
