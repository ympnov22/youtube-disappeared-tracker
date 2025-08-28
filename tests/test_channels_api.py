from typing import Callable, Generator
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


def create_test_db_dependency(
    engine: Engine,
) -> Callable[[], Generator[Session, None, None]]:
    """Create a test database session factory for dependency injection."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_test_db() -> Generator[Session, None, None]:
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    return get_test_db


class TestChannelsAPI:
    def setup_method(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        Base.metadata.create_all(bind=self.engine)

        test_app = FastAPI()
        test_app.include_router(app.router)
        test_app.dependency_overrides[get_db] = create_test_db_dependency(self.engine)
        self.client = TestClient(test_app)

    def teardown_method(self) -> None:
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    @patch("app.api.channels.YouTubeClient")
    def test_add_channel_success(self, mock_youtube_client_class: Mock) -> None:
        mock_client = Mock()
        mock_youtube_client_class.return_value = mock_client
        mock_client.resolve_channel_input.return_value = (
            "UCrAOnWiW_Q1w5UhKjZhOJmA",
            {
                "title": "Test Channel",
                "description": "Test Description",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "subscriber_count": 1000,
                "uploads_playlist_id": "UUrAOnWiW_Q1w5UhKjZhOJmA",
            },
        )

        response = self.client.post("/api/channels/", json={"input": "@testchannel"})

        assert response.status_code == 201
        data = response.json()
        assert data["channel_id"] == "UCrAOnWiW_Q1w5UhKjZhOJmA"
        assert data["title"] == "Test Channel"
        assert data["source_input"] == "@testchannel"
        assert data["is_active"] is True

    @patch("app.api.channels.YouTubeClient")
    def test_add_channel_not_found(self, mock_youtube_client_class: Mock) -> None:
        mock_client = Mock()
        mock_youtube_client_class.return_value = mock_client
        mock_client.resolve_channel_input.return_value = (None, None)

        response = self.client.post("/api/channels/", json={"input": "@nonexistent"})

        assert response.status_code == 404
        assert "Channel not found" in response.json()["detail"]

    @patch("app.api.channels.YouTubeClient")
    def test_add_channel_duplicate(self, mock_youtube_client_class: Mock) -> None:
        mock_client = Mock()
        mock_youtube_client_class.return_value = mock_client
        mock_client.resolve_channel_input.return_value = (
            "UCrAOnWiW_Q1w5UhKjZhOJmA",
            {
                "title": "Test Channel",
                "description": "Test Description",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "subscriber_count": 1000,
                "uploads_playlist_id": "UUrAOnWiW_Q1w5UhKjZhOJmA",
            },
        )

        response1 = self.client.post("/api/channels/", json={"input": "@testchannel"})
        assert response1.status_code == 201

        response2 = self.client.post(
            "/api/channels/",
            json={"input": "https://www.youtube.com/channel/UCrAOnWiW_Q1w5UhKjZhOJmA"},
        )
        assert response2.status_code == 409
        assert "already registered" in response2.json()["detail"]

    @patch("app.api.channels.YouTubeClient")
    def test_add_channel_limit_exceeded(self, mock_youtube_client_class: Mock) -> None:
        mock_client = Mock()
        mock_youtube_client_class.return_value = mock_client

        for i in range(10):
            mock_client.resolve_channel_input.return_value = (
                f"UCrAOnWiW_Q1w5UhKjZhOJm{i:01d}",
                {
                    "title": f"Test Channel {i}",
                    "description": f"Test Description {i}",
                    "thumbnail_url": f"https://example.com/thumb{i}.jpg",
                    "subscriber_count": 1000 + i,
                    "uploads_playlist_id": f"UUrAOnWiW_Q1w5UhKjZhOJm{i:01d}",
                },
            )
            response = self.client.post(
                "/api/channels/", json={"input": f"@testchannel{i}"}
            )
            assert response.status_code == 201

        mock_client.resolve_channel_input.return_value = (
            "UCrAOnWiW_Q1w5UhKjZhOJmX",
            {
                "title": "Test Channel X",
                "description": "Test Description X",
                "thumbnail_url": "https://example.com/thumbX.jpg",
                "subscriber_count": 2000,
                "uploads_playlist_id": "UUrAOnWiW_Q1w5UhKjZhOJmX",
            },
        )
        response = self.client.post("/api/channels/", json={"input": "@testchannelX"})
        assert response.status_code == 400
        assert "Maximum of 10 channels allowed" in response.json()["detail"]

    @patch("app.api.channels.YouTubeClient")
    def test_list_channels_empty(self, mock_youtube_client_class: Mock) -> None:
        response = self.client.get("/api/channels/")
        assert response.status_code == 200
        assert response.json() == []

    @patch("app.api.channels.YouTubeClient")
    def test_list_channels_with_data(self, mock_youtube_client_class: Mock) -> None:
        mock_client = Mock()
        mock_youtube_client_class.return_value = mock_client
        mock_client.resolve_channel_input.return_value = (
            "UCrAOnWiW_Q1w5UhKjZhOJmA",
            {
                "title": "Test Channel",
                "description": "Test Description",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "subscriber_count": 1000,
                "uploads_playlist_id": "UUrAOnWiW_Q1w5UhKjZhOJmA",
            },
        )

        add_response = self.client.post(
            "/api/channels/", json={"input": "@testchannel"}
        )
        assert add_response.status_code == 201

        list_response = self.client.get("/api/channels/")
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data) == 1
        assert data[0]["channel_id"] == "UCrAOnWiW_Q1w5UhKjZhOJmA"
        assert data[0]["title"] == "Test Channel"

    @patch("app.api.channels.YouTubeClient")
    def test_remove_channel_success(self, mock_youtube_client_class: Mock) -> None:
        mock_client = Mock()
        mock_youtube_client_class.return_value = mock_client
        mock_client.resolve_channel_input.return_value = (
            "UCrAOnWiW_Q1w5UhKjZhOJmA",
            {
                "title": "Test Channel",
                "description": "Test Description",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "subscriber_count": 1000,
                "uploads_playlist_id": "UUrAOnWiW_Q1w5UhKjZhOJmA",
            },
        )

        add_response = self.client.post(
            "/api/channels/", json={"input": "@testchannel"}
        )
        assert add_response.status_code == 201

        remove_response = self.client.delete("/api/channels/UCrAOnWiW_Q1w5UhKjZhOJmA")
        assert remove_response.status_code == 204

        list_response = self.client.get("/api/channels/")
        assert list_response.status_code == 200
        assert list_response.json() == []

    def test_remove_channel_not_found(self) -> None:
        response = self.client.delete("/api/channels/UCrAOnWiW_Q1w5UhKjZhOJmA")
        assert response.status_code == 404
        assert "Channel not found" in response.json()["detail"]

    @patch("app.api.channels.YouTubeClient")
    def test_remove_channel_already_removed(
        self, mock_youtube_client_class: Mock
    ) -> None:
        mock_client = Mock()
        mock_youtube_client_class.return_value = mock_client
        mock_client.resolve_channel_input.return_value = (
            "UCrAOnWiW_Q1w5UhKjZhOJmA",
            {
                "title": "Test Channel",
                "description": "Test Description",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "subscriber_count": 1000,
                "uploads_playlist_id": "UUrAOnWiW_Q1w5UhKjZhOJmA",
            },
        )

        add_response = self.client.post(
            "/api/channels/", json={"input": "@testchannel"}
        )
        assert add_response.status_code == 201

        remove_response1 = self.client.delete("/api/channels/UCrAOnWiW_Q1w5UhKjZhOJmA")
        assert remove_response1.status_code == 204

        remove_response2 = self.client.delete("/api/channels/UCrAOnWiW_Q1w5UhKjZhOJmA")
        assert remove_response2.status_code == 404
        assert "Channel not found" in remove_response2.json()["detail"]

    @patch("app.api.channels.YouTubeClient")
    def test_youtube_api_configuration_error(
        self, mock_youtube_client_class: Mock
    ) -> None:
        mock_youtube_client_class.side_effect = ValueError(
            "YOUTUBE_API_KEY environment variable is required"
        )

        response = self.client.post("/api/channels/", json={"input": "@testchannel"})
        assert response.status_code == 500
        assert "YouTube API configuration error" in response.json()["detail"]
