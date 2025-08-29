"""Simple tests for Phase 5 hardening and UX improvements."""

import os
from unittest.mock import Mock, patch

from app.core.i18n import I18n
from app.services.slack_notifier import SlackNotifier


class TestSlackNotifierEnhancements:
    """Test enhanced Slack notification features."""

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

    def test_get_event_severity(self):
        """Test severity level mapping."""
        notifier = SlackNotifier()

        assert notifier._get_event_severity("DELETED") == "HIGH"
        assert notifier._get_event_severity("PRIVATE") == "MEDIUM"
        assert notifier._get_event_severity("GEO_BLOCKED") == "LOW"
        assert notifier._get_event_severity("AGE_RESTRICTED") == "LOW"
        assert notifier._get_event_severity("UNKNOWN") == "MEDIUM"

    def test_bilingual_message_format_basic(self):
        """Test basic bilingual message formatting."""
        notifier = SlackNotifier()

        event = Mock()
        event.event_type.value = "DELETED"
        event.detected_at.strftime.return_value = "2025-08-29 10:30:00 UTC"
        event.details = {}

        video = Mock()
        video.video_id = "test123"
        video.title = "Test Video"

        channel = Mock()
        channel.title = "Test Channel"

        message_en = notifier._format_message(event, video, channel, "en")
        assert "🚨🗑️ Video Disappeared: Deleted" in message_en["text"]
        assert "Check on YouTube" in str(message_en["blocks"])

        message_ja = notifier._format_message(event, video, channel, "ja")
        assert "🚨🗑️ 動画が消失しました: 削除済み" in message_ja["text"]
        assert "YouTubeで確認" in str(message_ja["blocks"])


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

    def test_language_switching(self):
        """Test language switching functionality."""
        i18n = I18n(default_language="en")

        assert i18n.get_language() == "en"

        i18n.set_language("ja")
        assert i18n.get_language() == "ja"

        i18n.set_language("invalid")
        assert i18n.get_language() == "ja"


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    def test_slack_configuration_defaults(self):
        """Test Slack configuration with default values."""
        with patch.dict(os.environ, {}, clear=True):
            notifier = SlackNotifier()

            assert notifier.notification_language == "en"
            assert notifier.min_severity_threshold == "LOW"
            assert notifier.renotification_hours == 24
            assert notifier.max_notifications_per_video == 3

    def test_slack_configuration_custom(self):
        """Test Slack configuration with custom values."""
        with patch.dict(
            os.environ,
            {
                "SLACK_NOTIFICATION_LANGUAGE": "ja",
                "SLACK_MIN_SEVERITY": "HIGH",
                "SLACK_RENOTIFICATION_HOURS": "48",
                "SLACK_MAX_NOTIFICATIONS_PER_VIDEO": "5",
            },
        ):
            notifier = SlackNotifier()

            assert notifier.notification_language == "ja"
            assert notifier.min_severity_threshold == "HIGH"
            assert notifier.renotification_hours == 48
            assert notifier.max_notifications_per_video == 5
