import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import (
    detect_file_mime_and_extension,
    generate_public_id,
    sanitize_filename,
    validate_admin_api_key,
)
from app.services.cloudinary_service import cloudinary_service


def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd.png") == "passwd.png"
    assert sanitize_filename("my cool photo!.jpg") == "my_cool_photo_.jpg"
    assert sanitize_filename("") == "unnamed_asset"


def test_detect_file_mime_valid():
    # JPEG magic bytes: FF D8 FF
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    mime, ext = detect_file_mime_and_extension(jpeg_bytes)
    assert mime == "image/jpeg"
    assert ext in ["jpg", "jpeg"]

    # PNG magic bytes: \x89PNG\r\n\x1a\n
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    mime, ext = detect_file_mime_and_extension(png_bytes)
    assert mime == "image/png"
    assert ext == "png"


def test_detect_file_mime_invalid():
    # Executable or plain text file
    exe_bytes = b"MZ\x90\x00" + b"\x00" * 32
    with pytest.raises(HTTPException) as exc:
        detect_file_mime_and_extension(exe_bytes)
    assert exc.value.status_code in [400, 415]


def test_validate_admin_api_key():
    # Valid key
    assert validate_admin_api_key(settings.ADMIN_API_KEY) == settings.ADMIN_API_KEY

    # Invalid key
    with pytest.raises(HTTPException) as exc:
        validate_admin_api_key("wrong_key")
    assert exc.value.status_code == 401


def test_cloudinary_preset_urls():
    urls = cloudinary_service.build_preset_urls("test_asset_123")
    assert "delivery" in urls
    assert "thumbnail" in urls
    assert "square" in urls
    assert "landscape" in urls
    assert "portrait" in urls
    assert "c_fill" in urls["thumbnail"] or "fill" in urls["thumbnail"]
    assert "g_auto" in urls["thumbnail"] or "auto" in urls["thumbnail"]


def test_cloudinary_transformation_url():
    url = cloudinary_service.build_transformation_url(
        cloudinary_public_id="test_asset_123",
        width=500,
        height=500,
        crop="fill",
        gravity="auto",
        background_removal=True,
    )
    assert "test_asset_123" in url
    assert "w_500" in url or "500" in url
    assert "background_removal" in url
