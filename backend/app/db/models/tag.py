from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class AssetTag(Base):
    __tablename__ = "asset_tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=1.0)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    asset = relationship("Asset", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("asset_id", "tag", name="uq_asset_tag"),
        Index("ix_asset_tags_tag_confidence", "tag", "confidence"),
    )
