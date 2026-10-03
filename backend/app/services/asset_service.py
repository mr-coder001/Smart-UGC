from typing import Optional
import time
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.security import (
    detect_file_mime_and_extension,
    generate_public_id,
    sanitize_filename,
)
from app.db.models.asset import Asset, AssetStatus, ModerationStatus
from app.db.repositories.asset import AssetRepository
from app.schemas.asset import AssetPresets, AssetRead
from app.schemas.intelligence import AssetIntelligenceRead
from app.services.cloudinary_service import cloudinary_service
from app.services.intelligence.service import intelligence_engine
from app.services.moderation.service import moderation_service
from app.services.vision.service import vision_service


class AssetService:
    @staticmethod
    def enrich_asset_read(asset: Asset) -> AssetRead:
        """
        Enrich an Asset model instance with Cloudinary delivery presets and UGC intelligence.
        """
        presets_dict = cloudinary_service.build_preset_urls(asset.cloudinary_public_id)
        presets = AssetPresets(
            delivery=presets_dict["delivery"],
            thumbnail=presets_dict["thumbnail"],
            square=presets_dict["square"],
            landscape=presets_dict["landscape"],
            portrait=presets_dict["portrait"],
        )

        intelligence_data: Optional[AssetIntelligenceRead] = None
        if getattr(asset, "intelligence", None):
            try:
                intelligence_data = AssetIntelligenceRead.model_validate(asset.intelligence)
            except Exception as e:
                logger.warning(f"Could not parse asset intelligence for asset {asset.id}: {e}")

        return AssetRead(
            id=asset.id,
            public_id=asset.public_id,
            cloudinary_public_id=asset.cloudinary_public_id,
            cloudinary_url=asset.cloudinary_url or presets_dict["delivery"],
            original_filename=asset.original_filename,
            mime_type=asset.mime_type,
            file_size=asset.file_size,
            width=asset.width,
            height=asset.height,
            status=asset.status,
            moderation_status=asset.moderation_status,
            moderation_reason=asset.moderation_reason,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            approved_at=asset.approved_at,
            rejected_at=asset.rejected_at,
            decision_at=asset.decision_at,
            tags=asset.tags or [],
            processing_state=asset.processing_state,
            presets=presets,
            intelligence=intelligence_data,
        )

    async def upload_asset(
        self,
        file: UploadFile,
        db: AsyncSession,
    ) -> AssetRead:
        """
        Complete upload pipeline:
        1. Read binary
        2. Validate size (<= 10MB)
        3. Detect MIME type & file signature
        4. Upload to Cloudinary
        5. Persist to PostgreSQL
        6. Trigger auto-tagging & moderation evaluation
        """
        # Read file into memory (under 10MB, never stored permanently on disk)
        contents = await file.read()
        file_size = len(contents)

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                detail=f"File exceeds maximum allowed size of {max_mb} MB.",
            )

        # Validate MIME and file signature
        mime_type, ext = detect_file_mime_and_extension(contents, file.content_type)
        safe_filename = sanitize_filename(file.filename or f"image.{ext}")
        public_id = generate_public_id()

        # Cloudinary upload
        stage_timings = {}
        t_upload_start = time.perf_counter()
        try:
            cloud_result = cloudinary_service.upload_image(
                file_bytes=contents,
                public_id=public_id,
                folder="claudinary_assets",
                auto_tagging=True,
            )
            stage_timings["UPLOAD"] = int((time.perf_counter() - t_upload_start) * 1000)
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to upload asset to media storage: {str(e)}",
            )

        cloudinary_public_id = cloud_result.get("public_id", f"claudinary_assets/{public_id}")
        width = cloud_result.get("width")
        height = cloud_result.get("height")
        secure_url = cloud_result.get("secure_url")

        # Save to database
        repo = AssetRepository(db)
        asset = await repo.create(
            public_id=public_id,
            cloudinary_public_id=cloudinary_public_id,
            original_filename=safe_filename,
            mime_type=mime_type,
            file_size=file_size,
            width=width,
            height=height,
            cloudinary_url=secure_url,
            status=AssetStatus.PENDING,
            moderation_status=ModerationStatus.PENDING,
        )

        # Trigger vision auto-tagging
        t_vision_start = time.perf_counter()
        try:
            await vision_service.process_asset_tags(asset, db)
        except Exception as e:
            logger.warning(f"Vision auto-tagging error: {e}")
        stage_timings["VISION"] = int((time.perf_counter() - t_vision_start) * 1000)

        # Trigger moderation evaluation (defaults to manual pending review)
        t_mod_start = time.perf_counter()
        mod_result = None
        try:
            mod_result = await moderation_service.evaluate_asset(asset, db)
        except Exception as e:
            logger.warning(f"Moderation evaluation error: {e}")
        stage_timings["MODERATION"] = int((time.perf_counter() - t_mod_start) * 1000)

        # Trigger UGC Intelligence Engine (Failure-isolated)
        t_qa_start = time.perf_counter()
        try:
            mod_conf = getattr(mod_result, "confidence", None) if mod_result else None
            mod_violations = 1 if getattr(mod_result, "status", None) == ModerationStatus.REJECTED else 0
            stage_timings["QUALITY_ANALYSIS"] = int((time.perf_counter() - t_qa_start) * 1000)
            await intelligence_engine.process_asset(
                asset=asset,
                db=db,
                stage_timings_ms=stage_timings,
                moderation_confidence=mod_conf,
                moderation_violations=mod_violations,
            )
        except Exception as exc:
            logger.error(f"UGC Intelligence processing failed (isolated): {exc}")

        await db.commit()
        # Reload with relationships
        full_asset = await repo.get_by_id(asset.id)
        return self.enrich_asset_read(full_asset or asset)

    async def get_asset(self, asset_id: str, db: AsyncSession) -> AssetRead:
        repo = AssetRepository(db)
        if asset_id.isdigit():
            asset = await repo.get_by_id(int(asset_id))
        else:
            asset = await repo.get_by_public_id(asset_id)

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found",
            )
        return self.enrich_asset_read(asset)

    async def delete_asset(self, asset_id: str, db: AsyncSession) -> None:
        repo = AssetRepository(db)
        if asset_id.isdigit():
            asset = await repo.get_by_id(int(asset_id))
        else:
            asset = await repo.get_by_public_id(asset_id)

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found",
            )

        # Remove from Cloudinary
        try:
            cloudinary_service.delete_image(asset.cloudinary_public_id)
        except Exception as e:
            logger.warning(f"Could not delete asset {asset.cloudinary_public_id} from Cloudinary: {e}")

        # Remove from Database
        await repo.delete(asset)
        await db.commit()


asset_service = AssetService()
