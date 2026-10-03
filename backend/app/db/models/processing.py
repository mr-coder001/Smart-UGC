import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class TaskProcessingStatus(str, enum.Enum):
    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingState(Base):
    __tablename__ = "processing_states"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asset_id = Column(
        Integer,
        ForeignKey("assets.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    tagging_status = Column(
        Enum(TaskProcessingStatus, name="tagging_status_enum", create_type=False),
        default=TaskProcessingStatus.PENDING,
        nullable=False,
    )
    moderation_status = Column(
        Enum(TaskProcessingStatus, name="proc_moderation_status_enum", create_type=False),
        default=TaskProcessingStatus.PENDING,
        nullable=False,
    )
    background_removal_status = Column(
        Enum(TaskProcessingStatus, name="bg_removal_status_enum", create_type=False),
        default=TaskProcessingStatus.NOT_REQUESTED,
        nullable=False,
    )

    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    asset = relationship("Asset", back_populates="processing_state")
