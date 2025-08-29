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

        if not self.enabled:
            logger.info(
                "Slack notifications disabled: SLACK_WEBHOOK_URL not configured"
            )

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

        try:
            message = self._format_message(event, video, channel)
            success = await self._send_webhook(message)

            if success:
                logger.info(
                    "Slack notification sent for video disappearance",
                    extra={
                        "video_id": video.video_id,
                        "channel_id": channel.channel_id,
                        "event_type": event.event_type.value,
                        "detected_at": event.detected_at.isoformat(),
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
    ) -> dict:
        """Format the Slack message payload."""
        event_type_emoji = {
            "PRIVATE": "🔒",
            "DELETED": "🗑️",
            "GEO_BLOCKED": "🌍",
            "AGE_RESTRICTED": "🔞",
            "UNKNOWN": "❓",
        }

        emoji = event_type_emoji.get(event.event_type.value, "❓")
        event_type_display = event.event_type.value.replace("_", " ").title()

        title = str(video.title) if video.title else ""
        if len(title) > 100:
            title = title[:97] + "..."

        detected_time = event.detected_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        youtube_url = f"https://www.youtube.com/watch?v={video.video_id}"

        message = {
            "text": f"{emoji} Video Disappeared: {event_type_display}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Video Disappeared: {event_type_display}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Channel:*\n{channel.title}"},
                        {"type": "mrkdwn", "text": f"*Video ID:*\n`{video.video_id}`"},
                        {"type": "mrkdwn", "text": f"*Detected:*\n{detected_time}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Event Type:*\n{event_type_display}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Video Title:*\n{title}"},
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Check on YouTube"},
                            "url": youtube_url,
                            "style": "primary",
                        }
                    ],
                },
            ],
        }

        if event.details:
            context_items = []

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
