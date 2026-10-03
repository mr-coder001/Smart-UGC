import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Patch db execution to verify health logic safely
        with patch("app.api.health.get_db") as mock_db:
            response = await ac.get("/api/v1/health")
    # Health endpoint responds with 200
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
