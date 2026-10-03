from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.database import get_db
from app.schemas.webhook import WebhookResponse
from app.services.cloudinary_service import cloudinary_service
from app.services.webhook_service import webhook_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post(
    "/cloudinary",
    response_model=WebhookResponse,
    summary="Handle Cloudinary webhook notifications",
)
async def cloudinary_webhook(
    request: Request,
    x_cld_timestamp: str = Header(None, alias="X-Cld-Timestamp"),
    x_cld_signature: str = Header(None, alias="X-Cld-Signature"),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    """
    Receives asynchronous event webhooks from Cloudinary (e.g. moderation decisions, AI tag analysis).
    Idempotent and resilient to duplicates.
    """
    body_bytes = await request.body()

    # Verify signature if signature headers are provided
    if x_cld_signature and x_cld_timestamp:
        valid = cloudinary_service.verify_webhook_signature(
            body=body_bytes,
            timestamp=x_cld_timestamp,
            signature=x_cld_signature,
        )
        if not valid:
            logger.warning("Cloudinary webhook signature verification failed.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    return await webhook_service.process_cloudinary_event(payload=payload, db=db)
