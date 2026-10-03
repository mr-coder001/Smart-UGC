import os
import re
import uuid
from typing import Optional, Set
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
import filetype

from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

ALLOWED_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/avif",
    "image/heic",
    "image/heif",
}

# Signatures / magic byte detection fallbacks for supported images
def validate_admin_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Validate the incoming Admin API Key against the configured ADMIN_API_KEY.
    """
    if not api_key or api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Admin API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


def sanitize_filename(filename: str) -> str:
    """
    Sanitize client provided filename to remove directory traversals and unsafe characters.
    """
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r"[^\w\.-]", "_", clean_name)
    return clean_name or "unnamed_asset"


def detect_file_mime_and_extension(data: bytes, reported_mime: Optional[str] = None) -> tuple[str, str]:
    """
    Detect actual MIME type and extension using file headers / magic bytes.
    Never trust the client-reported MIME type without verification.
    """
    kind = filetype.guess(data)
    if kind is not None:
        detected_mime = kind.mime
        extension = kind.extension
    else:
        # Fallback check for common types if filetype doesn't match
        if data.startswith(b"\xff\xd8\xff"):
            detected_mime, extension = "image/jpeg", "jpg"
        elif data.startswith(b"\x89PNG\r\n\x1a\n"):
            detected_mime, extension = "image/png", "png"
        elif data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
            detected_mime, extension = "image/gif", "gif"
        elif data.startswith(b"RIFF") and b"WEBP" in data[8:16]:
            detected_mime, extension = "image/webp", "webp"
        elif b"ftypavif" in data[4:24]:
            detected_mime, extension = "image/avif", "avif"
        elif b"ftypheic" in data[4:24] or b"ftypmif1" in data[4:24]:
            detected_mime, extension = "image/heic", "heic"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to verify image signature or unsupported binary format."
            )

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{detected_mime}' is not supported. Allowed types: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
        )

    return detected_mime, extension


def generate_public_id(prefix: str = "asset") -> str:
    """
    Generate an internal unique ID for an asset.
    """
    return f"{prefix}_{uuid.uuid4().hex[:16]}"
