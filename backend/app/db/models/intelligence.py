import enum
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class ReviewDecisionEnum(str, enum.Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    AUTO_REJECTED = "AUTO_REJECTED"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class ReviewRiskEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AssetIntelligence(Base):
    __tablename__ = "asset_intelligence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asset_id = Column(
        Integer,
        ForeignKey("assets.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # 1. Visual Quality Score (0–100)
    quality_score = Column(Integer, nullable=False, default=0, index=True)
    quality_rating = Column(String(50), nullable=False, default="Needs Review")
    quality_factors = Column(JSON, nullable=False, default=list)
    unavailable_signals = Column(JSON, nullable=False, default=list)

    # 2. Channel Usage Recommendations
    usage_recommendations = Column(JSON, nullable=False, default=list)
    best_use = Column(String(100), nullable=True)
    recommended_format = Column(String(50), nullable=True)

    # 3. Intelligent Human Review Routing
    review_decision = Column(String(50), nullable=False, default=ReviewDecisionEnum.HUMAN_REVIEW.value, index=True)
    review_risk = Column(String(20), nullable=False, default=ReviewRiskEnum.MEDIUM.value, index=True)
    review_reason = Column(String(500), nullable=True)
    review_confidence = Column(Float, nullable=True, default=None)

    # 4. Explainable AI / Why System
    explanations = Column(JSON, nullable=False, default=dict)

    # 5. Pipeline Decision Timeline
    pipeline_timeline = Column(JSON, nullable=False, default=list)

    # Versioning & Failure isolation
    version = Column(String(20), nullable=False, default="1.0.0")
    status = Column(String(50), nullable=False, default="COMPLETED")  # COMPLETED | PARTIAL | FAILED
    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    asset = relationship("Asset", back_populates="intelligence")

    __table_args__ = (
        Index("ix_asset_intel_quality_score", "quality_score"),
        Index("ix_asset_intel_review_decision", "review_decision"),
        Index("ix_asset_intel_review_risk", "review_risk"),
    )
