from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import RequestError, TimeoutException

from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent, EventType
from app.models.video import Video
from app.services.slack_notifier import SlackNotifier


class TestSlackNotifier:
    def test_init_with_webhook_url(self):
        webhook_url = "https://hooks.slack.com/services/test"
        notifier = SlackNotifier(webhook_url)
        assert notifier.webhook_url == webhook_url
        assert notifier.enabled is True

    def test_init_without_webhook_url(self):
        notifier = SlackNotifier()
        assert notifier.webhook_url is None
        assert notifier.enabled is False

    @patch.dict(
        "os.environ", {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/env"}
    )
    def test_init_from_env(self):
        notifier = SlackNotifier()
        assert notifier.webhook_url == "https://hooks.slack.com/services/env"
        assert notifier.enabled is True

    def test_format_message_basic(self):
        notifier = SlackNotifier("https://test.com")

        channel = Channel(
            channel_id="UC123", title="Test Channel", uploads_playlist_id="UU123"
        )

        video = Video(
            video_id="abc123",
            channel_id="UC123",
            title="Test Video",
            description="Test description",
            is_available=False,
        )

        from datetime import datetime

        event = DisappearanceEvent(
            video_id="abc123",
            event_type=EventType.DELETED,
            details={"title": "Test Video", "channel_id": "UC123"},
            detected_at=datetime.utcnow(),
        )

        message = notifier._format_message(event, video, channel)

        assert message["text"] == "🗑️ Video Disappeared: Deleted"
        assert len(message["blocks"]) >= 4
        assert message["blocks"][0]["text"]["text"] == "🗑️ Video Disappeared: Deleted"

        fields = message["blocks"][1]["fields"]
        channel_field = next(f for f in fields if "Channel" in f["text"])
        assert "Test Channel" in channel_field["text"]

    def test_format_message_with_details(self):
        notifier = SlackNotifier("https://test.com")

        channel = Channel(
            channel_id="UC123", title="Test Channel", uploads_playlist_id="UU123"
        )

        video = Video(
            video_id="abc123",
            channel_id="UC123",
            title="Test Video",
            description="Test description",
            is_available=False,
        )

        from datetime import datetime

        event = DisappearanceEvent(
            video_id="abc123",
            event_type=EventType.PRIVATE,
            details={
                "title": "Test Video",
                "channel_id": "UC123",
                "view_count": 1000,
                "duration": "PT5M30S",
                "published_at": "2023-01-01T00:00:00",
            },
            detected_at=datetime.utcnow(),
        )

        message = notifier._format_message(event, video, channel)

        assert len(message["blocks"]) >= 5
        context_block = message["blocks"][-1]
        assert context_block["type"] == "context"
        context_text = context_block["elements"][0]["text"]
        assert "Views: 1,000" in context_text
        assert "Duration: PT5M30S" in context_text
        assert "Published: 2023-01-01T00:00:00" in context_text

    def test_format_message_long_title(self):
        notifier = SlackNotifier("https://test.com")

        channel = Channel(
            channel_id="UC123", title="Test Channel", uploads_playlist_id="UU123"
        )

        long_title = "A" * 150  # Longer than 100 chars
        video = Video(
            video_id="abc123", channel_id="UC123", title=long_title, is_available=False
        )

        from datetime import datetime

        event = DisappearanceEvent(
            video_id="abc123",
            event_type=EventType.DELETED,
            details={"title": long_title, "channel_id": "UC123"},
            detected_at=datetime.utcnow(),
        )

        message = notifier._format_message(event, video, channel)

        title_block = message["blocks"][2]
        title_text = title_block["text"]["text"]
        assert "..." in title_text
        assert (
            len(title_text) <= 120
        )  # "Video Title:\n" + truncated title + some buffer

    @pytest.mark.asyncio
    async def test_send_webhook_success(self):
        notifier = SlackNotifier("https://hooks.slack.com/services/test")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await notifier._send_webhook({"test": "message"})

            assert result is True
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_webhook_failure(self):
        notifier = SlackNotifier("https://hooks.slack.com/services/test")

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await notifier._send_webhook({"test": "message"})

            assert result is False

    @pytest.mark.asyncio
    async def test_send_webhook_timeout(self):
        notifier = SlackNotifier("https://hooks.slack.com/services/test")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=TimeoutException("Timeout")
            )

            result = await notifier._send_webhook({"test": "message"})

            assert result is False

    @pytest.mark.asyncio
    async def test_send_webhook_request_error(self):
        notifier = SlackNotifier("https://hooks.slack.com/services/test")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=RequestError("Connection failed")
            )

            result = await notifier._send_webhook({"test": "message"})

            assert result is False

    @pytest.mark.asyncio
    async def test_send_webhook_no_url(self):
        notifier = SlackNotifier()

        result = await notifier._send_webhook({"test": "message"})

        assert result is False

    @pytest.mark.asyncio
    async def test_send_disappearance_alert_disabled(self):
        notifier = SlackNotifier()  # No webhook URL

        channel = Channel(
            channel_id="UC123", title="Test Channel", uploads_playlist_id="UU123"
        )
        video = Video(
            video_id="abc123",
            channel_id="UC123",
            title="Test Video",
            is_available=False,
        )
        from datetime import datetime

        event = DisappearanceEvent(
            video_id="abc123",
            event_type=EventType.DELETED,
            detected_at=datetime.utcnow(),
        )

        result = await notifier.send_disappearance_alert(event, video, channel)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_disappearance_alert_success(self):
        notifier = SlackNotifier("https://hooks.slack.com/services/test")

        channel = Channel(
            channel_id="UC123", title="Test Channel", uploads_playlist_id="UU123"
        )
        video = Video(
            video_id="abc123",
            channel_id="UC123",
            title="Test Video",
            is_available=False,
        )
        from datetime import datetime

        event = DisappearanceEvent(
            video_id="abc123",
            event_type=EventType.DELETED,
            detected_at=datetime.utcnow(),
        )

        with patch.object(notifier, "_send_webhook", return_value=True) as mock_send:
            result = await notifier.send_disappearance_alert(event, video, channel)

            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_disappearance_alert_failure(self):
        notifier = SlackNotifier("https://hooks.slack.com/services/test")

        channel = Channel(
            channel_id="UC123", title="Test Channel", uploads_playlist_id="UU123"
        )
        video = Video(
            video_id="abc123",
            channel_id="UC123",
            title="Test Video",
            is_available=False,
        )
        from datetime import datetime

        event = DisappearanceEvent(
            video_id="abc123",
            event_type=EventType.DELETED,
            detected_at=datetime.utcnow(),
        )

        with patch.object(notifier, "_send_webhook", return_value=False) as mock_send:
            result = await notifier.send_disappearance_alert(event, video, channel)

            assert result is False
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_test_notification_success(self):
        notifier = SlackNotifier("https://hooks.slack.com/services/test")

        with patch.object(notifier, "_send_webhook", return_value=True) as mock_send:
            result = await notifier.send_test_notification()

            assert result is True
            mock_send.assert_called_once()

            call_args = mock_send.call_args[0][0]
            assert "Test Notification" in call_args["text"]

    @pytest.mark.asyncio
    async def test_send_test_notification_disabled(self):
        notifier = SlackNotifier()  # No webhook URL

        result = await notifier.send_test_notification()

        assert result is False
