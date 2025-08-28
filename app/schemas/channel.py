from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    input: str = Field(..., description="Channel URL, @handle, or channel ID")


class ChannelResponse(BaseModel):
    id: int
    channel_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subscriber_count: Optional[int] = None
    uploads_playlist_id: Optional[str] = None
    source_input: str
    is_active: bool
    added_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
