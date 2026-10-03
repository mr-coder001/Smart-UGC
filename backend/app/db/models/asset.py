import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    func,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class AssetStatus(str, enum.Enum):
    PROCESSING = "PROCESSING"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ModerationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    public_id = Column(String(64), unique=True, index=True, nullable=False)
    cloudinary_public_id = Column(String(255), unique=True, index=True, nullable=False)
    cloudinary_url = Column(String(1024), nullable=True)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(64), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # Asset and Moderation Lifecycle
    status = Column(
        Enum(AssetStatus, name="asset_status_enum", create_type=False),
        default=AssetStatus.PENDING,
        nullable=False,
        index=True,
    )
    moderation_status = Column(
        Enum(ModerationStatus, name="moderation_status_enum", create_type=False),
        default=ModerationStatus.PENDING,
        nullable=False,
        index=True,
    )
    moderation_reason = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    decision_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tags = relationship("AssetTag", back_populates="asset", cascade="all, delete-orphan", lazy="selectin")
    processing_state = relationship(
        "ProcessingState",
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    intelligence = relationship(
        "AssetIntelligence",
        back_populates="asset",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_assets_status_created_at", "status", "created_at"),
        Index("ix_assets_moderation_status_created_at", "moderation_status", "created_at"),
    )
