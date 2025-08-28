import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent, EventType
from app.models.video import Video

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_migration.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestMigration:
    def setup_method(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    def teardown_method(self) -> None:
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    def test_migration_creates_all_tables(self) -> None:
        """Test that migration creates all required tables with proper schema."""
        inspector = engine.dialect.get_table_names(engine.connect())

        expected_tables = {"channels", "videos", "disappearance_events"}
        actual_tables = set(inspector)

        assert expected_tables.issubset(
            actual_tables
        ), f"Missing tables: {expected_tables - actual_tables}"

    def test_video_table_schema(self) -> None:
        """Test that video table has correct schema."""
        result = self.db.execute(text("PRAGMA table_info(videos)"))
        columns = {row[1]: row[2] for row in result.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "video_id": "VARCHAR(255)",
            "channel_id": "VARCHAR(255)",
            "title": "VARCHAR(500)",
            "description": "TEXT",
            "thumbnail_url": "VARCHAR(500)",
            "published_at": "DATETIME",
            "duration": "VARCHAR(50)",
            "view_count": "INTEGER",
            "is_available": "BOOLEAN",
            "last_seen_at": "DATETIME",
            "first_detected_at": "DATETIME",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Missing column: {col_name}"

    def test_disappearance_events_table_schema(self) -> None:
        """Test that disappearance_events table has correct schema."""
        result = self.db.execute(text("PRAGMA table_info(disappearance_events)"))
        columns = {row[1]: row[2] for row in result.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "video_id": "VARCHAR(255)",
            "event_type": "VARCHAR(13)",
            "detected_at": "DATETIME",
            "details": "JSON",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Missing column: {col_name}"

    def test_foreign_key_constraints(self) -> None:
        """Test that foreign key relationships work correctly."""
        channel = Channel(
            channel_id="UCtest123",
            title="Test Channel",
            uploads_playlist_id="UUtest123",
            source_input="@test",
        )
        self.db.add(channel)
        self.db.commit()

        video = Video(
            video_id="test_video_123",
            channel_id="UCtest123",
            title="Test Video",
            published_at=pytest.importorskip("datetime").datetime.now(
                pytest.importorskip("datetime").timezone.utc
            ),
        )
        self.db.add(video)
        self.db.commit()

        event = DisappearanceEvent(
            video_id="test_video_123",
            event_type=EventType.PRIVATE,
        )
        self.db.add(event)
        self.db.commit()

        assert self.db.query(Channel).count() == 1
        assert self.db.query(Video).count() == 1
        assert self.db.query(DisappearanceEvent).count() == 1
