import io
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from app.db.models.asset import AssetStatus, ModerationStatus
from app.db.models.processing import TaskProcessingStatus
from app.main import app


@pytest.mark.asyncio
async def test_admin_authorization_failure():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Requesting admin stats without header
        response = await ac.get("/api/v1/admin/stats")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_stats_with_valid_key():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"X-Admin-API-Key": settings.ADMIN_API_KEY}
        with patch("app.services.metrics_service.metrics_service.get_admin_metrics", new_callable=AsyncMock) as mock_metrics:
            from app.schemas.admin import AdminStatsResponse
            mock_metrics.return_value = AdminStatsResponse(
                total_assets=10,
                pending_count=2,
                approved_count=7,
                rejected_count=1,
                tag_coverage_percentage=90.0,
                automation_rate=80.0,
                average_decision_time_seconds=15.4,
                processing_status_counts={"tagging_COMPLETED": 8},
            )
            response = await ac.get("/api/v1/admin/stats", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["total_assets"] == 10
            assert data["approved_count"] == 7
            assert data["automation_rate"] == 80.0


@pytest.mark.asyncio
async def test_upload_unsupported_mime():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Send a text file pretending to be image
        file_content = b"This is plain text and not an image file header"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        response = await ac.post("/api/v1/assets", files=files)
        # Should reject invalid signature / unsupported type
        assert response.status_code in [400, 415]


@pytest.mark.asyncio
async def test_upload_oversized_file():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Simulate > 10MB payload
        oversized_content = b"\xff\xd8\xff\xe0" + b"\x00" * (11 * 1024 * 1024)
        files = {"file": ("large.jpg", io.BytesIO(oversized_content), "image/jpeg")}
        response = await ac.post("/api/v1/assets", files=files)
        assert response.status_code == 413


@pytest.mark.asyncio
async def test_cloudinary_webhook_handling():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "notification_type": "upload",
            "public_id": "test_cld_123",
            "tags": ["nature", "mountain", "outdoor"],
        }
        with patch("app.services.webhook_service.webhook_service.process_cloudinary_event", new_callable=AsyncMock) as mock_wh:
            from app.schemas.webhook import WebhookResponse
            mock_wh.return_value = WebhookResponse(
                success=True,
                message="Webhook event processed successfully.",
                event_type="upload",
                asset_id="asset_123",
            )
            response = await ac.post("/api/v1/webhooks/cloudinary", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
