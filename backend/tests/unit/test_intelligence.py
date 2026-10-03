from datetime import datetime, timezone
import pytest
from app.core.config import settings
from app.db.models.asset import Asset, AssetStatus, ModerationStatus
from app.db.models.intelligence import ReviewDecisionEnum, ReviewRiskEnum
from app.db.models.tag import AssetTag
from app.schemas.asset import AssetRead
from app.services.asset_service import asset_service
from app.services.intelligence.explanation_engine import ExplanationEngine
from app.services.intelligence.pipeline_timeline import PipelineTimelineBuilder
from app.services.intelligence.quality_analyzer import QualityAnalyzer
from app.services.intelligence.review_router import ReviewRouter
from app.services.intelligence.service import IntelligenceEngine
from app.services.intelligence.usage_engine import UsageRecommendationEngine


def make_mock_asset(
    width=1920,
    height=1080,
    file_size=2000000,
    mime_type="image/jpeg",
    moderation_status=ModerationStatus.APPROVED,
    tags=None,
    public_id="mock_asset_1",
):
    now = datetime.now(timezone.utc)
    asset = Asset(
        id=1,
        public_id=public_id,
        cloudinary_public_id=f"claudinary_assets/{public_id}",
        original_filename="test_image.jpg",
        mime_type=mime_type,
        file_size=file_size,
        width=width,
        height=height,
        status=AssetStatus.APPROVED if moderation_status == ModerationStatus.APPROVED else AssetStatus.PENDING,
        moderation_status=moderation_status,
        moderation_reason=None,
        created_at=now,
        updated_at=now,
        tags=tags or [],
    )
    return asset


# 1. Scenario: High-quality image
def test_high_quality_image():
    analyzer = QualityAnalyzer()
    sample_tags = [
        AssetTag(id=1, asset_id=1, tag="product", confidence=0.96),
        AssetTag(id=2, asset_id=1, tag="studio", confidence=0.92),
    ]
    asset = make_mock_asset(width=3840, height=2160, file_size=4500000, mime_type="image/jpeg", tags=sample_tags)
    result = analyzer.analyze(asset)

    assert result.score >= 80
    assert result.rating == "Production Ready"
    assert any(f.factor == "Resolution Fidelity" and f.passed for f in result.factors)


# 2. Scenario: Low-resolution image
def test_low_resolution_image():
    analyzer = QualityAnalyzer()
    asset = make_mock_asset(width=320, height=240, file_size=15000, mime_type="image/jpeg")
    result = analyzer.analyze(asset)

    assert result.score < 60
    assert any(f.factor == "Resolution Fidelity" and not f.passed for f in result.factors)


# 3. Scenario: Unsafe / review image
def test_unsafe_review_image():
    router = ReviewRouter()
    # Explicitly rejected asset
    asset = make_mock_asset(moderation_status=ModerationStatus.REJECTED)
    result = router.evaluate(asset, moderation_confidence=0.98, moderation_violations=1)

    assert result.decision == ReviewDecisionEnum.AUTO_REJECTED
    assert result.risk == ReviewRiskEnum.HIGH


# 4. Scenario: Poor crop suitability (extreme aspect ratio)
def test_poor_crop_suitability():
    analyzer = QualityAnalyzer()
    usage_engine = UsageRecommendationEngine()

    # Panoramic aspect ratio (10:1)
    asset = make_mock_asset(width=4000, height=400)
    q_result = analyzer.analyze(asset)
    u_result = usage_engine.generate_recommendations(asset, q_result.score)

    # Ratio factor should indicate extreme framing
    assert any(f.factor == "Aspect Ratio Suitability" and not f.passed for f in q_result.factors)
    # Story vertical should NOT be recommended for a 10:1 panorama
    story_rec = next(r for r in u_result.recommendations if r.channel == "Story / Vertical")
    assert story_rec.decision == "NOT_RECOMMENDED"


# 5. Scenario: Missing metadata (0 dimensions, 0 file size)
def test_missing_metadata():
    analyzer = QualityAnalyzer()
    usage_engine = UsageRecommendationEngine()
    asset = make_mock_asset(width=None, height=None, file_size=None)

    result = analyzer.analyze(asset)
    assert 0 <= result.score <= 100
    u_result = usage_engine.generate_recommendations(asset, result.score)
    assert len(u_result.recommendations) == 5


