import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db.database import get_db
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    """
    Test client for FastAPI ASGI endpoints.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def admin_headers():
    return {"X-Admin-API-Key": settings.ADMIN_API_KEY}
