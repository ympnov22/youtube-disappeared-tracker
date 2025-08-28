import os
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeClient:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is required")

        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    def resolve_channel_input(
        self, input_str: str
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Resolve various channel input formats to channel ID and metadata.

        Args:
            input_str: Channel URL, @handle, or channel ID

        Returns:
            Tuple of (channel_id, channel_metadata) or (None, None) if not found
        """
        channel_id = self._extract_channel_id(input_str)

        if channel_id:
            return self._get_channel_metadata(channel_id)

        return self._resolve_by_handle_or_username(input_str)

    def _extract_channel_id(self, input_str: str) -> Optional[str]:
        """Extract channel ID from various URL formats or return if already a channel ID."""  # noqa: E501
        if re.match(r"^UC[a-zA-Z0-9_-]{22}$", input_str):
            return input_str

        try:
            parsed = urlparse(input_str)
            path = parsed.path

            channel_match = re.match(r"^/channel/(UC[a-zA-Z0-9_-]{22})/?$", path)
            if channel_match:
                return channel_match.group(1)

        except Exception:
            pass

        return None

    def _resolve_by_handle_or_username(
        self, input_str: str
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """Resolve @handle or /user/username or /c/customname to channel ID."""
        try:
            parsed = urlparse(input_str)
            path = parsed.path

            if input_str.startswith("@"):
                handle = input_str[1:]
            elif path.startswith("/@"):
                handle = path[2:]
            elif path.startswith("/user/"):
                username = path[6:]
                return self._search_by_username(username)
            elif path.startswith("/c/"):
                custom_name = path[3:]
                return self._search_by_custom_name(custom_name)
            else:
                handle = input_str.strip()

            return self._search_by_handle(handle)

        except Exception:
            return None, None

    def _search_by_handle(self, handle: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Search for channel by handle."""
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics", forHandle=handle
            )
            response = request.execute()

            if response.get("items"):
                channel = response["items"][0]
                channel_id = channel["id"]
                metadata = self._extract_metadata(channel)
                return channel_id, metadata

        except HttpError:
            pass

        return None, None

    def _search_by_username(
        self, username: str
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """Search for channel by legacy username."""
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics", forUsername=username
            )
            response = request.execute()

            if response.get("items"):
                channel = response["items"][0]
                channel_id = channel["id"]
                metadata = self._extract_metadata(channel)
                return channel_id, metadata

        except HttpError:
            pass

        return None, None

    def _search_by_custom_name(
        self, custom_name: str
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """Search for channel by custom name using search API."""
        try:
            request = self.youtube.search().list(
                part="snippet", q=custom_name, type="channel", maxResults=1
            )
            response = request.execute()

            if response.get("items"):
                channel_id = response["items"][0]["snippet"]["channelId"]
                return self._get_channel_metadata(channel_id)

        except HttpError:
            pass

        return None, None

    def _get_channel_metadata(
        self, channel_id: str
    ) -> Tuple[Optional[str], Optional[Dict]]:
        """Get channel metadata by channel ID."""
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails", id=channel_id
            )
            response = request.execute()

            if response.get("items"):
                channel = response["items"][0]
                metadata = self._extract_metadata(channel)
                return channel_id, metadata

        except HttpError:
            pass

        return None, None

    def _extract_metadata(self, channel_data: Dict) -> Dict:
        """Extract relevant metadata from YouTube API response."""
        snippet = channel_data.get("snippet", {})
        statistics = channel_data.get("statistics", {})
        content_details = channel_data.get("contentDetails", {})

        return {
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "thumbnail_url": snippet.get("thumbnails", {})
            .get("default", {})
            .get("url"),
            "subscriber_count": int(statistics.get("subscriberCount", 0))
            if statistics.get("subscriberCount")
            else None,
            "uploads_playlist_id": content_details.get("relatedPlaylists", {}).get(
                "uploads"
            ),
        }
