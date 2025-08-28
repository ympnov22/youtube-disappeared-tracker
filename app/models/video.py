from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(255), unique=True, index=True, nullable=False)
    channel_id = Column(String(255), ForeignKey("channels.channel_id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    duration = Column(String(50), nullable=True)
    view_count = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    last_seen_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    first_detected_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
