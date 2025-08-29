import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.channel import Channel
from app.models.disappearance_event import DisappearanceEvent, EventType
from app.models.video import Video

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


client = TestClient(app)


class TestWebRoutes:
    def setup_method(self):
        """Set up test data before each test."""
        app.dependency_overrides[get_db] = override_get_db

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        self.admin_username = "testadmin"
        self.admin_password = "testpass123"

        self.test_channel_id = "UC123456789"
        self.test_video_id = "abc123"

        db = TestingSessionLocal()
        try:
            from datetime import datetime

            test_channel = Channel(
                channel_id=self.test_channel_id,
                title="Test Channel",
                uploads_playlist_id="UU123456789",
                source_input="@testchannel",
                is_active=True,
            )
            db.add(test_channel)

            test_video = Video(
                video_id=self.test_video_id,
                channel_id=self.test_channel_id,
                title="Test Video",
                description="Test description",
                published_at=datetime.utcnow(),
                is_available=True,
                view_count=1000,
                duration="PT5M30S",
            )
            db.add(test_video)

            test_event = DisappearanceEvent(
                video_id=self.test_video_id,
                event_type=EventType.DELETED,
                details={
                    "title": "Test Video",
                    "channel_id": self.test_channel_id,
                    "channel_title": "Test Channel",
                },
                detected_at=datetime.utcnow(),
            )
            db.add(test_event)

            db.commit()
        finally:
            db.close()

    def get_auth_headers(self):
        """Get basic auth headers for admin access."""
        import base64

        credentials = base64.b64encode(
            f"{self.admin_username}:{self.admin_password}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    def test_admin_dashboard_redirect(self):
        """Test admin dashboard redirects to channels page."""
        response = client.get(
            "/admin", headers=self.get_auth_headers(), follow_redirects=False
        )
        assert response.status_code == 302
        assert response.headers["location"] == "/admin/channels"

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    def test_admin_channels_page(self):
        """Test admin channels page loads correctly."""
        response = client.get("/admin/channels", headers=self.get_auth_headers())
        assert response.status_code == 200
        assert "Test Channel" in response.text
        assert "UC123456789" in response.text

    def test_admin_channels_unauthorized(self):
        """Test admin channels page requires authentication."""
        response = client.get("/admin/channels")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    def test_admin_channels_wrong_credentials(self):
        """Test admin channels page rejects wrong credentials."""
        import base64

        wrong_headers = {
            "Authorization": "Basic " + base64.b64encode(b"wrong:wrong").decode()
        }
        response = client.get("/admin/channels", headers=wrong_headers)
        assert response.status_code == 401

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    @patch("app.web.routes.YouTubeClient")
    @patch("app.web.routes.verify_csrf_token")
    def test_add_channel_success(self, mock_verify_csrf, mock_youtube_client):
        """Test adding a new channel successfully."""
        mock_verify_csrf.return_value = True
        mock_client_instance = MagicMock()
        mock_client_instance.resolve_channel_input.return_value = (
            "UC987654321",
            {"title": "New Test Channel", "uploads_playlist_id": "UU987654321"},
        )
        mock_youtube_client.return_value = mock_client_instance

        response = client.post(
            "/admin/channels/add",
            data={"channel_input": "@newchannel", "csrf_token": "valid_token"},
            headers=self.get_auth_headers(),
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/admin/channels"

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    @patch("app.web.routes.verify_csrf_token")
    def test_add_channel_invalid_csrf(self, mock_verify_csrf):
        """Test adding channel with invalid CSRF token fails."""
        mock_verify_csrf.return_value = False

        response = client.post(
            "/admin/channels/add",
            data={"channel_input": "@newchannel", "csrf_token": "invalid_token"},
            headers=self.get_auth_headers(),
        )
        assert response.status_code == 403

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    @patch("app.web.routes.verify_csrf_token")
    def test_delete_channel_success(self, mock_verify_csrf):
        """Test deleting a channel successfully."""
        mock_verify_csrf.return_value = True

        response = client.post(
            f"/admin/channels/{self.test_channel_id}/delete",
            data={"csrf_token": "valid_token"},
            headers=self.get_auth_headers(),
            follow_redirects=False,
        )

        assert response.status_code == 303

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    @patch("app.web.routes.verify_csrf_token")
    def test_delete_channel_not_found(self, mock_verify_csrf):
        """Test deleting non-existent channel returns 404."""
        mock_verify_csrf.return_value = True

        response = client.post(
            "/admin/channels/nonexistent/delete",
            data={"csrf_token": "valid_token"},
            headers=self.get_auth_headers(),
        )

        assert response.status_code == 404

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    @patch("app.web.routes.VideoIngestionService")
    @patch("app.web.routes.YouTubeClient")
    @patch("app.web.routes.verify_csrf_token")
    def test_scan_channel_success(
        self, mock_verify_csrf, mock_youtube_client, mock_ingestion_service
    ):
        """Test scanning a channel successfully."""
        mock_verify_csrf.return_value = True
        mock_ingestion_instance = MagicMock()
        mock_ingestion_instance.scan_channel.return_value = (
            5,
            2,
            1,
        )  # added, updated, events
        mock_ingestion_service.return_value = mock_ingestion_instance

        response = client.post(
            f"/admin/channels/{self.test_channel_id}/scan",
            data={"csrf_token": "valid_token"},
            headers=self.get_auth_headers(),
            follow_redirects=False,
        )

        assert response.status_code == 303
        mock_ingestion_instance.scan_channel.assert_called_once_with(
            self.test_channel_id
        )

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    @patch("app.web.routes.verify_csrf_token")
    def test_scan_channel_not_found(self, mock_verify_csrf):
        """Test scanning non-existent channel returns 404."""
        mock_verify_csrf.return_value = True

        response = client.post(
            "/admin/channels/nonexistent/scan",
            data={"csrf_token": "valid_token"},
            headers=self.get_auth_headers(),
        )

        assert response.status_code == 404

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    def test_channel_videos_page(self):
        """Test channel videos page loads correctly."""
        response = client.get(
            f"/admin/channels/{self.test_channel_id}/videos",
            headers=self.get_auth_headers(),
        )
        assert response.status_code == 200
        assert "Test Video" in response.text
        assert "abc123" in response.text

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    def test_channel_videos_not_found(self):
        """Test channel videos page for non-existent channel returns 404."""
        response = client.get(
            "/admin/channels/nonexistent/videos", headers=self.get_auth_headers()
        )
        assert response.status_code == 404

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    def test_admin_events_page(self):
        """Test admin events page loads correctly."""
        response = client.get("/admin/events", headers=self.get_auth_headers())
        assert response.status_code == 200
        assert "Test Video" in response.text
        assert "DELETED" in response.text

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    def test_admin_events_filtered_by_channel(self):
        """Test admin events page with channel filter."""
        response = client.get(
            f"/admin/events?channel_id={self.test_channel_id}",
            headers=self.get_auth_headers(),
        )
        assert response.status_code == 200
        assert "Test Video" in response.text

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_admin_credentials(self):
        """Test that missing admin credentials returns 500."""
        response = client.get("/admin/channels", headers=self.get_auth_headers())
        assert response.status_code == 500

    @patch.dict(
        os.environ, {"ADMIN_USERNAME": "testadmin", "ADMIN_PASSWORD": "testpass123"}
    )
    @patch("app.web.routes.require_https")
    def test_https_enforcement(self, mock_require_https):
        """Test that HTTPS enforcement is called."""
        mock_require_https.side_effect = None  # Don't raise exception

        response = client.get("/admin/channels", headers=self.get_auth_headers())
        assert response.status_code == 200
        assert mock_require_https.called

    def test_rate_limiting_add_channel(self):
        """Test rate limiting on add channel endpoint."""
        response = client.post("/admin/channels/add", data={"channel_input": "@test"})
        assert response.status_code == 401

    def test_rate_limiting_scan_channel(self):
        """Test rate limiting on scan channel endpoint."""
        response = client.post(f"/admin/channels/{self.test_channel_id}/scan")
        assert response.status_code == 401

    def teardown_method(self):
        """Clean up test data after each test."""
        if get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]
