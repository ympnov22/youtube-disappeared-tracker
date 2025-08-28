from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VideoBase(BaseModel):
    video_id: str
    channel_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    published_at: datetime
    duration: Optional[str] = None
    view_count: Optional[int] = None


class VideoCreate(VideoBase):
    pass


class VideoResponse(VideoBase):
    id: int
    is_available: bool
    last_seen_at: datetime
    first_detected_at: datetime

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    videos: list[VideoResponse]
    total: int
    limit: int
    offset: int
