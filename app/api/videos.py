from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent, EventType
from app.models.video import Video
from app.schemas.disappearance_event import (
    DisappearanceEventListResponse,
    DisappearanceEventResponse,
)
from app.schemas.scan import ScanResponse
from app.schemas.video import VideoListResponse, VideoResponse
from app.services.video_ingestion import VideoIngestionService
from app.services.youtube_client import YouTubeClient

router = APIRouter(tags=["videos"])
backward_compat_router = APIRouter(tags=["videos-legacy"])


@router.post("/scan/{channel_id}", response_model=ScanResponse)
@backward_compat_router.post("/scan/{channel_id}", response_model=ScanResponse)
async def scan_channel(channel_id: str, db: Session = Depends(get_db)) -> ScanResponse:
    """
    Manually trigger a scan for a specific channel.

    Args:
        channel_id: The YouTube channel ID to scan

    Returns:
        Scan results with counts of added, updated videos and events created
    """
    channel = (
        db.query(Channel)
        .filter(Channel.channel_id == channel_id, Channel.is_active.is_(True))
        .first()
    )

    if not channel:
        try:
            youtube_client = YouTubeClient()
            resolved_channel_id, metadata = youtube_client.resolve_channel_input(
                channel_id
            )

            if not resolved_channel_id or not metadata:
                raise HTTPException(
                    status_code=404,
                    detail=f"Channel {channel_id} not found on YouTube",
                )

            from sqlalchemy import func

            channel_count = (
                db.query(func.count(Channel.id))
                .filter(Channel.is_active.is_(True))
                .scalar()
            )
            if channel_count >= 10:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Maximum of 10 channels allowed. "
                        "Please remove a channel before scanning a new one."
                    ),
                )

            channel = Channel(
                channel_id=resolved_channel_id,
                title=metadata["title"],
                description=metadata.get("description"),
                thumbnail_url=metadata.get("thumbnail_url"),
                subscriber_count=metadata.get("subscriber_count"),
                uploads_playlist_id=metadata.get("uploads_playlist_id"),
                source_input=channel_id,
            )
            db.add(channel)
            db.commit()
            db.refresh(channel)

        except HTTPException:
            raise
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Channel {channel_id} not found on YouTube",
            )
        except Exception as e:
            from app.services.youtube_client import (
                YouTubeAPIError,
                YouTubeQuotaExhaustedError,
            )

            if isinstance(e, (YouTubeAPIError, YouTubeQuotaExhaustedError)):
                raise HTTPException(
                    status_code=404,
                    detail=f"Channel {channel_id} not found on YouTube",
                )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to register channel {channel_id}: {str(e)}",
            )

    try:
        youtube_client = YouTubeClient()
        ingestion_service = VideoIngestionService(db, youtube_client)
        added, updated, events_created = ingestion_service.scan_channel(channel_id)

        return ScanResponse(
            added=added,
            updated=updated,
            events_created=events_created,
            channel_id=channel_id,
            message=f"Successfully scanned channel {channel.title}",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan channel: {str(e)}",
        )


@router.get("/channels/{channel_id}/videos", response_model=VideoListResponse)
async def get_channel_videos(
    channel_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None, pattern="^(active|missing)$"),
) -> VideoListResponse:
    """
    Get videos for a specific channel with pagination and filtering.

    Args:
        channel_id: The YouTube channel ID
        limit: Maximum number of videos to return (1-100)
        offset: Number of videos to skip
        status: Filter by video status ('active' or 'missing')

    Returns:
        Paginated list of videos
    """
    channel = (
        db.query(Channel)
        .filter(Channel.channel_id == channel_id, Channel.is_active.is_(True))
        .first()
    )

    if not channel:
        raise HTTPException(
            status_code=404,
            detail=f"Channel {channel_id} not found or inactive",
        )

    query = db.query(Video).filter(Video.channel_id == channel_id)

    if status == "active":
        query = query.filter(Video.is_available.is_(True))
    elif status == "missing":
        query = query.filter(Video.is_available.is_(False))

    total = query.count()

    videos = query.order_by(desc(Video.published_at)).offset(offset).limit(limit).all()

    return VideoListResponse(
        videos=[VideoResponse.model_validate(video) for video in videos],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/events", response_model=DisappearanceEventListResponse)
async def get_disappearance_events(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    channel_id: Optional[str] = Query(default=None),
    event_type: Optional[EventType] = Query(default=None),
    since: Optional[str] = Query(default=None),
) -> DisappearanceEventListResponse:
    """
    Get disappearance events with pagination and filtering.

    Args:
        limit: Maximum number of events to return (1-100)
        offset: Number of events to skip
        channel_id: Filter by channel ID
        event_type: Filter by event type
        since: Filter events since this ISO datetime

    Returns:
        Paginated list of disappearance events
    """
    query = db.query(DisappearanceEvent)

    if channel_id:
        query = query.join(Video).filter(Video.channel_id == channel_id)

    if event_type:
        query = query.filter(DisappearanceEvent.event_type == event_type)

    if since:
        try:
            from datetime import datetime

            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            query = query.filter(DisappearanceEvent.detected_at >= since_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid 'since' datetime format. Use ISO format.",
            )

    total = query.count()

    events = (
        query.order_by(desc(DisappearanceEvent.detected_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return DisappearanceEventListResponse(
        events=[DisappearanceEventResponse.model_validate(event) for event in events],
        total=total,
        limit=limit,
        offset=offset,
    )
