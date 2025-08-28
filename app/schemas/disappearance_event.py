from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel

from app.models.disappearance_event import EventType


class DisappearanceEventBase(BaseModel):
    video_id: str
    event_type: EventType
    details: Optional[Dict[str, Any]] = None


class DisappearanceEventCreate(DisappearanceEventBase):
    pass


class DisappearanceEventResponse(DisappearanceEventBase):
    id: int
    detected_at: datetime

    class Config:
        from_attributes = True


class DisappearanceEventListResponse(BaseModel):
    events: list[DisappearanceEventResponse]
    total: int
    limit: int
    offset: int
