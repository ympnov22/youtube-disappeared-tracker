from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.background_jobs import BackgroundJobService


class TestBackgroundJobServiceExtended:
    def setup_method(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "SCAN_ENABLED": "true",
                "SCAN_INTERVAL_MINUTES": "30",
                "SCAN_CONCURRENCY": "2",
                "SCAN_BATCH_SIZE": "5",
                "REDIS_URL": "redis://localhost:6379/0",
            },
        ):
            with patch("app.services.background_jobs.REDIS_AVAILABLE", True), patch(
                "app.services.background_jobs.SCHEDULER_AVAILABLE", True
            ):
                self.service = BackgroundJobService()

    def test_init_disabled_by_env(self) -> None:
        with patch.dict("os.environ", {"SCAN_ENABLED": "false"}):
            service = BackgroundJobService()
            assert service.enabled is False

    def test_init_redis_unavailable(self) -> None:
        with patch.dict("os.environ", {"SCAN_ENABLED": "true"}), patch(
            "app.services.background_jobs.REDIS_AVAILABLE", False
        ), patch("app.services.background_jobs.SCHEDULER_AVAILABLE", True):
            service = BackgroundJobService()
            assert service.enabled is False

    def test_init_scheduler_unavailable(self) -> None:
        with patch.dict("os.environ", {"SCAN_ENABLED": "true"}), patch(
            "app.services.background_jobs.REDIS_AVAILABLE", True
        ), patch("app.services.background_jobs.SCHEDULER_AVAILABLE", False):
            service = BackgroundJobService()
            assert service.enabled is False

    def test_setup_redis_connection_failure(self) -> None:
        with patch.dict(
            "os.environ",
            {"SCAN_ENABLED": "true", "REDIS_URL": "redis://invalid:6379/0"},
        ), patch("app.services.background_jobs.REDIS_AVAILABLE", True), patch(
            "app.services.background_jobs.SCHEDULER_AVAILABLE", True
        ), patch(
            "app.services.background_jobs.redis.from_url"
        ) as mock_redis:
            mock_client = Mock()
            mock_client.ping.side_effect = Exception("Connection failed")
            mock_redis.return_value = mock_client

            service = BackgroundJobService()
            assert service.enabled is False

    def test_setup_redis_not_available(self) -> None:
        with patch("app.services.background_jobs.REDIS_AVAILABLE", False):
            service = BackgroundJobService()
            service._setup_redis()
            assert service.redis_client is None

    def test_setup_scheduler_disabled(self) -> None:
        service = BackgroundJobService()
        service.enabled = False
        service._setup_scheduler()
        assert service.scheduler is None

    def test_setup_scheduler_not_available(self) -> None:
        with patch("app.services.background_jobs.SCHEDULER_AVAILABLE", False):
            service = BackgroundJobService()
            service.enabled = True
            service._setup_scheduler()
            assert service.scheduler is None

    def test_start_disabled(self) -> None:
        service = BackgroundJobService()
        service.enabled = False
        service.start()

    def test_start_no_scheduler(self) -> None:
        service = BackgroundJobService()
        service.enabled = True
        service.scheduler = None
        service.start()

    def test_stop_no_scheduler(self) -> None:
        service = BackgroundJobService()
        service.scheduler = None
        service.stop()

    def test_get_status_disabled(self) -> None:
        service = BackgroundJobService()
        service.enabled = False
        status = service.get_status()
        assert status == {"enabled": False, "next_run": None}

    def test_get_status_no_scheduler(self) -> None:
        service = BackgroundJobService()
        service.enabled = True
        service.scheduler = None
        status = service.get_status()
        assert status["enabled"] is True
        assert status["running"] is False
        assert status["next_run"] is None

    def test_get_status_no_job(self) -> None:
        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = None
        mock_scheduler.running = True

        service = BackgroundJobService()
        service.enabled = True
        service.scheduler = mock_scheduler

        status = service.get_status()
        assert status["enabled"] is True
        assert status["running"] is True
        assert status["next_run"] is None

    def test_acquire_lock_no_redis(self) -> None:
        service = BackgroundJobService()
        service.redis_client = None
        result = service._acquire_lock("UCtest123")
        assert result is True

    def test_acquire_lock_success(self) -> None:
        mock_redis = Mock()
        mock_redis.set.return_value = True

        service = BackgroundJobService()
        service.redis_client = mock_redis

        result = service._acquire_lock("UCtest123", timeout=300)
        assert result is True
        mock_redis.set.assert_called_once_with(
            "scan_lock:UCtest123", "1", nx=True, ex=300
        )

    def test_acquire_lock_failure(self) -> None:
        mock_redis = Mock()
        mock_redis.set.return_value = None

        service = BackgroundJobService()
        service.redis_client = mock_redis

        result = service._acquire_lock("UCtest123")
        assert result is False

    def test_release_lock_no_redis(self) -> None:
        service = BackgroundJobService()
        service.redis_client = None
        service._release_lock("UCtest123")

    def test_release_lock_success(self) -> None:
        mock_redis = Mock()

        service = BackgroundJobService()
        service.redis_client = mock_redis

        service._release_lock("UCtest123")
        mock_redis.delete.assert_called_once_with("scan_lock:UCtest123")

    @patch("app.services.background_jobs.SessionLocal")
    def test_scan_all_channels_success(self, mock_session_local: Mock) -> None:
        mock_db = Mock(spec=Session)
        mock_session_local.return_value = mock_db

        mock_channel = Mock()
        mock_channel.channel_id = "UCtest123"
        query_chain = mock_db.query.return_value.filter.return_value.limit.return_value
        query_chain.all.return_value = [mock_channel]

        service = BackgroundJobService()
        service.scan_batch_size = 1

        with patch.object(service, "_acquire_lock", return_value=True), patch.object(
            service, "_scan_single_channel"
        ) as mock_scan, patch.object(service, "_release_lock") as mock_release:
            service._scan_all_channels()

            mock_scan.assert_called_once_with(mock_db, "UCtest123")
            mock_release.assert_called_once_with("UCtest123")

    @patch("app.services.background_jobs.SessionLocal")
    def test_scan_all_channels_lock_failed(self, mock_session_local: Mock) -> None:
        mock_db = Mock(spec=Session)
        mock_session_local.return_value = mock_db

        mock_channel = Mock()
        mock_channel.channel_id = "UCtest123"
        query_chain = mock_db.query.return_value.filter.return_value.limit.return_value
        query_chain.all.return_value = [mock_channel]

        service = BackgroundJobService()
        service.scan_batch_size = 1

        with patch.object(service, "_acquire_lock", return_value=False), patch.object(
            service, "_scan_single_channel"
        ) as mock_scan:
            service._scan_all_channels()

            mock_scan.assert_not_called()

    @patch("app.services.background_jobs.SessionLocal")
    def test_scan_all_channels_scan_error(self, mock_session_local: Mock) -> None:
        mock_db = Mock(spec=Session)
        mock_session_local.return_value = mock_db

        mock_channel = Mock()
        mock_channel.channel_id = "UCtest123"
        query_chain = mock_db.query.return_value.filter.return_value.limit.return_value
        query_chain.all.return_value = [mock_channel]

        service = BackgroundJobService()
        service.scan_batch_size = 1

        with patch.object(service, "_acquire_lock", return_value=True), patch.object(
            service, "_scan_single_channel", side_effect=Exception("Scan failed")
        ), patch.object(service, "_release_lock") as mock_release:
            service._scan_all_channels()

            mock_release.assert_called_once_with("UCtest123")

    def test_scan_single_channel_success(self) -> None:
        mock_db = Mock(spec=Session)

        with patch(
            "app.services.youtube_client.YouTubeClient"
        ) as mock_youtube_class, patch(
            "app.services.video_ingestion.VideoIngestionService"
        ) as mock_ingestion_class:
            mock_youtube = Mock()
            mock_youtube_class.return_value = mock_youtube

            mock_ingestion = Mock()
            mock_ingestion.scan_channel.return_value = (5, 2, 1)
            mock_ingestion_class.return_value = mock_ingestion

            service = BackgroundJobService()
            service._scan_single_channel(mock_db, "UCtest123")

            mock_ingestion.scan_channel.assert_called_once_with("UCtest123")

    def test_scan_single_channel_error(self) -> None:
        mock_db = Mock(spec=Session)

        with patch(
            "app.services.youtube_client.YouTubeClient"
        ) as mock_youtube_class, patch(
            "app.services.video_ingestion.VideoIngestionService"
        ) as mock_ingestion_class:
            mock_youtube = Mock()
            mock_youtube_class.return_value = mock_youtube

            mock_ingestion = Mock()
            mock_ingestion.scan_channel.side_effect = Exception("API Error")
            mock_ingestion_class.return_value = mock_ingestion

            service = BackgroundJobService()

            with pytest.raises(Exception, match="API Error"):
                service._scan_single_channel(mock_db, "UCtest123")

    def test_environment_variable_parsing(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "SCAN_ENABLED": "true",
                "SCAN_INTERVAL_MINUTES": "120",
                "SCAN_CONCURRENCY": "4",
                "SCAN_BATCH_SIZE": "20",
                "REDIS_URL": "redis://localhost:6379/0",
            },
        ), patch("app.services.background_jobs.REDIS_AVAILABLE", True), patch(
            "app.services.background_jobs.SCHEDULER_AVAILABLE", True
        ), patch(
            "app.services.background_jobs.redis.from_url"
        ) as mock_redis:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            service = BackgroundJobService()
            assert service.enabled is True
            assert service.scan_interval_minutes == 120
            assert service.scan_concurrency == 4
            assert service.scan_batch_size == 20

    def test_default_environment_values(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            service = BackgroundJobService()
            assert service.enabled is False
            assert service.scan_interval_minutes == 60
            assert service.scan_concurrency == 1
            assert service.scan_batch_size == 10
