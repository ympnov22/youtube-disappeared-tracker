from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.disappearance_event import DisappearanceEvent, EventType
from app.models.video import Video

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_video_models.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


class TestVideoModel:
    def setup_method(self) -> None:
        self.db = TestingSessionLocal()
        self.db.query(Video).delete()
        self.db.query(DisappearanceEvent).delete()
        self.db.commit()

    def teardown_method(self) -> None:
        self.db.close()

    def test_create_video(self) -> None:
        video = Video(
            video_id="test_video_123",
            channel_id="UCtest123",
            title="Test Video",
            description="Test Description",
            published_at=datetime.now(timezone.utc),
            is_available=True,
        )
        self.db.add(video)
        self.db.commit()

        retrieved = (
            self.db.query(Video).filter(Video.video_id == "test_video_123").first()
        )
        assert retrieved is not None
        assert retrieved.title == "Test Video"
        assert retrieved.is_available is True

    def test_video_unique_constraint(self) -> None:
        video1 = Video(
            video_id="duplicate_video",
            channel_id="UCtest123",
            title="Video 1",
            published_at=datetime.now(timezone.utc),
        )
        video2 = Video(
            video_id="duplicate_video",
            channel_id="UCtest456",
            title="Video 2",
            published_at=datetime.now(timezone.utc),
        )

        self.db.add(video1)
        self.db.commit()

        self.db.add(video2)
        with pytest.raises(Exception):
            self.db.commit()


class TestDisappearanceEventModel:
    def setup_method(self) -> None:
        self.db = TestingSessionLocal()
        self.db.query(Video).delete()
        self.db.query(DisappearanceEvent).delete()
        self.db.commit()

        self.video = Video(
            video_id="test_video_123",
            channel_id="UCtest123",
            title="Test Video",
            published_at=datetime.now(timezone.utc),
        )
        self.db.add(self.video)
        self.db.commit()

    def teardown_method(self) -> None:
        self.db.close()

    def test_create_disappearance_event(self) -> None:
        event = DisappearanceEvent(
            video_id="test_video_123",
            event_type=EventType.PRIVATE,
            details={"reason": "Made private by owner"},
        )
        self.db.add(event)
        self.db.commit()

        retrieved = (
            self.db.query(DisappearanceEvent)
            .filter(DisappearanceEvent.video_id == "test_video_123")
            .first()
        )
        assert retrieved is not None
        assert retrieved.event_type == EventType.PRIVATE
        assert retrieved.details["reason"] == "Made private by owner"

    def test_event_types(self) -> None:
        event_types = [
            EventType.PRIVATE,
            EventType.DELETED,
            EventType.GEO_BLOCKED,
            EventType.AGE_RESTRICTED,
            EventType.UNKNOWN,
        ]

        for event_type in event_types:
            event = DisappearanceEvent(
                video_id="test_video_123",
                event_type=event_type,
            )
            self.db.add(event)

        self.db.commit()

        events = self.db.query(DisappearanceEvent).all()
        assert len(events) == 5
        retrieved_types = {event.event_type for event in events}
        assert retrieved_types == set(event_types)
