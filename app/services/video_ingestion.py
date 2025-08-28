import logging
from datetime import datetime
from typing import Tuple

from sqlalchemy.orm import Session

from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent, EventType
from app.models.video import Video
from app.services.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


class VideoIngestionService:
    def __init__(self, db: Session, youtube_client: YouTubeClient):
        self.db = db
        self.youtube_client = youtube_client

    def scan_channel(self, channel_id: str) -> Tuple[int, int, int]:
        """
        Scan a channel for videos and detect disappearances.

        Returns:
            Tuple of (added_count, updated_count, events_created_count)
        """
        channel = (
            self.db.query(Channel)
            .filter(Channel.channel_id == channel_id, Channel.is_active.is_(True))
            .first()
        )

        if not channel or not channel.uploads_playlist_id:
            raise ValueError(
                f"Channel {channel_id} not found or missing uploads playlist"
            )

        try:
            current_videos = self.youtube_client.fetch_channel_videos(
                str(channel.uploads_playlist_id)
            )
        except Exception as e:
            logger.error(f"Failed to fetch videos for channel {channel_id}: {e}")
            raise

        existing_videos = (
            self.db.query(Video).filter(Video.channel_id == channel_id).all()
        )

        existing_video_ids = {v.video_id for v in existing_videos}
        current_video_ids = {v["video_id"] for v in current_videos}

        added_count = 0
        updated_count = 0
        events_created_count = 0

        for video_data in current_videos:
            video_id = video_data["video_id"]
            existing_video = next(
                (v for v in existing_videos if v.video_id == video_id), None
            )

            if existing_video:
                if not existing_video.is_available:
                    existing_video.is_available = True  # type: ignore[assignment]
                    existing_video.last_seen_at = datetime.utcnow()  # type: ignore[assignment]  # noqa: E501
                    updated_count += 1
                else:
                    existing_video.last_seen_at = datetime.utcnow()  # type: ignore[assignment]  # noqa: E501

                existing_video.title = video_data["title"]
                if video_data.get("description") is not None:
                    existing_video.description = video_data["description"]
                if video_data.get("thumbnail_url") is not None:
                    existing_video.thumbnail_url = video_data["thumbnail_url"]
                if video_data.get("view_count") is not None:
                    existing_video.view_count = video_data["view_count"]
            else:
                new_video = Video(
                    video_id=video_id,
                    channel_id=channel_id,
                    title=video_data["title"],
                    description=video_data.get("description"),
                    thumbnail_url=video_data.get("thumbnail_url"),
                    published_at=video_data["published_at"],
                    duration=video_data.get("duration"),
                    view_count=video_data.get("view_count"),
                    is_available=True,
                )
                self.db.add(new_video)
                added_count += 1

        disappeared_video_ids = existing_video_ids - current_video_ids
        for video_id in disappeared_video_ids:
            video = next(v for v in existing_videos if v.video_id == video_id)
            if video.is_available:
                video.is_available = False  # type: ignore[assignment]

                event = DisappearanceEvent(
                    video_id=video_id,
                    event_type=EventType.UNKNOWN,
                    details={"title": video.title, "channel_id": channel_id},
                )
                self.db.add(event)
                events_created_count += 1

        self.db.commit()
        return added_count, updated_count, events_created_count
