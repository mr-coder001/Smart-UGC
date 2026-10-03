from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.assets import router as assets_router
from app.api.health import router as health_router
from app.api.search import router as search_router
from app.api.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(assets_router)
api_router.include_router(search_router)
api_router.include_router(admin_router)
api_router.include_router(webhooks_router)

__all__ = ["api_router"]
