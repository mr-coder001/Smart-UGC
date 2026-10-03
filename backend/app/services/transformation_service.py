from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.asset import AssetRepository
from app.schemas.asset import AssetTransformRequest, AssetTransformResponse
from app.services.cloudinary_service import cloudinary_service


class TransformationService:
    async def generate_transformation(
        self,
        asset_id: str,
        params: AssetTransformRequest,
        db: AsyncSession,
    ) -> AssetTransformResponse:
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

        url = cloudinary_service.build_transformation_url(
            cloudinary_public_id=asset.cloudinary_public_id,
            width=params.width,
            height=params.height,
            crop=params.crop,
            gravity=params.gravity,
            background_removal=params.background_removal,
            target_format=params.format,
            quality=params.quality,
        )

        return AssetTransformResponse(
            asset_id=asset.public_id,
            transformation_url=url,
            applied_parameters=params.model_dump(),
        )


transformation_service = TransformationService()
