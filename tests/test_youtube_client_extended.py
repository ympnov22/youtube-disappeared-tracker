from unittest.mock import patch

from app.services.youtube_client import YouTubeClient


class TestYouTubeClientExtended:
    def setup_method(self) -> None:
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "test-key"}):
            self.client = YouTubeClient()

    def test_extract_video_metadata_private_video(self) -> None:
        playlist_item = {"contentDetails": {"videoId": "private_video"}}
        video_detail = {
            "id": "private_video",
            "snippet": {"title": "Private Video"},
            "status": {"privacyStatus": "private"},
        }

        result = self.client._extract_video_metadata(playlist_item, video_detail)
        assert result is None

    def test_extract_video_metadata_no_published_date(self) -> None:
        playlist_item = {"contentDetails": {"videoId": "no_date_video"}}
        video_detail = {
            "id": "no_date_video",
            "snippet": {"title": "No Date Video"},
            "status": {"privacyStatus": "public"},
        }

        result = self.client._extract_video_metadata(playlist_item, video_detail)
        assert result is None

    def test_extract_video_metadata_invalid_data(self) -> None:
        playlist_item = {"contentDetails": {"videoId": "invalid_video"}}
        video_detail = {}

        result = self.client._extract_video_metadata(playlist_item, video_detail)
        assert result is None

    def test_extract_video_metadata_malformed_date(self) -> None:
        playlist_item = {"contentDetails": {"videoId": "malformed_date_video"}}
        video_detail = {
            "id": "malformed_date_video",
            "snippet": {
                "title": "Malformed Date Video",
                "publishedAt": "invalid-date-format",
            },
            "status": {"privacyStatus": "public"},
        }

        result = self.client._extract_video_metadata(playlist_item, video_detail)
        assert result is None

    def test_get_video_details_empty_list(self) -> None:
        result = self.client._get_video_details([])
        assert result == {}

    def test_extract_channel_id_url_parsing_exception(self) -> None:
        result = self.client._extract_channel_id("not-a-url://invalid")
        assert result is None

    def test_extract_channel_id_from_various_formats(self) -> None:
        valid_channel_id = "UCtest123456789012345678"

        result = self.client._extract_channel_id(valid_channel_id)
        assert result == valid_channel_id

        result = self.client._extract_channel_id(
            f"https://www.youtube.com/channel/{valid_channel_id}"
        )
        assert result == valid_channel_id

        result = self.client._extract_channel_id(
            "https://www.youtube.com/user/testuser"
        )
        assert result is None

        result = self.client._extract_channel_id("@testhandle")
        assert result is None

    def test_resolve_by_handle_or_username_with_invalid_input(self) -> None:
        result = self.client._resolve_by_handle_or_username("invalid://url")
        assert result == (None, None)

    def test_resolve_by_handle_or_username_with_handle(self) -> None:
        with patch.object(self.client, "_search_by_handle") as mock_search:
            mock_search.return_value = ("UCtest123", {"title": "Test"})

            result = self.client._resolve_by_handle_or_username("@testhandle")
            assert result == ("UCtest123", {"title": "Test"})
            mock_search.assert_called_once_with("testhandle")

    def test_resolve_by_handle_or_username_with_username(self) -> None:
        with patch.object(self.client, "_search_by_username") as mock_search_username:
            mock_search_username.return_value = ("UCtest123", {"title": "Test"})

            result = self.client._resolve_by_handle_or_username(
                "https://www.youtube.com/user/testuser"
            )
            assert result == ("UCtest123", {"title": "Test"})
            mock_search_username.assert_called_once_with("testuser")

    def test_resolve_by_handle_or_username_fallback_to_custom(self) -> None:
        with patch.object(self.client, "_search_by_custom_name") as mock_search_custom:
            mock_search_custom.return_value = ("UCtest123", {"title": "Test"})

            result = self.client._resolve_by_handle_or_username(
                "https://www.youtube.com/c/testchannel"
            )
            assert result == ("UCtest123", {"title": "Test"})
            mock_search_custom.assert_called_once_with("testchannel")

    def test_resolve_channel_input_with_channel_id(self) -> None:
        with patch.object(
            self.client, "_extract_channel_id"
        ) as mock_extract, patch.object(
            self.client, "_get_channel_metadata"
        ) as mock_get_metadata:
            mock_extract.return_value = "UCtest123"
            mock_get_metadata.return_value = ("UCtest123", {"title": "Test"})

            result = self.client.resolve_channel_input("UCtest123")
            assert result == ("UCtest123", {"title": "Test"})
            mock_extract.assert_called_once_with("UCtest123")
            mock_get_metadata.assert_called_once_with("UCtest123")

    def test_resolve_channel_input_fallback_to_handle(self) -> None:
        with patch.object(
            self.client, "_extract_channel_id"
        ) as mock_extract, patch.object(
            self.client, "_resolve_by_handle_or_username"
        ) as mock_resolve:
            mock_extract.return_value = None
            mock_resolve.return_value = ("UCtest123", {"title": "Test"})

            result = self.client.resolve_channel_input("@testhandle")
            assert result == ("UCtest123", {"title": "Test"})
            mock_extract.assert_called_once_with("@testhandle")
            mock_resolve.assert_called_once_with("@testhandle")

    def test_extract_video_metadata_success(self) -> None:
        playlist_item = {"contentDetails": {"videoId": "test_video"}}
        video_detail = {
            "id": "test_video",
            "snippet": {
                "title": "Test Video",
                "description": "Test Description",
                "publishedAt": "2023-01-01T00:00:00Z",
                "thumbnails": {"default": {"url": "http://example.com/thumb.jpg"}},
            },
            "status": {"privacyStatus": "public"},
            "contentDetails": {"duration": "PT5M30S"},
            "statistics": {"viewCount": "1000"},
        }

        result = self.client._extract_video_metadata(playlist_item, video_detail)
        assert result is not None
        assert result["video_id"] == "test_video"
        assert result["title"] == "Test Video"
        assert result["description"] == "Test Description"

    def test_extract_video_metadata_missing_snippet(self) -> None:
        playlist_item = {"contentDetails": {"videoId": "test_video"}}
        video_detail = {"id": "test_video", "status": {"privacyStatus": "public"}}

        result = self.client._extract_video_metadata(playlist_item, video_detail)
        assert result is None

    def test_extract_video_metadata_missing_status(self) -> None:
        playlist_item = {"contentDetails": {"videoId": "test_video"}}
        video_detail = {
            "id": "test_video",
            "snippet": {"title": "Test Video", "publishedAt": "2023-01-01T00:00:00Z"},
        }

        result = self.client._extract_video_metadata(playlist_item, video_detail)
        assert result is not None
        assert result["video_id"] == "test_video"
