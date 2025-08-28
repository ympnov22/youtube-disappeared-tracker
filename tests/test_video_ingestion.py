from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent, EventType
from app.models.video import Video
from app.services.video_ingestion import VideoIngestionService

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_video_ingestion.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


class TestVideoIngestionService:
    def setup_method(self) -> None:
        self.db = TestingSessionLocal()
        self.db.query(Video).delete()
        self.db.query(DisappearanceEvent).delete()
        self.db.query(Channel).delete()
        self.db.commit()

        self.channel = Channel(
            channel_id="UCtest123",
            title="Test Channel",
            uploads_playlist_id="UUtest123",
            source_input="@testchannel",
        )
        self.db.add(self.channel)
        self.db.commit()

        self.mock_youtube_client = Mock()
        self.service = VideoIngestionService(self.db, self.mock_youtube_client)

    def teardown_method(self) -> None:
        self.db.close()

    def test_scan_channel_new_videos(self) -> None:
        mock_videos = [
            {
                "video_id": "video1",
                "title": "Video 1",
                "description": "Description 1",
                "published_at": datetime.now(timezone.utc),
                "view_count": 1000,
            },
            {
                "video_id": "video2",
                "title": "Video 2",
                "description": "Description 2",
                "published_at": datetime.now(timezone.utc),
                "view_count": 2000,
            },
        ]
        self.mock_youtube_client.fetch_channel_videos.return_value = mock_videos

        added, updated, events = self.service.scan_channel("UCtest123")

        assert added == 2
        assert updated == 0
        assert events == 0

        videos = self.db.query(Video).all()
        assert len(videos) == 2
        assert all(v.is_available for v in videos)

    def test_scan_channel_idempotent(self) -> None:
        existing_video = Video(
            video_id="existing_video",
            channel_id="UCtest123",
            title="Old Title",
            published_at=datetime.now(timezone.utc),
            is_available=True,
        )
        self.db.add(existing_video)
        self.db.commit()

        mock_videos = [
            {
                "video_id": "existing_video",
                "title": "Updated Title",
                "description": "Updated Description",
                "published_at": datetime.now(timezone.utc),
                "view_count": 5000,
            }
        ]
        self.mock_youtube_client.fetch_channel_videos.return_value = mock_videos

        added, updated, events = self.service.scan_channel("UCtest123")

        assert added == 0
        assert updated == 0
        assert events == 0

        video = self.db.query(Video).filter(Video.video_id == "existing_video").first()
        assert video.title == "Updated Title"
        assert video.description == "Updated Description"

    def test_scan_channel_detect_disappearance(self) -> None:
        existing_video = Video(
            video_id="disappeared_video",
            channel_id="UCtest123",
            title="Disappeared Video",
            published_at=datetime.now(timezone.utc),
            is_available=True,
        )
        self.db.add(existing_video)
        self.db.commit()

        self.mock_youtube_client.fetch_channel_videos.return_value = []

        added, updated, events = self.service.scan_channel("UCtest123")

        assert added == 0
        assert updated == 0
        assert events == 1

        video = (
            self.db.query(Video).filter(Video.video_id == "disappeared_video").first()
        )
        assert video.is_available is False

        event = (
            self.db.query(DisappearanceEvent)
            .filter(DisappearanceEvent.video_id == "disappeared_video")
            .first()
        )
        assert event is not None
        assert event.event_type == EventType.UNKNOWN

    def test_scan_channel_reappearance(self) -> None:
        disappeared_video = Video(
            video_id="reappeared_video",
            channel_id="UCtest123",
            title="Reappeared Video",
            published_at=datetime.now(timezone.utc),
            is_available=False,
        )
        self.db.add(disappeared_video)
        self.db.commit()

        mock_videos = [
            {
                "video_id": "reappeared_video",
                "title": "Reappeared Video",
                "description": "Back online",
                "published_at": datetime.now(timezone.utc),
                "view_count": 1000,
            }
        ]
        self.mock_youtube_client.fetch_channel_videos.return_value = mock_videos

        added, updated, events = self.service.scan_channel("UCtest123")

        assert added == 0
        assert updated == 1
        assert events == 0

        video = (
            self.db.query(Video).filter(Video.video_id == "reappeared_video").first()
        )
        assert video.is_available is True

    def test_scan_channel_not_found(self) -> None:
        with pytest.raises(ValueError, match="Channel nonexistent not found"):
            self.service.scan_channel("nonexistent")

    def test_scan_channel_youtube_api_error(self) -> None:
        self.mock_youtube_client.fetch_channel_videos.side_effect = Exception(
            "API Error"
        )

        with pytest.raises(Exception, match="API Error"):
            self.service.scan_channel("UCtest123")
