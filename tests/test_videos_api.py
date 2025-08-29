from datetime import datetime, timezone
from typing import Generator
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent, EventType
from app.models.video import Video

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


client = TestClient(app)


class TestVideosAPI:
    def setup_method(self) -> None:
        app.dependency_overrides[get_db] = override_get_db

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        db = TestingSessionLocal()
        try:
            self.channel = Channel(
                channel_id="UCtest123",
                title="Test Channel",
                uploads_playlist_id="UUtest123",
                source_input="@testchannel",
                is_active=True,
            )
            db.add(self.channel)
            db.commit()
            db.refresh(self.channel)
        finally:
            db.close()

    def teardown_method(self) -> None:
        if get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]

    @patch("app.api.videos.YouTubeClient")
    @patch("app.api.videos.VideoIngestionService")
    def test_scan_channel_success(
        self, mock_ingestion_service_class: Mock, mock_youtube_client_class: Mock
    ) -> None:
        mock_service = Mock()
        mock_ingestion_service_class.return_value = mock_service
        mock_service.scan_channel.return_value = (5, 2, 1)

        response = client.post("/api/scan/UCtest123")

        assert response.status_code == 200
        data = response.json()
        assert data["added"] == 5
        assert data["updated"] == 2
        assert data["events_created"] == 1
        assert data["channel_id"] == "UCtest123"

    def test_scan_channel_not_found(self) -> None:
        response = client.post("/api/scan/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("app.api.videos.YouTubeClient")
    @patch("app.api.videos.VideoIngestionService")
    def test_scan_channel_api_error(
        self, mock_ingestion_service_class: Mock, mock_youtube_client_class: Mock
    ) -> None:
        mock_service = Mock()
        mock_ingestion_service_class.return_value = mock_service
        mock_service.scan_channel.side_effect = Exception("API quota exceeded")

        response = client.post("/api/scan/UCtest123")
        assert response.status_code == 500
        assert "Failed to scan channel" in response.json()["detail"]

    def test_get_channel_videos_empty(self) -> None:
        response = client.get("/api/channels/UCtest123/videos")
        assert response.status_code == 200
        data = response.json()
        assert data["videos"] == []
        assert data["total"] == 0

    def test_get_channel_videos_with_data(self) -> None:
        db = TestingSessionLocal()
        video1 = Video(
            video_id="video1",
            channel_id="UCtest123",
            title="Video 1",
            published_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
            is_available=True,
        )
        video2 = Video(
            video_id="video2",
            channel_id="UCtest123",
            title="Video 2",
            published_at=datetime(2023, 1, 2, tzinfo=timezone.utc),
            is_available=False,
        )
        db.add_all([video1, video2])
        db.commit()
        db.close()

        response = client.get("/api/channels/UCtest123/videos")
        assert response.status_code == 200
        data = response.json()
        assert len(data["videos"]) == 2
        assert data["total"] == 2

    def test_get_channel_videos_filter_active(self) -> None:
        db = TestingSessionLocal()
        video1 = Video(
            video_id="video1",
            channel_id="UCtest123",
            title="Active Video",
            published_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
            is_available=True,
        )
        video2 = Video(
            video_id="video2",
            channel_id="UCtest123",
            title="Missing Video",
            published_at=datetime(2023, 1, 2, tzinfo=timezone.utc),
            is_available=False,
        )
        db.add_all([video1, video2])
        db.commit()
        db.close()

        response = client.get("/api/channels/UCtest123/videos?status=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data["videos"]) == 1
        assert data["videos"][0]["title"] == "Active Video"

    def test_get_channel_videos_pagination(self) -> None:
        db = TestingSessionLocal()
        for i in range(10):
            video = Video(
                video_id=f"video{i}",
                channel_id="UCtest123",
                title=f"Video {i}",
                published_at=datetime(2023, 1, i + 1, tzinfo=timezone.utc),
                is_available=True,
            )
            db.add(video)
        db.commit()
        db.close()

        response = client.get("/api/channels/UCtest123/videos?limit=5&offset=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["videos"]) == 5
        assert data["total"] == 10
        assert data["limit"] == 5
        assert data["offset"] == 3

    def test_get_channel_not_found(self) -> None:
        response = client.get("/api/channels/nonexistent/videos")
        assert response.status_code == 404

    def test_get_disappearance_events_empty(self) -> None:
        response = client.get("/api/events")
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0

    def test_get_disappearance_events_with_data(self) -> None:
        db = TestingSessionLocal()
        video = Video(
            video_id="disappeared_video",
            channel_id="UCtest123",
            title="Disappeared Video",
            published_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
            is_available=False,
        )
        event = DisappearanceEvent(
            video_id="disappeared_video",
            event_type=EventType.PRIVATE,
            details={"reason": "Made private"},
        )
        db.add_all([video, event])
        db.commit()
        db.close()

        response = client.get("/api/events")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["event_type"] == "PRIVATE"

    def test_get_disappearance_events_filter_by_type(self) -> None:
        db = TestingSessionLocal()
        video = Video(
            video_id="disappeared_video",
            channel_id="UCtest123",
            title="Disappeared Video",
            published_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
            is_available=False,
        )
        event1 = DisappearanceEvent(
            video_id="disappeared_video",
            event_type=EventType.PRIVATE,
        )
        event2 = DisappearanceEvent(
            video_id="disappeared_video",
            event_type=EventType.DELETED,
        )
        db.add_all([video, event1, event2])
        db.commit()
        db.close()

        response = client.get("/api/events?event_type=PRIVATE")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["event_type"] == "PRIVATE"

    def test_get_disappearance_events_invalid_since(self) -> None:
        response = client.get("/api/events?since=invalid-date")
        assert response.status_code == 400
        assert "Invalid 'since' datetime format" in response.json()["detail"]
