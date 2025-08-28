from unittest.mock import Mock, patch

import pytest

from app.services.youtube_client import YouTubeClient


class TestYouTubeClient:
    @pytest.fixture
    def mock_youtube_service(self):
        with patch("app.services.youtube_client.build") as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def youtube_client(self, mock_youtube_service):
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "test-api-key"}):
            return YouTubeClient()

    def test_init_without_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                ValueError, match="YOUTUBE_API_KEY environment variable is required"
            ):
                YouTubeClient()

    def test_extract_channel_id_direct_channel_id(self, youtube_client):
        channel_id = "UCrAOnWiW_Q1w5UhKjZhOJmA"
        result = youtube_client._extract_channel_id(channel_id)
        assert result == channel_id

    def test_extract_channel_id_channel_url(self, youtube_client):
        url = "https://www.youtube.com/channel/UCrAOnWiW_Q1w5UhKjZhOJmA"
        result = youtube_client._extract_channel_id(url)
        assert result == "UCrAOnWiW_Q1w5UhKjZhOJmA"

    def test_extract_channel_id_channel_url_with_trailing_slash(self, youtube_client):
        url = "https://www.youtube.com/channel/UCrAOnWiW_Q1w5UhKjZhOJmA/"
        result = youtube_client._extract_channel_id(url)
        assert result == "UCrAOnWiW_Q1w5UhKjZhOJmA"

    def test_extract_channel_id_invalid_format(self, youtube_client):
        invalid_inputs = [
            "invalid-channel-id",
            "UC123",  # Too short
            "https://www.youtube.com/@handle",
            "https://www.youtube.com/user/username",
            "https://www.youtube.com/c/customname",
        ]
        for invalid_input in invalid_inputs:
            result = youtube_client._extract_channel_id(invalid_input)
            assert result is None

    def test_resolve_channel_input_direct_channel_id(
        self, youtube_client, mock_youtube_service
    ):
        channel_id = "UCrAOnWiW_Q1w5UhKjZhOJmA"
        mock_response = {
            "items": [
                {
                    "id": channel_id,
                    "snippet": {
                        "title": "Test Channel",
                        "description": "Test Description",
                        "thumbnails": {
                            "default": {"url": "https://example.com/thumb.jpg"}
                        },
                    },
                    "statistics": {"subscriberCount": "1000"},
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "UUrAOnWiW_Q1w5UhKjZhOJmA"}
                    },
                }
            ]
        }

        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_youtube_service.channels.return_value.list.return_value = mock_request

        result_id, metadata = youtube_client.resolve_channel_input(channel_id)

        assert result_id == channel_id
        assert metadata["title"] == "Test Channel"
        assert metadata["description"] == "Test Description"
        assert metadata["subscriber_count"] == 1000
        assert metadata["uploads_playlist_id"] == "UUrAOnWiW_Q1w5UhKjZhOJmA"

    def test_resolve_channel_input_handle(self, youtube_client, mock_youtube_service):
        handle = "@testhandle"
        channel_id = "UCrAOnWiW_Q1w5UhKjZhOJmA"
        mock_response = {
            "items": [
                {
                    "id": channel_id,
                    "snippet": {
                        "title": "Test Channel",
                        "description": "Test Description",
                        "thumbnails": {
                            "default": {"url": "https://example.com/thumb.jpg"}
                        },
                    },
                    "statistics": {"subscriberCount": "1000"},
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "UUrAOnWiW_Q1w5UhKjZhOJmA"}
                    },
                }
            ]
        }

        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_youtube_service.channels.return_value.list.return_value = mock_request

        result_id, metadata = youtube_client.resolve_channel_input(handle)

        mock_youtube_service.channels.return_value.list.assert_called_with(
            part="snippet,statistics", forHandle="testhandle"
        )
        assert result_id == channel_id
        assert metadata["title"] == "Test Channel"

    def test_resolve_channel_input_handle_url(
        self, youtube_client, mock_youtube_service
    ):
        handle_url = "https://www.youtube.com/@testhandle"
        channel_id = "UCrAOnWiW_Q1w5UhKjZhOJmA"
        mock_response = {
            "items": [
                {
                    "id": channel_id,
                    "snippet": {
                        "title": "Test Channel",
                        "description": "Test Description",
                        "thumbnails": {
                            "default": {"url": "https://example.com/thumb.jpg"}
                        },
                    },
                    "statistics": {"subscriberCount": "1000"},
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "UUrAOnWiW_Q1w5UhKjZhOJmA"}
                    },
                }
            ]
        }

        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_youtube_service.channels.return_value.list.return_value = mock_request

        result_id, metadata = youtube_client.resolve_channel_input(handle_url)

        mock_youtube_service.channels.return_value.list.assert_called_with(
            part="snippet,statistics", forHandle="testhandle"
        )
        assert result_id == channel_id

    def test_resolve_channel_input_user_url(self, youtube_client, mock_youtube_service):
        user_url = "https://www.youtube.com/user/testuser"
        channel_id = "UCrAOnWiW_Q1w5UhKjZhOJmA"
        mock_response = {
            "items": [
                {
                    "id": channel_id,
                    "snippet": {
                        "title": "Test Channel",
                        "description": "Test Description",
                        "thumbnails": {
                            "default": {"url": "https://example.com/thumb.jpg"}
                        },
                    },
                    "statistics": {"subscriberCount": "1000"},
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "UUrAOnWiW_Q1w5UhKjZhOJmA"}
                    },
                }
            ]
        }

        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_youtube_service.channels.return_value.list.return_value = mock_request

        result_id, metadata = youtube_client.resolve_channel_input(user_url)

        mock_youtube_service.channels.return_value.list.assert_called_with(
            part="snippet,statistics", forUsername="testuser"
        )
        assert result_id == channel_id

    def test_resolve_channel_input_custom_url(
        self, youtube_client, mock_youtube_service
    ):
        custom_url = "https://www.youtube.com/c/testchannel"
        channel_id = "UCrAOnWiW_Q1w5UhKjZhOJmA"

        search_response = {"items": [{"snippet": {"channelId": channel_id}}]}

        channels_response = {
            "items": [
                {
                    "id": channel_id,
                    "snippet": {
                        "title": "Test Channel",
                        "description": "Test Description",
                        "thumbnails": {
                            "default": {"url": "https://example.com/thumb.jpg"}
                        },
                    },
                    "statistics": {"subscriberCount": "1000"},
                    "contentDetails": {
                        "relatedPlaylists": {"uploads": "UUrAOnWiW_Q1w5UhKjZhOJmA"}
                    },
                }
            ]
        }

        mock_search_request = Mock()
        mock_search_request.execute.return_value = search_response
        mock_youtube_service.search.return_value.list.return_value = mock_search_request

        mock_channels_request = Mock()
        mock_channels_request.execute.return_value = channels_response
        mock_youtube_service.channels.return_value.list.return_value = (
            mock_channels_request
        )

        result_id, metadata = youtube_client.resolve_channel_input(custom_url)

        mock_youtube_service.search.return_value.list.assert_called_with(
            part="snippet", q="testchannel", type="channel", maxResults=1
        )
        assert result_id == channel_id

    def test_resolve_channel_input_not_found(
        self, youtube_client, mock_youtube_service
    ):
        mock_response = {"items": []}
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_youtube_service.channels.return_value.list.return_value = mock_request

        result_id, metadata = youtube_client.resolve_channel_input("@nonexistent")

        assert result_id is None
        assert metadata is None

    def test_extract_metadata_complete(self, youtube_client):
        channel_data = {
            "snippet": {
                "title": "Test Channel",
                "description": "Test Description",
                "thumbnails": {"default": {"url": "https://example.com/thumb.jpg"}},
            },
            "statistics": {"subscriberCount": "1000"},
            "contentDetails": {
                "relatedPlaylists": {"uploads": "UUrAOnWiW_Q1w5UhKjZhOJmA"}
            },
        }

        metadata = youtube_client._extract_metadata(channel_data)

        assert metadata["title"] == "Test Channel"
        assert metadata["description"] == "Test Description"
        assert metadata["thumbnail_url"] == "https://example.com/thumb.jpg"
        assert metadata["subscriber_count"] == 1000
        assert metadata["uploads_playlist_id"] == "UUrAOnWiW_Q1w5UhKjZhOJmA"

    def test_extract_metadata_minimal(self, youtube_client):
        channel_data = {"snippet": {}, "statistics": {}, "contentDetails": {}}

        metadata = youtube_client._extract_metadata(channel_data)

        assert metadata["title"] == ""
        assert metadata["description"] == ""
        assert metadata["thumbnail_url"] is None
        assert metadata["subscriber_count"] is None
        assert metadata["uploads_playlist_id"] is None
