import logging
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent
from app.models.video import Video
from app.services.video_ingestion import VideoIngestionService
from app.services.youtube_client import YouTubeClient
from app.web.auth import (
    generate_csrf_token,
    limiter,
    require_https,
    verify_admin_credentials,
    verify_csrf_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/admin", response_class=RedirectResponse)
async def admin_dashboard(
    request: Request,
    admin_user: str = Depends(verify_admin_credentials),
) -> RedirectResponse:
    """Admin dashboard - redirect to channels page."""
    require_https(request)
    return RedirectResponse(url="/admin/channels", status_code=302)


@router.get("/admin/channels")
async def admin_channels(
    request: Request,
    page: int = 1,
    search: str = "",
    db: Session = Depends(get_db),
    admin_user: str = Depends(verify_admin_credentials),
) -> Any:
    """Admin channels list page with pagination and search."""
    require_https(request)

    per_page = 10
    offset = (page - 1) * per_page

    query = db.query(Channel).filter(Channel.is_active.is_(True))

    if search:
        query = query.filter(
            Channel.title.ilike(f"%{search}%")
            | Channel.channel_id.ilike(f"%{search}%")
            | Channel.source_input.ilike(f"%{search}%")
        )

    total_channels = query.count()
    total_pages = (total_channels + per_page - 1) // per_page

    channels = query.offset(offset).limit(per_page).all()

    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token

    return templates.TemplateResponse(
        "channels.html",
        {
            "request": request,
            "channels": channels,
            "csrf_token": csrf_token,
            "admin_user": admin_user,
            "current_page": page,
            "total_pages": total_pages,
            "total_channels": total_channels,
            "search": search,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if page < total_pages else None,
        },
    )


@router.get("/admin/channels/{channel_id}/videos")
async def channel_videos(
    request: Request,
    channel_id: str,
    db: Session = Depends(get_db),
    admin_user: str = Depends(verify_admin_credentials),
) -> Any:
    """Channel videos page."""
    require_https(request)

    channel = (
        db.query(Channel)
        .filter(Channel.channel_id == channel_id, Channel.is_active.is_(True))
        .first()
    )

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    videos = (
        db.query(Video)
        .filter(Video.channel_id == channel_id)
        .order_by(desc(Video.published_at))
        .limit(100)
        .all()
    )

    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token

    return templates.TemplateResponse(
        "channel_videos.html",
        {
            "request": request,
            "channel": channel,
            "videos": videos,
            "csrf_token": csrf_token,
            "admin_user": admin_user,
        },
    )


@router.get("/admin/events")
async def disappearance_events(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: str = Depends(verify_admin_credentials),
) -> Any:
    """Disappearance events page."""
    require_https(request)

    events = (
        db.query(DisappearanceEvent)
        .join(Video)
        .join(Channel)
        .order_by(desc(DisappearanceEvent.detected_at))
        .limit(100)
        .all()
    )

    csrf_token = generate_csrf_token()
    request.session["csrf_token"] = csrf_token

    return templates.TemplateResponse(
        "events.html",
        {
            "request": request,
            "events": events,
            "csrf_token": csrf_token,
            "admin_user": admin_user,
        },
    )


@router.post("/admin/channels/add")
@limiter.limit("5/minute")
async def add_channel(
    request: Request,
    channel_input: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    admin_user: str = Depends(verify_admin_credentials),
) -> RedirectResponse:
    """Add a new channel."""
    require_https(request)

    if not verify_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    try:
        youtube_client = YouTubeClient()
        channel_id, metadata = youtube_client.resolve_channel_input(channel_input)

        if not channel_id or not metadata:
            raise HTTPException(status_code=400, detail="Could not resolve channel")

        existing_channel = (
            db.query(Channel).filter(Channel.channel_id == channel_id).first()
        )

        if existing_channel:
            if not existing_channel.is_active:
                existing_channel.is_active = True  # type: ignore[assignment]
                db.commit()
                logger.info(f"Reactivated channel {channel_id}")
            else:
                raise HTTPException(status_code=400, detail="Channel already exists")
        else:
            new_channel = Channel(
                channel_id=channel_id,
                title=metadata.get("title", "Unknown"),
                description=metadata.get("description"),
                thumbnail_url=metadata.get("thumbnail_url"),
                uploads_playlist_id=metadata.get("uploads_playlist_id"),
                source_input=channel_input,
                is_active=True,
            )
            db.add(new_channel)
            db.commit()
            logger.info(f"Added new channel {channel_id}")

        return RedirectResponse(url="/admin/channels", status_code=303)

    except Exception as e:
        logger.error(f"Failed to add channel {channel_input}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to add channel: {str(e)}")


@router.post("/admin/channels/{channel_id}/scan")
@limiter.limit("2/minute")
async def scan_channel(
    request: Request,
    channel_id: str,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    admin_user: str = Depends(verify_admin_credentials),
) -> RedirectResponse:
    """Manually scan a channel."""
    require_https(request)

    if not verify_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    channel = (
        db.query(Channel)
        .filter(Channel.channel_id == channel_id, Channel.is_active.is_(True))
        .first()
    )

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    try:
        youtube_client = YouTubeClient()
        ingestion_service = VideoIngestionService(db, youtube_client)
        added, updated, events_created = ingestion_service.scan_channel(channel_id)

        logger.info(
            f"Scanned channel {channel_id}: {added} added, {updated} updated, "
            f"{events_created} events created"
        )

        return RedirectResponse(url="/admin/channels", status_code=303)

    except Exception as e:
        logger.error(f"Failed to scan channel {channel_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/admin/channels/{channel_id}/delete")
@limiter.limit("3/minute")
async def delete_channel(
    request: Request,
    channel_id: str,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    admin_user: str = Depends(verify_admin_credentials),
) -> RedirectResponse:
    """Soft delete a channel."""
    require_https(request)

    if not verify_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    channel = (
        db.query(Channel)
        .filter(Channel.channel_id == channel_id, Channel.is_active.is_(True))
        .first()
    )

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    channel.is_active = False  # type: ignore[assignment]
    db.commit()

    logger.info(f"Soft deleted channel {channel_id}")
    return RedirectResponse(url="/admin/channels", status_code=303)
