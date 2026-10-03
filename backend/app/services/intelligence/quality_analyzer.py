from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.db.models.asset import Asset, AssetStatus, ModerationStatus


class QualityFactorResult(BaseModel):
    factor: str
    passed: bool
    impact: str  # positive, neutral, negative
    description: str
    signal_used: str


class QualityAnalysisResult(BaseModel):
    score: int
    rating: str
    factors: List[QualityFactorResult]
    unavailable_signals: List[str]
    version: str = "1.1.0"


class QualityAnalyzer:
    VERSION = "1.1.0"

    # Explicitly tracked signals that are physically unavailable in standard web payloads
    UNAVAILABLE_SIGNALS = [
        "sensor_snr_raw_lux",
        "lens_point_spread_blur",
        "chromatic_aberration_psf",
    ]

    def analyze(self, asset: Asset) -> QualityAnalysisResult:
        """
        Deterministic, transparent quality calculation (0–100).
        Uses strictly grounded real metadata:
        - Resolution Fidelity: 35 points max
        - Aspect Ratio Suitability: 20 points max
        - Subject Visual Definition: 25 points max
        - Brand Safety Compliance: 20 points max
        """
        score = 0
        factors: List[QualityFactorResult] = []

        width = asset.width or 0
        height = asset.height or 0
        pixels = width * height

        # --- 1. Resolution & Dimension Quality (Max 35 pts) ---
        if width <= 0 or height <= 0:
            # Missing dimension data receives 0 points (no silent positive points)
            factors.append(
                QualityFactorResult(
                    factor="Resolution Fidelity",
                    passed=False,
                    impact="negative",
                    description="Resolution: Dimensions unavailable; resolution cannot be verified.",
                    signal_used="dimensions:none",
                )
            )
        elif pixels >= 1920 * 1080:  # Full HD / 2MP+
            score += 35
            factors.append(
                QualityFactorResult(
                    factor="Resolution Fidelity",
                    passed=True,
                    impact="positive",
                    description=f"Resolution: {width}×{height} px; exceeds 2.0 MP master standard for high-density displays.",
                    signal_used=f"dimensions:{width}x{height}",
                )
            )
        elif pixels >= 1000 * 1000:  # Standard High Res (1MP+)
            score += 28
            factors.append(
                QualityFactorResult(
                    factor="Resolution Fidelity",
                    passed=True,
                    impact="positive",
                    description=f"Resolution: {width}×{height} px; meets standard high-resolution threshold (1.0+ MP) for catalog and zoom.",
                    signal_used=f"dimensions:{width}x{height}",
                )
            )
        elif pixels >= 600 * 600:  # Medium Res (0.36MP+)
            score += 18
            factors.append(
                QualityFactorResult(
                    factor="Resolution Fidelity",
                    passed=True,
                    impact="neutral",
                    description=f"Resolution: {width}×{height} px; meets the configured minimum for product cards and thumbnails.",
                    signal_used=f"dimensions:{width}x{height}",
                )
            )
        else:  # Under 600x600
            score += 8
            factors.append(
                QualityFactorResult(
                    factor="Resolution Fidelity",
                    passed=False,
                    impact="negative",
                    description=f"Resolution: {width}×{height} px; below the 600×600 px standard, risk of pixelation on large viewports.",
                    signal_used=f"dimensions:{width}x{height}",
                )
            )

        # --- 2. Aspect Ratio & Framing Adaptability (Max 20 pts) ---
        if width > 0 and height > 0:
            ratio = width / height
            if 0.8 <= ratio <= 1.25:
                score += 20
                factors.append(
                    QualityFactorResult(
                        factor="Aspect Ratio Suitability",
                        passed=True,
                        impact="positive",
                        description=f"Aspect ratio: {ratio:.2f}:1; balanced near-square format requires minimal cropping for 1:1 containers.",
                        signal_used=f"aspect_ratio:{ratio:.2f}",
                    )
                )
            elif 1.25 < ratio <= 2.2:
                score += 20
                factors.append(
                    QualityFactorResult(
                        factor="Aspect Ratio Suitability",
                        passed=True,
                        impact="positive",
                        description=f"Aspect ratio: {ratio:.2f}:1; standard landscape orientation accommodates horizontal multi-channel containers.",
                        signal_used=f"aspect_ratio:{ratio:.2f}",
                    )
                )
            elif 0.5 <= ratio < 0.8:
                score += 20
                factors.append(
                    QualityFactorResult(
                        factor="Aspect Ratio Suitability",
                        passed=True,
                        impact="positive",
                        description=f"Aspect ratio: {ratio:.2f}:1; standard portrait orientation accommodates vertical social and mobile feeds.",
                        signal_used=f"aspect_ratio:{ratio:.2f}",
                    )
                )
            else:
                score += 8
                factors.append(
                    QualityFactorResult(
                        factor="Aspect Ratio Suitability",
                        passed=False,
                        impact="negative",
                        description=f"Aspect ratio: {ratio:.2f}:1; extreme framing requires substantial cropping for standard containers.",
                        signal_used=f"aspect_ratio:{ratio:.2f}",
                    )
                )
        else:
            factors.append(
                QualityFactorResult(
                    factor="Aspect Ratio Suitability",
                    passed=False,
                    impact="neutral",
                    description="Aspect ratio: Dimensions unavailable; aspect ratio calculation omitted.",
                    signal_used="dimensions:none",
                )
            )

        # --- 3. AI Vision Detection & Subject Definition (Max 25 pts) ---
        tags = asset.tags or []
        if tags:
            valid_confidences = [t.confidence for t in tags if t.confidence is not None]
            avg_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 1.0
            if avg_confidence >= 0.85:
                score += 25
                factors.append(
                    QualityFactorResult(
                        factor="Subject Visual Definition",
                        passed=True,
                        impact="positive",
                        description=f"Subject definition: {len(tags)} visual entities verified with {(avg_confidence * 100):.1f}% provider confidence.",
                        signal_used=f"vision_tags_count:{len(tags)},avg_conf:{avg_confidence:.2f}",
                    )
                )
            elif avg_confidence >= 0.60:
                score += 18
                factors.append(
                    QualityFactorResult(
                        factor="Subject Visual Definition",
                        passed=True,
                        impact="positive",
                        description=f"Subject definition: {len(tags)} visual entities verified with {(avg_confidence * 100):.1f}% provider confidence.",
                        signal_used=f"vision_tags_count:{len(tags)},avg_conf:{avg_confidence:.2f}",
                    )
                )
            else:
                score += 10
                factors.append(
                    QualityFactorResult(
                        factor="Subject Visual Definition",
                        passed=True,
                        impact="neutral",
                        description=f"Subject definition: {len(tags)} visual entities detected with moderate provider confidence ({(avg_confidence * 100):.1f}%).",
                        signal_used=f"vision_tags_count:{len(tags)},avg_conf:{avg_confidence:.2f}",
                    )
                )
        else:
            # 0 points when no vision tags were returned (no silent positive points)
            factors.append(
                QualityFactorResult(
                    factor="Subject Visual Definition",
                    passed=False,
                    impact="neutral",
                    description="Subject definition: No automated vision tags detected from provider; visual entity confirmation unverified.",
                    signal_used="vision_tags:0",
                )
            )

        # --- 4. Brand Safety & Moderation Alignment (Max 20 pts) ---
        if asset.moderation_status == ModerationStatus.APPROVED:
            score += 20
            factors.append(
                QualityFactorResult(
                    factor="Brand Safety Compliance",
                    passed=True,
                    impact="positive",
                    description="Brand safety: Moderation completed successfully; approved for publication.",
                    signal_used=f"moderation_status:{asset.moderation_status.value}",
                )
            )
        elif asset.moderation_status == ModerationStatus.PENDING:
            # 0 points while pending moderation (no positive score for unverified assets)
            factors.append(
                QualityFactorResult(
                    factor="Brand Safety Compliance",
                    passed=False,
                    impact="neutral",
                    description="Brand safety: Asset pending moderation inspection; manual review required before public distribution.",
                    signal_used=f"moderation_status:{asset.moderation_status.value}",
                )
            )
        else:
            score -= 15
            factors.append(
                QualityFactorResult(
                    factor="Brand Safety Compliance",
                    passed=False,
                    impact="negative",
                    description=f"Brand safety: Moderation rejected ({asset.moderation_reason or 'Policy violation'}).",
                    signal_used=f"moderation_status:{asset.moderation_status.value}",
                )
            )

        # Clamp strictly between 0 and 100
        final_score = max(0, min(100, score))

        if final_score >= 80:
            rating = "Production Ready"
        elif final_score >= 55:
            rating = "Acceptable"
        else:
            rating = "Needs Review"

        return QualityAnalysisResult(
            score=final_score,
            rating=rating,
            factors=factors,
            unavailable_signals=self.UNAVAILABLE_SIGNALS,
            version=self.VERSION,
        )


quality_analyzer = QualityAnalyzer()

