"""Tests for Phase 5 hardening and UX improvements."""

import os
from unittest.mock import Mock, patch

import pytest
from googleapiclient.errors import HttpError

from app.core.i18n import I18n
from app.services.background_jobs import BackgroundJobService
from app.services.slack_notifier import SlackNotifier
from app.services.youtube_client import YouTubeClient, YouTubeQuotaExhaustedError


class TestSlackNotifierEnhancements:
    """Test enhanced Slack notification features."""

    def test_bilingual_message_formatting_english(self):
        """Test English message formatting."""
        notifier = SlackNotifier()

        event = Mock()
        event.event_type.value = "DELETED"
        event.detected_at.strftime.return_value = "2025-08-29 10:30:00 UTC"
        event.details = {"view_count": 1000, "duration": "PT5M30S"}

        video = Mock()
        video.video_id = "test123"
        video.title = "Test Video"

        channel = Mock()
        channel.title = "Test Channel"

        message = notifier._format_message(event, video, channel, "en")

        assert "🚨🗑️ Video Disappeared: Deleted" in message["text"]
        blocks_str = str(message["blocks"])
        assert "Test Channel" in blocks_str
        assert "test123" in blocks_str
        assert "Check on YouTube" in blocks_str

    def test_bilingual_message_formatting_japanese(self):
        """Test Japanese message formatting."""
        notifier = SlackNotifier()

        event = Mock()
        event.event_type.value = "PRIVATE"
        event.detected_at.strftime.return_value = "2025-08-29 10:30:00 UTC"
        event.details = {}

        video = Mock()
        video.video_id = "test123"
        video.title = "テスト動画"

        channel = Mock()
        channel.title = "テストチャンネル"

        message = notifier._format_message(event, video, channel, "ja")

        assert "⚠️🔒 動画が消失しました: 非公開" in message["text"]
        blocks_str = str(message["blocks"])
        assert "テストチャンネル" in blocks_str
        assert "YouTubeで確認" in blocks_str

    def test_severity_threshold_filtering(self):
        """Test notification filtering by severity threshold."""
        with patch.dict(os.environ, {"SLACK_MIN_SEVERITY": "HIGH"}):
            notifier = SlackNotifier()

            high_event = Mock()
            high_event.event_type.value = "DELETED"

            low_event = Mock()
            low_event.event_type.value = "GEO_BLOCKED"

            video = Mock()

            assert notifier._should_send_notification(high_event, video) is True
            assert notifier._should_send_notification(low_event, video) is False


class TestYouTubeClientRetry:
    """Test YouTube API retry and backoff mechanisms."""

    @patch("app.services.youtube_client.time.sleep")
    def test_retry_on_rate_limit(self, mock_sleep):
        """Test retry behavior on rate limit (429) errors."""
        client = YouTubeClient()

        mock_request = Mock()

        error1 = HttpError(Mock(status=429), b"Rate limit exceeded")
        error2 = HttpError(Mock(status=429), b"Rate limit exceeded")

        mock_request.execute.side_effect = [error1, error2, {"items": [{"id": "test"}]}]

        result = client._execute_with_retry(mock_request, "test operation")

        assert result == {"items": [{"id": "test"}]}
        assert mock_request.execute.call_count == 3
        assert mock_sleep.call_count == 2

    def test_quota_exhausted_exception(self):
        """Test quota exhausted error handling."""
        client = YouTubeClient()

        error = HttpError(Mock(status=403), b"Quota exceeded")
        error.error_details = [{"reason": "quotaExceeded"}]

        mock_request = Mock()
        mock_request.execute.side_effect = error

        with pytest.raises(YouTubeQuotaExhaustedError):
            client._execute_with_retry(mock_request, "test operation")

    @patch("app.services.youtube_client.time.sleep")
    def test_exponential_backoff_timing(self, mock_sleep):
        """Test exponential backoff timing calculation."""
        with patch.dict(
            os.environ,
            {"YOUTUBE_API_BASE_DELAY": "1.0", "YOUTUBE_API_BACKOFF_MULTIPLIER": "2.0"},
        ):
            client = YouTubeClient()

            mock_request = Mock()

            error1 = HttpError(Mock(status=500), b"Server error")
            error2 = HttpError(Mock(status=500), b"Server error")

            mock_request.execute.side_effect = [error1, error2, {"success": True}]

            client._execute_with_retry(mock_request, "test operation")

            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert len(sleep_calls) == 2
            assert sleep_calls[0] >= 1.0
            assert sleep_calls[1] >= 2.0


class TestBackgroundJobLocking:
    """Test enhanced background job locking mechanisms."""

    @patch("app.services.background_jobs.redis")
    def test_lock_acquisition_with_retry(self, mock_redis_module):
        """Test lock acquisition with retry logic."""
        mock_redis = Mock()
        mock_redis_module.from_url.return_value = mock_redis

        mock_redis.set.side_effect = [False, True]
        mock_redis.get.return_value = None

        service = BackgroundJobService()
        service.redis_client = mock_redis

        result = service._acquire_lock("test_channel")

        assert result is True
        assert mock_redis.set.call_count == 2

    @patch("app.services.background_jobs.redis")
    @patch("app.services.background_jobs.time.time")
    def test_stale_lock_detection(self, mock_time, mock_redis_module):
        """Test detection and cleanup of stale locks."""
        mock_redis = Mock()
        mock_redis_module.from_url.return_value = mock_redis

        current_time = 1000.0
        stale_time = 500.0
        mock_time.return_value = current_time

        stale_lock_value = f"12345:{stale_time}"
        mock_redis.set.side_effect = [False, True]
        mock_redis.get.return_value = stale_lock_value.encode("utf-8")

        service = BackgroundJobService()
        service.redis_client = mock_redis

        with patch.object(service, "_force_release_lock") as mock_force_release:
            result = service._acquire_lock("test_channel", timeout=300)

            assert result is True
            mock_force_release.assert_called_once_with("test_channel", stale_lock_value)


class TestI18nSystem:
    """Test internationalization system."""

    def test_translation_retrieval(self):
        """Test basic translation retrieval."""
        i18n = I18n(default_language="en")

        assert i18n.t("nav.channels") == "Channels"

        i18n.set_language("ja")
        assert i18n.t("nav.channels") == "チャンネル"

    def test_translation_formatting(self):
        """Test translation with formatting parameters."""
        i18n = I18n(default_language="en")

        result = i18n.t("pagination.page_of", current=1, total=5)
        assert result == "Page 1 of 5"

        i18n.set_language("ja")
        result = i18n.t("pagination.page_of", current=1, total=5)
        assert result == "1 / 5 ページ"

    def test_fallback_behavior(self):
        """Test fallback behavior for missing translations."""
        i18n = I18n(default_language="en")

        assert i18n.t("non.existent.key") == "non.existent.key"
