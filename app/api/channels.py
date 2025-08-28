from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.channel import Channel
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.services.youtube_client import YouTubeClient

router = APIRouter(prefix="/channels", tags=["channels"])


@router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def add_channel(channel_data: ChannelCreate, db: Session = Depends(get_db)):
    """
    Add a new channel with validation, 10-channel limit, and deduplication.

    Accepts various input formats:
    - Channel URLs: https://www.youtube.com/channel/UCxxxxx
    - Handle URLs: https://www.youtube.com/@handle
    - User URLs: https://www.youtube.com/user/username
    - Custom URLs: https://www.youtube.com/c/customname
    - Direct channel IDs: UCxxxxx
    - Direct handles: @handle
    """
    channel_count = (
        db.query(func.count(Channel.id)).filter(Channel.is_active.is_(True)).scalar()
    )
    if channel_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 10 channels allowed. Please remove a channel "
            "before adding a new one.",
        )

    try:
        youtube_client = YouTubeClient()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="YouTube API configuration error",
        )

    channel_id, metadata = youtube_client.resolve_channel_input(channel_data.input)

    if not channel_id or not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found. Please check the URL or handle and try again.",
        )

    existing_channel = (
        db.query(Channel)
        .filter(Channel.channel_id == channel_id, Channel.is_active.is_(True))
        .first()
    )

    if existing_channel:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Channel '{metadata['title']}' is already registered.",
        )

    new_channel = Channel(
        channel_id=channel_id,
        title=metadata["title"],
        description=metadata.get("description"),
        thumbnail_url=metadata.get("thumbnail_url"),
        subscriber_count=metadata.get("subscriber_count"),
        uploads_playlist_id=metadata.get("uploads_playlist_id"),
        source_input=channel_data.input,
    )

    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)

    return ChannelResponse.model_validate(new_channel)


@router.get("/", response_model=List[ChannelResponse])
async def list_channels(db: Session = Depends(get_db)):
    """
    List all registered channels with metadata.

    Returns channels ordered by most recently added first.
    """
    channels = (
        db.query(Channel)
        .filter(Channel.is_active.is_(True))
        .order_by(Channel.added_at.desc())
        .all()
    )
    return [ChannelResponse.model_validate(channel) for channel in channels]


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_channel(channel_id: str, db: Session = Depends(get_db)):
    """
    Remove a channel (soft delete).

    Args:
        channel_id: The YouTube channel ID (UCxxxxx format)
    """
    channel = (
        db.query(Channel)
        .filter(Channel.channel_id == channel_id, Channel.is_active.is_(True))
        .first()
    )

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found or already removed.",
        )

    channel.is_active = False
    db.commit()

    return None
