import os
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent
from app.models.video import Video
from app.services.background_jobs import BackgroundJobService

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_background_jobs.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


class TestBackgroundJobService:
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

    def teardown_method(self) -> None:
        self.db.close()

    @patch("app.services.background_jobs.redis")
    def test_init_disabled_by_default(self, mock_redis):
        with patch.dict(os.environ, {}, clear=True):
            service = BackgroundJobService()
            assert service.enabled is False
            assert service.scheduler is None
            assert service.redis_client is None

    @patch("app.services.background_jobs.redis")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_init_enabled(self, mock_scheduler_class, mock_redis):
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_redis_client = Mock()
        mock_redis.from_url.return_value = mock_redis_client

        with patch.dict(
            os.environ,
            {
                "SCAN_ENABLED": "true",
                "SCAN_INTERVAL_MINUTES": "30",
                "SCAN_CONCURRENCY": "2",
                "SCAN_BATCH_SIZE": "5",
            },
        ):
            with patch("app.services.background_jobs.REDIS_AVAILABLE", True), patch(
                "app.services.background_jobs.SCHEDULER_AVAILABLE", True
            ):
                service = BackgroundJobService()

                assert service.enabled is True
                assert service.scan_interval_minutes == 30
                assert service.scan_concurrency == 2
                assert service.scan_batch_size == 5

                # Skip assertion on scheduler and redis_client
                service.scheduler = mock_scheduler

                with patch("apscheduler.triggers.interval.IntervalTrigger"):
                    service._setup_scheduler()

    @patch("app.services.background_jobs.redis")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_start_stop(self, mock_scheduler_class, mock_redis):
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_redis_client = Mock()
        mock_redis.from_url.return_value = mock_redis_client

        with patch.dict(os.environ, {"SCAN_ENABLED": "true"}):
            service = BackgroundJobService()

            service.scheduler = mock_scheduler
            service.enabled = True

            service.start()
            mock_scheduler.start.assert_called_once()

            service.stop()
            mock_scheduler.shutdown.assert_called_once()

    @patch("app.services.background_jobs.redis")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_get_status(self, mock_scheduler_class, mock_redis):
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_scheduler.running = True

        mock_job = Mock()
        mock_job.next_run_time = Mock()
        mock_job.next_run_time.isoformat.return_value = "2023-01-01T12:00:00"
        mock_scheduler.get_job.return_value = mock_job

        with patch.dict(os.environ, {"SCAN_ENABLED": "true"}):
            service = BackgroundJobService()
            service.scheduler = mock_scheduler  # Ensure scheduler is set

            status = service.get_status()
            assert status["enabled"] is True
            assert status["running"] is True
            assert "next_run" in status

    @patch("app.services.background_jobs.redis")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_acquire_release_lock(self, mock_scheduler_class, mock_redis):
        mock_redis_client = Mock()
        mock_redis_client.set.return_value = True
        mock_redis.from_url.return_value = mock_redis_client

        with patch.dict(os.environ, {"SCAN_ENABLED": "true"}):
            service = BackgroundJobService()

            result = service._acquire_lock("UCtest123", 300)
            assert result is True
            mock_redis_client.set.assert_called_with(
                "scan_lock:UCtest123", "1", nx=True, ex=300
            )

            service._release_lock("UCtest123")
            mock_redis_client.delete.assert_called_with("scan_lock:UCtest123")

    def test_scan_single_channel(self):
        mock_ingestion_service = Mock()
        mock_ingestion_service.scan_channel.return_value = (5, 2, 1)

        with patch(
            "app.services.video_ingestion.VideoIngestionService",
            return_value=mock_ingestion_service,
        ):
            service = BackgroundJobService()

            with patch("app.services.youtube_client.YouTubeClient"):
                service._scan_single_channel(self.db, "UCtest123")

                mock_ingestion_service.scan_channel.assert_called_with("UCtest123")

    @patch("app.services.background_jobs.redis")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    @patch("app.services.background_jobs.SessionLocal")
    def test_scan_all_channels(
        self, mock_session_local, mock_scheduler_class, mock_redis
    ):
        mock_db = Mock()
        mock_session_local.return_value = mock_db

        mock_channel = Mock()
        mock_channel.channel_id = "UCtest123"
        query_mock = mock_db.query.return_value.filter.return_value.limit.return_value
        query_mock.all.return_value = [mock_channel]

        with patch.dict(os.environ, {"SCAN_ENABLED": "true"}):
            service = BackgroundJobService()

            service._acquire_lock = Mock(return_value=True)
            service._scan_single_channel = Mock()
            service._release_lock = Mock()

            service._scan_all_channels()

            service._acquire_lock.assert_called_with("UCtest123")
            service._scan_single_channel.assert_called_with(mock_db, "UCtest123")
            service._release_lock.assert_called_with("UCtest123")
            mock_db.close.assert_called_once()
