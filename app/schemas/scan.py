from pydantic import BaseModel


class ScanResponse(BaseModel):
    added: int
    updated: int
    events_created: int
    channel_id: str
    message: str
