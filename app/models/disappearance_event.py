import enum

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class EventType(enum.Enum):
    PRIVATE = "PRIVATE"
    DELETED = "DELETED"
    GEO_BLOCKED = "GEO_BLOCKED"
    AGE_RESTRICTED = "AGE_RESTRICTED"
    UNKNOWN = "UNKNOWN"


class DisappearanceEvent(Base):
    __tablename__ = "disappearance_events"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(255), ForeignKey("videos.video_id"), nullable=False)
    event_type: Column[EventType] = Column(Enum(EventType), nullable=False)
    detected_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    details = Column(JSON, nullable=True)