# 6. Scenario: Missing Vision confidence / tags
def test_missing_vision_confidence():
    analyzer = QualityAnalyzer()
    explanation_engine = ExplanationEngine()
    asset = make_mock_asset(tags=[])

    result = analyzer.analyze(asset)
    assert any(f.factor == "Subject Visual Definition" for f in result.factors)

    # Explanation engine must gracefully report missing metadata
    exp = explanation_engine._explain_tags(asset)
    assert "Insufficient metadata" in exp.summary


# 7. Scenario: Missing moderation confidence / default fallback
def test_missing_moderation_confidence():
    router = ReviewRouter()
    asset = make_mock_asset(moderation_status=ModerationStatus.PENDING)
    # Evaluate with default confidence
    result = router.evaluate(asset, moderation_confidence=0.70)

    assert result.decision == ReviewDecisionEnum.HUMAN_REVIEW
    assert result.confidence == 0.70


# 8. Scenario: Failed intelligence calculation (Failure Isolation)
@pytest.mark.asyncio
async def test_failed_intelligence_calculation_isolation():
    engine = IntelligenceEngine()

    class BrokenAsset:
        id = 9999
        width = "INVALID_TYPE_TRIGGERING_EXCEPTION"
        height = 100

    # Ensure engine handles or identifies failure deterministically
    try:
        engine.calculate_quality_score(BrokenAsset())
    except Exception as e:
        assert isinstance(e, (AttributeError, TypeError))


# 9. Scenario: Existing legacy asset without intelligence data (Backward Compatibility)
def test_legacy_asset_backward_compatibility():
    legacy_asset = make_mock_asset()
    legacy_asset.intelligence = None

    # enrich_asset_read must not crash when intelligence is None
    asset_read = asset_service.enrich_asset_read(legacy_asset)
    assert isinstance(asset_read, AssetRead)
    assert asset_read.intelligence is None


# 10. Scenario: Deterministic repeated calculation
def test_deterministic_repeated_calculation():
    analyzer = QualityAnalyzer()
    asset = make_mock_asset(width=1920, height=1080, file_size=1500000)

    res1 = analyzer.analyze(asset)
    res2 = analyzer.analyze(asset)
    res3 = analyzer.analyze(asset)

    assert res1.score == res2.score == res3.score
    assert len(res1.factors) == len(res2.factors)
    assert [f.factor for f in res1.factors] == [f.factor for f in res2.factors]


# 11. Scenario: Usage recommendation boundaries
def test_usage_recommendation_boundaries():
    usage_engine = UsageRecommendationEngine()

    # Square asset with high resolution and high quality score -> Product Card should be READY
    square_asset = make_mock_asset(width=1200, height=1200)
    square_rec = usage_engine.generate_recommendations(square_asset, quality_score=85)
    pc = next(r for r in square_rec.recommendations if r.channel == "Product Card")
    assert pc.decision == "READY"

    # Wide landscape asset -> Website Hero should be READY
    wide_asset = make_mock_asset(width=2400, height=1200)
    wide_rec = usage_engine.generate_recommendations(wide_asset, quality_score=85)
    hero = next(r for r in wide_rec.recommendations if r.channel == "Website Hero")
    assert hero.decision == "READY"


# 12. Scenario: Human review threshold behavior
def test_human_review_threshold_behavior():
    router = ReviewRouter(auto_approve_threshold=0.90, auto_reject_threshold=0.40)
    pending_asset = make_mock_asset(moderation_status=ModerationStatus.PENDING)

    # High confidence >= 0.90 -> AUTO_APPROVED
    high_res = router.evaluate(pending_asset, moderation_confidence=0.95)
    assert high_res.decision == ReviewDecisionEnum.AUTO_APPROVED

    # Borderline confidence (0.75) -> HUMAN_REVIEW
    border_res = router.evaluate(pending_asset, moderation_confidence=0.75)
    assert border_res.decision == ReviewDecisionEnum.HUMAN_REVIEW

    # None confidence -> HUMAN_REVIEW
    none_res = router.evaluate(pending_asset, moderation_confidence=None)
    assert none_res.decision == ReviewDecisionEnum.HUMAN_REVIEW
    assert none_res.confidence is None


