import asyncio
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.rate_limit import get_redis
from app.db.database import get_db

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any], tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Service health check endpoint verifying database and Redis readiness.
    """
    db_status = "healthy"
    try:
        from app.db.database import get_session_factory
        factory = await get_session_factory()
        async with factory() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=2.0)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    redis_status = "healthy"
    try:
        redis_conn = await asyncio.wait_for(get_redis(), timeout=1.5)
        if redis_conn:
            await asyncio.wait_for(redis_conn.ping(), timeout=1.5)
        else:
            redis_status = "unconfigured_or_fallback"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if "unhealthy" not in db_status else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "redis": redis_status,
        "version": "1.0.0",
    }
