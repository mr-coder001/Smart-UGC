import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional
import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils

from app.core.config import settings
from app.core.logging import logger


class CloudinaryService:
    def __init__(self):
        self._configure()

    def _configure(self):
        # Configure Cloudinary SDK using settings
        if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )
            self.configured = True
        else:
            self.configured = False
            logger.warning("Cloudinary credentials not set. Running in mock/fallback mode.")

    def is_configured(self) -> bool:
        if not self.configured and settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
            self._configure()
        return self.configured

    def upload_image(
        self,
        file_bytes: bytes,
        public_id: str,
        folder: str = "assets",
        auto_tagging: bool = True,
        notification_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload image binary to Cloudinary with secure parameters and optional auto-tagging.
        """
        if not self.is_configured():
            # Fallback mock for local testing when Cloudinary secrets are not yet provided
            logger.info(f"Cloudinary not configured. Generating mock upload for public_id={public_id}")
            return {
                "public_id": "sample",
                "version": int(time.time()),
                "width": 1200,
                "height": 800,
                "format": "jpg",
                "bytes": len(file_bytes),
                "secure_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
                "tags": ["object", "photo"],
            }

        options: Dict[str, Any] = {
            "public_id": public_id,
            "folder": folder,
            "resource_type": "image",
            "overwrite": True,
        }
        if notification_url:
            options["notification_url"] = notification_url

        # Trigger auto-tagging if requested
        if auto_tagging:
            # categorization="google_tagging,imagga_tagging" or auto_tagging=0.6
            options["auto_tagging"] = 0.6

        result = cloudinary.uploader.upload(file_bytes, **options)
        return result

    def delete_image(self, public_id: str) -> Dict[str, Any]:
        """
        Delete an image asset from Cloudinary.
        """
        if not self.is_configured():
            return {"result": "ok"}
        return cloudinary.uploader.destroy(public_id, resource_type="image")

    def build_delivery_url(self, cloudinary_public_id: str) -> str:
        """
        Default optimized delivery URL (f_auto, q_auto).
        """
        if not self.is_configured():
            pid = "sample.jpg" if cloudinary_public_id.startswith("claudinary_assets/") else cloudinary_public_id
            return f"https://res.cloudinary.com/demo/image/upload/f_auto,q_auto/{pid}"

        url, _ = cloudinary.utils.cloudinary_url(
            cloudinary_public_id,
            fetch_format="auto",
            quality="auto",
            secure=True,
        )
        return url

    def build_preset_urls(self, cloudinary_public_id: str) -> Dict[str, str]:
        """
        Generate subject-aware cropped preset URLs.
        - thumbnail: 300x300
        - square: 1080x1080
        - landscape: 1600x900
        - portrait: 1080x1350
        """
        presets = {
            "thumbnail": {"width": 300, "height": 300, "crop": "fill", "gravity": "auto"},
            "square": {"width": 1080, "height": 1080, "crop": "fill", "gravity": "auto"},
            "landscape": {"width": 1600, "height": 900, "crop": "fill", "gravity": "auto"},
            "portrait": {"width": 1080, "height": 1350, "crop": "fill", "gravity": "auto"},
        }

        urls = {
            "delivery": self.build_delivery_url(cloudinary_public_id)
        }

        for preset_name, config in presets.items():
            if not self.is_configured():
                w, h = config["width"], config["height"]
                pid = "sample.jpg" if cloudinary_public_id.startswith("claudinary_assets/") else cloudinary_public_id
                urls[preset_name] = f"https://res.cloudinary.com/demo/image/upload/c_fill,g_auto,w_{w},h_{h},f_auto,q_auto/{pid}"
            else:
                url, _ = cloudinary.utils.cloudinary_url(
                    cloudinary_public_id,
                    width=config["width"],
                    height=config["height"],
                    crop=config["crop"],
                    gravity=config["gravity"],
                    fetch_format="auto",
                    quality="auto",
                    secure=True,
                )
                urls[preset_name] = url

        return urls

    def build_transformation_url(
        self,
        cloudinary_public_id: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crop: Optional[str] = "fill",
        gravity: Optional[str] = "auto",
        background_removal: bool = False,
        target_format: Optional[str] = "auto",
        quality: Optional[str] = "auto",
    ) -> str:
        """
        Generate on-demand transformation URL without creating permanent duplicate files.
        """
        transformation_args: Dict[str, Any] = {
            "secure": True,
            "fetch_format": target_format or "auto",
            "quality": quality or "auto",
        }

        if width:
            transformation_args["width"] = width
        if height:
            transformation_args["height"] = height
        if crop:
            transformation_args["crop"] = crop
        if gravity:
            transformation_args["gravity"] = gravity

        if background_removal:
            # Cloudinary background removal transformation effect
            transformation_args["effect"] = "background_removal"

        if not self.is_configured():
            # Build mock URL for development
            parts = [f"f_{target_format or 'auto'}", f"q_{quality or 'auto'}"]
            if width:
                parts.append(f"w_{width}")
            if height:
                parts.append(f"h_{height}")
            if crop:
                parts.append(f"c_{crop}")
            if gravity:
                parts.append(f"g_{gravity}")
            if background_removal:
                parts.append("e_background_removal")
            pid = "sample.jpg" if cloudinary_public_id.startswith("claudinary_assets/") else cloudinary_public_id
            return f"https://res.cloudinary.com/demo/image/upload/{','.join(parts)}/{pid}"

        url, _ = cloudinary.utils.cloudinary_url(cloudinary_public_id, **transformation_args)
        return url

    def verify_webhook_signature(self, body: bytes, timestamp: str, signature: str) -> bool:
        """
        Verify Cloudinary webhook signature using HMAC-SHA1 or HMAC-SHA256 with API secret.
        """
        if not settings.CLOUDINARY_API_SECRET and not settings.CLOUDINARY_WEBHOOK_SECRET:
            return True

        secret = settings.CLOUDINARY_WEBHOOK_SECRET or settings.CLOUDINARY_API_SECRET
        data_to_sign = body.decode("utf-8", errors="ignore") + timestamp + secret
        expected_sig = hashlib.sha1(data_to_sign.encode("utf-8")).hexdigest()

        return hmac.compare_digest(expected_sig, signature)


cloudinary_service = CloudinaryService()