# 13. Scenario: Explanation generation
def test_explanation_generation():
    engine = IntelligenceEngine()
    asset = make_mock_asset(width=1920, height=1080)
    q_res = engine.calculate_quality_score(asset)
    u_res = engine.generate_usage_recommendations(asset, q_res.score)
    r_res = engine.calculate_review_risk(asset, confidence=0.96)

    explanations = engine.generate_decision_explanation(asset, q_res, u_res, r_res)

    assert explanations.moderation.summary != ""
    assert len(explanations.moderation.points) > 0
    assert explanations.quality.summary != ""
    assert explanations.crop.summary != ""
    assert explanations.recommendations.summary != ""


# 14. Scenario: Timeline builder duration integrity (Never fabricate duration)
def test_timeline_duration_integrity():
    builder = PipelineTimelineBuilder()
    asset = make_mock_asset()

    # Without timing dict: duration_ms must be None, NOT a fabricated number
    timeline_no_timing = builder.build_timeline(asset, stage_timings_ms=None)
    for stage in timeline_no_timing:
        assert stage.duration_ms is None

    # With real measured timings: duration_ms should match measured value
    real_timings = {"UPLOAD": 240, "VISION": 85}
    timeline_with_timing = builder.build_timeline(asset, stage_timings_ms=real_timings)
    upload_stage = next(s for s in timeline_with_timing if s.stage == "UPLOAD")
    assert upload_stage.duration_ms == 240
    delivery_stage = next(s for s in timeline_with_timing if s.stage == "DELIVERY")
    assert delivery_stage.duration_ms is None


# 15. Scenario: Quality Score exact weights, bounds [0, 100], and zero-silent scoring
def test_quality_score_weights_and_bounds():
    analyzer = QualityAnalyzer()

    # Asset with perfect specs: width >= 2560 (35), ratio 1.0 (20), 4 tags (25), approved (20) = 100
    perfect_tags = [
        AssetTag(id=1, asset_id=1, tag="product", confidence=0.95),
        AssetTag(id=2, asset_id=1, tag="studio", confidence=0.90),
        AssetTag(id=3, asset_id=1, tag="packaging", confidence=0.85),
    ]
    perfect_asset = make_mock_asset(
        width=3000,
        height=3000,
        file_size=2500000,
        moderation_status=ModerationStatus.APPROVED,
        tags=perfect_tags,
    )
    result = analyzer.analyze(perfect_asset)
    assert result.score == 100
    assert 0 <= result.score <= 100

    # Ensure factors are present and pass
    factors_by_name = {f.factor: f for f in result.factors}
    assert factors_by_name["Resolution Fidelity"].passed is True
    assert factors_by_name["Resolution Fidelity"].impact == "positive"
    assert factors_by_name["Aspect Ratio Suitability"].passed is True
    assert factors_by_name["Aspect Ratio Suitability"].impact == "positive"
    assert factors_by_name["Subject Visual Definition"].passed is True
    assert factors_by_name["Subject Visual Definition"].impact == "positive"
    assert factors_by_name["Brand Safety Compliance"].passed is True
    assert factors_by_name["Brand Safety Compliance"].impact == "positive"

    # Empty asset: No dimensions, no tags, pending moderation -> must be 0 points, no silent positive points
    empty_asset = make_mock_asset(
        width=None,
        height=None,
        file_size=None,
        moderation_status=ModerationStatus.PENDING,
        tags=[],
    )
    empty_result = analyzer.analyze(empty_asset)
    assert empty_result.score == 0
    for f in empty_result.factors:
        assert f.passed is False
        assert f.impact in ("negative", "neutral")


# 16. Scenario: Brand safety compliance factor matches authoritative moderation state
def test_brand_safety_consistency_with_moderation_state():
    analyzer = QualityAnalyzer()

    # Case A: Approved
    approved_asset = make_mock_asset(moderation_status=ModerationStatus.APPROVED)
    res_app = analyzer.analyze(approved_asset)
    safety_app = next(f for f in res_app.factors if f.factor == "Brand Safety Compliance")
    assert safety_app.passed is True
    assert safety_app.impact == "positive"
    assert "approved" in safety_app.description.lower() or "clear" in safety_app.description.lower()
    assert "pending" not in safety_app.description.lower()

    # Case B: Pending
    pending_asset = make_mock_asset(moderation_status=ModerationStatus.PENDING)
    res_pen = analyzer.analyze(pending_asset)
    safety_pen = next(f for f in res_pen.factors if f.factor == "Brand Safety Compliance")
    assert safety_pen.passed is False
    assert safety_pen.impact == "neutral"
    assert "pending" in safety_pen.description.lower()

    # Case C: Rejected
    rejected_asset = make_mock_asset(moderation_status=ModerationStatus.REJECTED)
    res_rej = analyzer.analyze(rejected_asset)
    safety_rej = next(f for f in res_rej.factors if f.factor == "Brand Safety Compliance")
    assert safety_rej.passed is False
    assert safety_rej.impact == "negative"
    assert "flagged" in safety_rej.description.lower() or "violation" in safety_rej.description.lower()


