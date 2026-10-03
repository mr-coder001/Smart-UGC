from typing import Any, Dict, List, Tuple
from pydantic import BaseModel

from app.db.models.asset import Asset, ModerationStatus


# Centralized, explicit internal usage profile specifications
# All recommendation decisions are evaluated deterministically against these configured thresholds
USAGE_PROFILES: Dict[str, Dict[str, Any]] = {
    "product_card": {
        "channel": "Product Card",
        "target_format": "1:1 Square",
        "min_width": 600,
        "min_height": 600,
        "preferred_aspect_ratio_min": 0.80,
        "preferred_aspect_ratio_max": 1.25,
        "acceptable_aspect_ratio_min": 0.60,
        "acceptable_aspect_ratio_max": 1.60,
        "min_quality_score": 60,
        "review_quality_score": 45,
        "requires_approved_moderation": False,
        "preferred_orientation": "square",
        "description": "Square or near-square product catalog card requiring balanced framing and crisp detail.",
    },
    "website_hero": {
        "channel": "Website Hero",
        "target_format": "16:9 Landscape",
        "min_width": 1400,
        "min_height": 500,
        "preferred_aspect_ratio_min": 1.40,
        "preferred_aspect_ratio_max": 3.00,
        "acceptable_aspect_ratio_min": 1.20,
        "acceptable_aspect_ratio_max": 3.50,
        "min_quality_score": 70,
        "review_quality_score": 55,
        "requires_approved_moderation": False,
        "preferred_orientation": "landscape",
        "description": "Full-bleed desktop banner requiring landscape orientation and high horizontal pixel count.",
    },
    "social_feed": {
        "channel": "Social Feed",
        "target_format": "4:5 Portrait",
        "min_width": 800,
        "min_height": 800,
        "preferred_aspect_ratio_min": 0.75,
        "preferred_aspect_ratio_max": 1.80,
        "acceptable_aspect_ratio_min": 0.50,
        "acceptable_aspect_ratio_max": 2.20,
        "min_quality_score": 60,
        "review_quality_score": 45,
        "requires_approved_moderation": False,
        "preferred_orientation": "any",
        "description": "In-feed image post accommodating square, vertical, or landscape feed aspect ratios.",
    },
    "story_vertical": {
        "channel": "Story / Vertical",
        "target_format": "9:16 Vertical",
        "min_width": 600,
        "min_height": 1080,
        "preferred_aspect_ratio_min": 0.45,
        "preferred_aspect_ratio_max": 0.75,
        "acceptable_aspect_ratio_min": 0.40,
        "acceptable_aspect_ratio_max": 1.00,
        "min_quality_score": 65,
        "review_quality_score": 50,
        "requires_approved_moderation": False,
        "preferred_orientation": "portrait",
        "description": "Full-height vertical mobile experience matching standard 9:16 portrait viewports.",
    },
    "marketplace_listing": {
        "channel": "Marketplace Listing",
        "target_format": "1:1 Square",
        "min_width": 800,
        "min_height": 800,
        "preferred_aspect_ratio_min": 0.80,
        "preferred_aspect_ratio_max": 1.25,
        "acceptable_aspect_ratio_min": 0.65,
        "acceptable_aspect_ratio_max": 1.50,
        "min_quality_score": 65,
        "review_quality_score": 50,
        "requires_approved_moderation": True,
        "preferred_orientation": "square",
        "description": "High-definition catalog listing requiring clean framing, high resolution, and verified moderation approval.",
    },
}


class ChannelRecommendation(BaseModel):
    channel: str
    decision: str  # "READY" | "REVIEW" | "NOT_RECOMMENDED"
    reason: str
    signals: List[str] = []
    rules_triggered: List[str] = []
    supporting_metadata: Dict[str, Any] = {}


class UsageRecommendationResult(BaseModel):
    recommendations: List[ChannelRecommendation]
    best_use: str
    recommended_format: str


