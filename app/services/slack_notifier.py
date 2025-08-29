import logging
import os
from typing import Optional

import httpx

from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent
from app.models.video import Video

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Service for sending Slack notifications about video disappearance events."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)

        self.notification_language = os.getenv("SLACK_NOTIFICATION_LANGUAGE", "en")
        self.min_severity_threshold = os.getenv("SLACK_MIN_SEVERITY", "LOW")
        self.renotification_hours = int(os.getenv("SLACK_RENOTIFICATION_HOURS", "24"))
        self.max_notifications_per_video = int(
            os.getenv("SLACK_MAX_NOTIFICATIONS_PER_VIDEO", "3")
        )

        if not self.enabled:
            logger.info(
                "Slack notifications disabled: SLACK_WEBHOOK_URL not configured"
            )

    def _get_event_severity(self, event_type: str) -> str:
        """Get severity level for event type."""
        severity_map = {
            "DELETED": "HIGH",
            "PRIVATE": "MEDIUM",
            "GEO_BLOCKED": "LOW",
            "AGE_RESTRICTED": "LOW",
            "UNKNOWN": "MEDIUM",
        }
        return severity_map.get(event_type, "MEDIUM")

    def _should_send_notification(
        self, event: DisappearanceEvent, video: Video
    ) -> bool:
        """Check if notification should be sent based on thresholds and rules."""
        event_severity = self._get_event_severity(event.event_type.value)
        severity_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

        min_level = severity_levels.get(self.min_severity_threshold, 1)
        event_level = severity_levels.get(event_severity, 2)

        if event_level < min_level:
            logger.debug(
                f"Skipping notification: severity {event_severity} "
                f"below threshold {self.min_severity_threshold}"
            )
            return False

        return True

    async def send_disappearance_alert(
        self,
        event: DisappearanceEvent,
        video: Video,
        channel: Channel,
    ) -> bool:
        """
        Send a Slack notification for a video disappearance event.

        Args:
            event: The disappearance event
            video: The video that disappeared
            channel: The channel the video belongs to

        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Slack notification skipped: not enabled")
            return False

        if not self._should_send_notification(event, video):
            return False

        try:
            message = self._format_message(
                event, video, channel, self.notification_language
            )
            success = await self._send_webhook(message)

            if success:
                logger.info(
                    "Slack notification sent for video disappearance",
                    extra={
                        "video_id": video.video_id,
                        "channel_id": channel.channel_id,
                        "event_type": event.event_type.value,
                        "detected_at": event.detected_at.isoformat(),
                        "language": self.notification_language,
                        "severity": self._get_event_severity(event.event_type.value),
                    },
                )
            else:
                logger.warning(
                    "Failed to send Slack notification",
                    extra={
                        "video_id": video.video_id,
                        "channel_id": channel.channel_id,
                        "event_type": event.event_type.value,
                    },
                )

            return success

        except Exception as e:
            logger.error(
                f"Error sending Slack notification: {e}",
                extra={
                    "video_id": video.video_id,
                    "channel_id": channel.channel_id,
                    "event_type": event.event_type.value,
                },
                exc_info=True,
            )
            return False

    def _format_message(
        self,
        event: DisappearanceEvent,
        video: Video,
        channel: Channel,
        language: str = "en",
    ) -> dict:
        """Format the Slack message payload with bilingual support."""
        event_type_emoji = {
            "PRIVATE": "🔒",
            "DELETED": "🗑️",
            "GEO_BLOCKED": "🌍",
            "AGE_RESTRICTED": "🔞",
            "UNKNOWN": "❓",
        }

        severity_icons = {
            "DELETED": "🚨",
            "PRIVATE": "⚠️",
            "GEO_BLOCKED": "ℹ️",
            "AGE_RESTRICTED": "ℹ️",
            "UNKNOWN": "❓",
        }

        emoji = event_type_emoji.get(event.event_type.value, "❓")
        severity = severity_icons.get(event.event_type.value, "❓")

        if language == "ja":
            event_type_display = {
                "PRIVATE": "非公開",
                "DELETED": "削除済み",
                "GEO_BLOCKED": "地域制限",
                "AGE_RESTRICTED": "年齢制限",
                "UNKNOWN": "不明",
            }.get(event.event_type.value, "不明")
            header_text = f"{severity}{emoji} 動画が消失しました: {event_type_display}"
            button_text = "YouTubeで確認"
            fields = [
                {"type": "mrkdwn", "text": f"*チャンネル:*\n{channel.title}"},
                {"type": "mrkdwn", "text": f"*動画ID:*\n`{video.video_id}`"},
                {
                    "type": "mrkdwn",
                    "text": (
                        f"*検出日時:*\n"
                        f"{event.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    ),
                },
                {"type": "mrkdwn", "text": f"*イベント種別:*\n{event_type_display}"},
            ]
            title_prefix = "*動画タイトル:*\n"
        else:
            event_type_display = event.event_type.value.replace("_", " ").title()
            header_text = f"{severity}{emoji} Video Disappeared: {event_type_display}"
            button_text = "Check on YouTube"
            fields = [
                {"type": "mrkdwn", "text": f"*Channel:*\n{channel.title}"},
                {"type": "mrkdwn", "text": f"*Video ID:*\n`{video.video_id}`"},
                {
                    "type": "mrkdwn",
                    "text": (
                        f"*Detected:*\n"
                        f"{event.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    ),
                },
                {"type": "mrkdwn", "text": f"*Event Type:*\n{event_type_display}"},
            ]
            title_prefix = "*Video Title:*\n"

        title = str(video.title) if video.title else ""
        if len(title) > 100:
            title = title[:97] + "..."

        youtube_url = f"https://www.youtube.com/watch?v={video.video_id}"

        message = {
            "text": header_text,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": header_text,
                    },
                },
                {
                    "type": "section",
                    "fields": fields,
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{title_prefix}{title}"},
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": button_text},
                            "url": youtube_url,
                            "style": "primary",
                        }
                    ],
                },
            ],
        }

        if event.details:
            context_items = []
            if language == "ja":
                if "view_count" in event.details:
                    context_items.append(f"再生回数: {event.details['view_count']:,}")
                if "duration" in event.details:
                    context_items.append(f"長さ: {event.details['duration']}")
                if "published_at" in event.details:
                    context_items.append(f"公開日: {event.details['published_at']}")
            else:
                if "view_count" in event.details:
                    context_items.append(f"Views: {event.details['view_count']:,}")
                if "duration" in event.details:
                    context_items.append(f"Duration: {event.details['duration']}")
                if "published_at" in event.details:
                    context_items.append(f"Published: {event.details['published_at']}")

            if context_items:
                blocks = list(message.get("blocks", []))
                blocks.append(
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": " • ".join(context_items)}
                        ],
                    }
                )
                message["blocks"] = blocks

        return message

    async def _send_webhook(self, message: dict) -> bool:
        """Send the webhook request to Slack."""
        if not self.webhook_url:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    return True
                else:
                    logger.warning(
                        "Slack webhook returned status %d: %s",
                        response.status_code,
                        response.text,
                    )
                    return False

        except httpx.TimeoutException:
            logger.warning("Slack webhook request timed out")
            return False
        except httpx.RequestError as e:
            logger.warning(f"Slack webhook request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack webhook: {e}")
            return False

    async def send_test_notification(self) -> bool:
        """Send a test notification to verify Slack integration."""
        if not self.enabled:
            return False

        test_message = {
            "text": "🧪 YouTube Tracker Test Notification",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🧪 YouTube Tracker Test Notification",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "This is a test notification to verify that Slack "
                        "integration is working correctly.",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "If you received this message, your Slack webhook "
                            "is configured properly.",
                        }
                    ],
                },
            ],
        }

        success = await self._send_webhook(test_message)

        if success:
            logger.info("Slack test notification sent successfully")
        else:
            logger.warning("Failed to send Slack test notification")

        return success