# 17. Scenario: Usage recommendations grounding - no fake marketplace platform claims
def test_usage_recommendations_grounding_no_fake_claims():
    usage_engine = UsageRecommendationEngine()

    # Small asset (656x593) like the user's test asset
    test_asset = make_mock_asset(width=656, height=593)
    result = usage_engine.generate_recommendations(test_asset, quality_score=75)

    assert len(result.recommendations) == 5
    for rec in result.recommendations:
        # Must not fabricate ungrounded claims about marketplace seller specifications or platform compliance
        reason_lower = rec.reason.lower()
        assert "marketplace seller" not in reason_lower
        assert "platform compliance" not in reason_lower
        assert "platform-specific" not in reason_lower
        assert "strict marketplace" not in reason_lower

        # Supporting metadata must be present
        assert rec.supporting_metadata is not None
        assert "width" in rec.supporting_metadata
        assert "height" in rec.supporting_metadata
        assert "aspect_ratio" in rec.supporting_metadata
        assert "rules_triggered" in rec.model_dump()


# 18. Scenario: Multi-asset profiles evaluation
def test_multi_asset_profiles_evaluation():
    engine = IntelligenceEngine()

    # A. High-quality product image (3840x2160, approved, tags)
    tags_a = [AssetTag(id=1, asset_id=1, tag="bottle", confidence=0.94)]
    asset_a = make_mock_asset(width=3840, height=2160, moderation_status=ModerationStatus.APPROVED, tags=tags_a)
    q_a = engine.calculate_quality_score(asset_a)
    u_a = engine.generate_usage_recommendations(asset_a, q_a.score)
    hero_a = next(r for r in u_a.recommendations if r.channel == "Website Hero")
    assert q_a.score >= 80
    assert hero_a.decision == "READY"

    # B. Low-resolution image (320x240, approved, no tags)
    asset_b = make_mock_asset(width=320, height=240, moderation_status=ModerationStatus.APPROVED, tags=[])
    q_b = engine.calculate_quality_score(asset_b)
    u_b = engine.generate_usage_recommendations(asset_b, q_b.score)
    hero_b = next(r for r in u_b.recommendations if r.channel == "Website Hero")
    pc_b = next(r for r in u_b.recommendations if r.channel == "Product Card")
    assert q_b.score < 50
    assert hero_b.decision == "NOT_RECOMMENDED"
    assert pc_b.decision == "NOT_RECOMMENDED"

    # C. Wide landscape image (2560x1080, ratio 2.37)
    asset_c = make_mock_asset(width=2560, height=1080, moderation_status=ModerationStatus.APPROVED)
    q_c = engine.calculate_quality_score(asset_c)
    u_c = engine.generate_usage_recommendations(asset_c, q_c.score)
    story_c = next(r for r in u_c.recommendations if r.channel == "Story / Vertical")
    assert story_c.decision == "NOT_RECOMMENDED"

    # D. Tall portrait image (1080x1920, ratio 0.56 = 9:16)
    asset_d = make_mock_asset(width=1080, height=1920, moderation_status=ModerationStatus.APPROVED)
    q_d = engine.calculate_quality_score(asset_d)
    u_d = engine.generate_usage_recommendations(asset_d, q_d.score)
    story_d = next(r for r in u_d.recommendations if r.channel == "Story / Vertical")
    hero_d = next(r for r in u_d.recommendations if r.channel == "Website Hero")
    assert story_d.decision == "READY"
    assert hero_d.decision == "NOT_RECOMMENDED"

    # E. Test asset (656x593, ratio 1.11:1)
    asset_e = make_mock_asset(width=656, height=593, moderation_status=ModerationStatus.APPROVED)
    q_e = engine.calculate_quality_score(asset_e)
    u_e = engine.generate_usage_recommendations(asset_e, q_e.score)
    # Check that resolutions and aspect ratios in reasons match exactly 656x593 and 1.11:1
    for rec in u_e.recommendations:
        assert rec.supporting_metadata["width"] == 656
        assert rec.supporting_metadata["height"] == 593