class UsageRecommendationEngine:
    PROFILES = USAGE_PROFILES

    def generate_recommendations(
        self, asset: Asset, quality_score: int
    ) -> UsageRecommendationResult:
        """
        Evaluate asset against concrete channel constraints and generate channel suitability decisions.
        Uses strictly measured properties (dimensions, aspect ratio, quality score, moderation status).
        Never cites external platform specifications unless explicitly configured.
        """
        width = asset.width or 0
        height = asset.height or 0
        ratio = (width / height) if (width > 0 and height > 0) else 1.0
        is_rejected = asset.moderation_status == ModerationStatus.REJECTED
        is_approved = asset.moderation_status == ModerationStatus.APPROVED

        recommendations: List[ChannelRecommendation] = []

        # Common metadata dictionary
        base_meta = {
            "width": width,
            "height": height,
            "aspect_ratio": round(ratio, 2),
            "quality_score": quality_score,
            "moderation_status": asset.moderation_status.value if asset.moderation_status else "UNKNOWN",
        }

        # 1. Product Card
        pc_conf = self.PROFILES["product_card"]
        pc_rules: List[str] = []
        if is_rejected:
            pc_decision = "NOT_RECOMMENDED"
            pc_reason = "Asset has been rejected during moderation inspection."
            pc_rules.append("moderation_rejected")
        elif min(width, height) >= pc_conf["min_width"] and pc_conf["preferred_aspect_ratio_min"] <= ratio <= pc_conf["preferred_aspect_ratio_max"] and quality_score >= pc_conf["min_quality_score"]:
            pc_decision = "READY"
            pc_reason = f"Measured resolution ({width}×{height} px) and aspect ratio ({ratio:.2f}:1) satisfy standard 1:1 product card requirements without substantial cropping."
            pc_rules.extend(["resolution_adequate", "aspect_ratio_aligned", "quality_adequate"])
        elif min(width, height) >= 400 and quality_score >= pc_conf["review_quality_score"]:
            pc_decision = "REVIEW"
            if ratio < pc_conf["preferred_aspect_ratio_min"] or ratio > pc_conf["preferred_aspect_ratio_max"]:
                pc_reason = f"Aspect ratio ({ratio:.2f}:1) deviates from 1:1 target; subject-aware cropping is recommended."
                pc_rules.append("aspect_ratio_requires_crop")
            else:
                pc_reason = f"Resolution ({width}×{height} px) meets card display but is below preferred {pc_conf['min_width']}px baseline for zoom."
                pc_rules.append("resolution_borderline")
        else:
            pc_decision = "NOT_RECOMMENDED"
            if min(width, height) < 400:
                pc_reason = f"Measured resolution ({width}×{height} px) is below the internal 400×400 px minimum for product cards."
                pc_rules.append("resolution_insufficient")
            else:
                pc_reason = f"Quality score ({quality_score}/100) is below the minimum threshold ({pc_conf['review_quality_score']} pts) for product cards."
                pc_rules.append("quality_insufficient")

        recommendations.append(
            ChannelRecommendation(
                channel=pc_conf["channel"],
                decision=pc_decision,
                reason=pc_reason,
                signals=[f"dimensions:{width}x{height}", f"quality_score:{quality_score}", f"aspect_ratio:{ratio:.2f}"],
                rules_triggered=pc_rules,
                supporting_metadata=base_meta,
            )
        )

        # 2. Website Hero
        hero_conf = self.PROFILES["website_hero"]
        hero_rules: List[str] = []
        if is_rejected:
            hero_decision = "NOT_RECOMMENDED"
            hero_reason = "Asset has been rejected during moderation inspection."
            hero_rules.append("moderation_rejected")
        elif width >= hero_conf["min_width"] and ratio >= hero_conf["preferred_aspect_ratio_min"] and quality_score >= hero_conf["min_quality_score"]:
            hero_decision = "READY"
            hero_reason = f"Measured width ({width} px) and landscape ratio ({ratio:.2f}:1) satisfy internal hero banner specifications (min {hero_conf['min_width']} px width, {hero_conf['preferred_aspect_ratio_min']:.2f}:1 ratio)."
            hero_rules.extend(["width_adequate", "aspect_ratio_landscape", "quality_adequate"])
        elif width >= 1000 and ratio >= hero_conf["acceptable_aspect_ratio_min"] and quality_score >= hero_conf["review_quality_score"]:
            hero_decision = "REVIEW"
            hero_reason = f"Width ({width} px) and aspect ratio ({ratio:.2f}:1) require responsive scaling or vertical focal cropping for wide banners."
            hero_rules.append("width_or_ratio_borderline")
        else:
            hero_decision = "NOT_RECOMMENDED"
            if width < 1000:
                hero_reason = f"Horizontal resolution ({width} px) is below the configured internal threshold (1000 px minimum) for hero displays."
                hero_rules.append("width_insufficient")
            else:
                hero_reason = f"Aspect ratio ({ratio:.2f}:1) is non-landscape; hero banners require a minimum {hero_conf['acceptable_aspect_ratio_min']:.2f}:1 landscape ratio."
                hero_rules.append("aspect_ratio_non_landscape")

        recommendations.append(
            ChannelRecommendation(
                channel=hero_conf["channel"],
                decision=hero_decision,
                reason=hero_reason,
                signals=[f"width:{width}", f"aspect_ratio:{ratio:.2f}", f"quality_score:{quality_score}"],
                rules_triggered=hero_rules,
                supporting_metadata=base_meta,
            )
        )

        # 3. Social Feed
        soc_conf = self.PROFILES["social_feed"]
        soc_rules: List[str] = []
        if is_rejected:
            soc_decision = "NOT_RECOMMENDED"
            soc_reason = "Asset has been rejected during moderation inspection."
            soc_rules.append("moderation_rejected")
        elif max(width, height) >= soc_conf["min_width"] and soc_conf["preferred_aspect_ratio_min"] <= ratio <= soc_conf["preferred_aspect_ratio_max"] and quality_score >= soc_conf["min_quality_score"]:
            soc_decision = "READY"
            soc_reason = f"Measured dimensions ({width}×{height} px) and ratio ({ratio:.2f}:1) fit standard in-feed social display parameters."
            soc_rules.extend(["dimensions_adequate", "ratio_in_feed", "quality_adequate"])
        elif max(width, height) >= 500 and quality_score >= soc_conf["review_quality_score"]:
            soc_decision = "REVIEW"
            soc_reason = f"Aspect ratio ({ratio:.2f}:1) requires subject-aware smart cropping (g_auto) to center focal elements in standard feed containers."
            soc_rules.append("crop_centering_recommended")
        else:
            soc_decision = "NOT_RECOMMENDED"
            soc_reason = f"Measured resolution ({width}×{height} px) is below the configured 500 px minimum threshold for social feeds."
            soc_rules.append("resolution_insufficient")

        recommendations.append(
            ChannelRecommendation(
                channel=soc_conf["channel"],
                decision=soc_decision,
                reason=soc_reason,
                signals=[f"dimensions:{width}x{height}", f"quality_score:{quality_score}"],
                rules_triggered=soc_rules,
                supporting_metadata=base_meta,
            )
        )

        # 4. Story / Vertical
        story_conf = self.PROFILES["story_vertical"]
        story_rules: List[str] = []
        if is_rejected:
            story_decision = "NOT_RECOMMENDED"
            story_reason = "Asset has been rejected during moderation inspection."
            story_rules.append("moderation_rejected")
        elif height >= story_conf["min_height"] and story_conf["preferred_aspect_ratio_min"] <= ratio <= story_conf["preferred_aspect_ratio_max"] and quality_score >= story_conf["min_quality_score"]:
            story_decision = "READY"
            story_reason = f"Vertical portrait framing ({ratio:.2f}:1) and height ({height} px) align naturally with 9:16 vertical mobile containers."
            story_rules.extend(["portrait_ratio_aligned", "height_adequate", "quality_adequate"])
        elif height >= 800 and ratio <= story_conf["acceptable_aspect_ratio_max"] and quality_score >= story_conf["review_quality_score"]:
            story_decision = "REVIEW"
            story_reason = f"Near-square or moderate portrait ratio ({ratio:.2f}:1) requires vertical smart-crop expansion to fill 9:16 mobile viewports."
            story_rules.append("crop_to_vertical_needed")
        else:
            story_decision = "NOT_RECOMMENDED"
            if ratio > 1.0:
                story_reason = f"Aspect ratio ({ratio:.2f}:1) is landscape/horizontal; converting to 9:16 (0.56:1) vertical format requires substantial cropping."
                story_rules.append("landscape_to_vertical_mismatch")
            else:
                story_reason = f"Vertical resolution ({height} px) is below the configured 800 px minimum for vertical displays."
                story_rules.append("height_insufficient")

        recommendations.append(
            ChannelRecommendation(
                channel=story_conf["channel"],
                decision=story_decision,
                reason=story_reason,
                signals=[f"height:{height}", f"aspect_ratio:{ratio:.2f}"],
                rules_triggered=story_rules,
                supporting_metadata=base_meta,
            )
        )

        # 5. Marketplace Listing (Strict internal thresholds: approved moderation, high res, square framing)
        mkt_conf = self.PROFILES["marketplace_listing"]
        mkt_rules: List[str] = []
        if is_rejected:
            mkt_decision = "NOT_RECOMMENDED"
            mkt_reason = "Asset has been rejected during moderation inspection."
            mkt_rules.append("moderation_rejected")
        elif not is_approved:
            # When moderation is pending or not yet approved
            mkt_decision = "REVIEW" if (min(width, height) >= 600 and quality_score >= mkt_conf["review_quality_score"]) else "NOT_RECOMMENDED"
            mkt_reason = f"Requires approved moderation status before listing syndication (current status: {asset.moderation_status.value if asset.moderation_status else 'PENDING'})."
            mkt_rules.append("moderation_not_approved")
        elif min(width, height) >= mkt_conf["min_width"] and mkt_conf["preferred_aspect_ratio_min"] <= ratio <= mkt_conf["preferred_aspect_ratio_max"] and quality_score >= mkt_conf["min_quality_score"]:
            mkt_decision = "READY"
            mkt_reason = f"Verified safe status, high resolution ({width}×{height} px), and near-square framing ({ratio:.2f}:1) satisfy internal listing profile criteria."
            mkt_rules.extend(["moderation_approved", "resolution_adequate", "framing_aligned", "quality_adequate"])
        elif min(width, height) >= 600 and quality_score >= mkt_conf["review_quality_score"]:
            mkt_decision = "REVIEW"
            mkt_reason = f"Resolution ({width}×{height} px) is below preferred {mkt_conf['min_width']}×{mkt_conf['min_height']} px baseline or framing ({ratio:.2f}:1) requires cropping to square."
            mkt_rules.append("resolution_or_framing_borderline")
        else:
            mkt_decision = "NOT_RECOMMENDED"
            mkt_reason = f"Resolution ({width}×{height} px) is below the configured 600×600 px internal threshold for listing cards."
            mkt_rules.append("resolution_insufficient")

        recommendations.append(
            ChannelRecommendation(
                channel=mkt_conf["channel"],
                decision=mkt_decision,
                reason=mkt_reason,
                signals=[f"quality_score:{quality_score}", f"moderation:{asset.moderation_status.value if asset.moderation_status else 'UNKNOWN'}"],
                rules_triggered=mkt_rules,
                supporting_metadata=base_meta,
            )
        )

        # Determine Best Use and Recommended Format
        ready_channels = [r.channel for r in recommendations if r.decision == "READY"]
        if "Product Card" in ready_channels:
            best_use = "Product Card"
            recommended_format = "1:1 Square"
        elif "Website Hero" in ready_channels:
            best_use = "Website Hero"
            recommended_format = "16:9 Landscape"
        elif "Story / Vertical" in ready_channels:
            best_use = "Story / Vertical"
            recommended_format = "9:16 Vertical"
        elif "Social Feed" in ready_channels:
            best_use = "Social Feed"
            recommended_format = "4:5 Portrait"
        elif "Marketplace Listing" in ready_channels:
            best_use = "Marketplace Listing"
            recommended_format = "1:1 Square"
        elif ready_channels:
            best_use = ready_channels[0]
            recommended_format = "1:1 Square"
        else:
            best_use = "General Library"
            recommended_format = "Optimized Original"

        return UsageRecommendationResult(
            recommendations=recommendations,
            best_use=best_use,
            recommended_format=recommended_format,
        )


usage_engine = UsageRecommendationEngine()

