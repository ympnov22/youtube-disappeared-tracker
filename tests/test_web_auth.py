import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPBasicCredentials

from app.web.auth import (
    generate_csrf_token,
    get_admin_credentials,
    require_https,
    verify_admin_credentials,
    verify_csrf_token,
)


class TestWebAuth:
    def test_get_admin_credentials_success(self):
        with patch.dict(
            os.environ, {"ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": "secret"}
        ):
            username, password = get_admin_credentials()
            assert username == "admin"
            assert password == "secret"

    def test_get_admin_credentials_missing_username(self):
        with patch.dict(os.environ, {"ADMIN_PASSWORD": "secret"}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                get_admin_credentials()
            assert exc_info.value.status_code == 500

    def test_get_admin_credentials_missing_password(self):
        with patch.dict(os.environ, {"ADMIN_USERNAME": "admin"}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                get_admin_credentials()
            assert exc_info.value.status_code == 500

    def test_get_admin_credentials_both_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                get_admin_credentials()
            assert exc_info.value.status_code == 500

    def test_verify_admin_credentials_success(self):
        credentials = HTTPBasicCredentials(username="admin", password="secret")

        with patch.dict(
            os.environ, {"ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": "secret"}
        ):
            result = verify_admin_credentials(credentials)
            assert result == "admin"

    def test_verify_admin_credentials_wrong_username(self):
        credentials = HTTPBasicCredentials(username="wrong", password="secret")

        with patch.dict(
            os.environ, {"ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": "secret"}
        ):
            with pytest.raises(HTTPException) as exc_info:
                verify_admin_credentials(credentials)
            assert exc_info.value.status_code == 401
            assert "WWW-Authenticate" in exc_info.value.headers

    def test_verify_admin_credentials_wrong_password(self):
        credentials = HTTPBasicCredentials(username="admin", password="wrong")

        with patch.dict(
            os.environ, {"ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": "secret"}
        ):
            with pytest.raises(HTTPException) as exc_info:
                verify_admin_credentials(credentials)
            assert exc_info.value.status_code == 401
            assert "WWW-Authenticate" in exc_info.value.headers

    def test_verify_admin_credentials_env_not_configured(self):
        credentials = HTTPBasicCredentials(username="admin", password="secret")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                verify_admin_credentials(credentials)
            assert exc_info.value.status_code == 500

    def test_generate_csrf_token(self):
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()

        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2  # Should be unique

    def test_verify_csrf_token_success(self):
        token = "test_token_123"

        scope = {"type": "http", "method": "POST", "session": {"csrf_token": token}}
        request = Request(scope=scope)

        result = verify_csrf_token(request, token)
        assert result is True

    def test_verify_csrf_token_no_session_token(self):
        token = "test_token_123"

        scope = {"type": "http", "method": "POST", "session": {}}
        request = Request(scope=scope)

        result = verify_csrf_token(request, token)
        assert result is False

    def test_verify_csrf_token_wrong_token(self):
        session_token = "session_token_123"
        provided_token = "wrong_token_456"

        scope = {
            "type": "http",
            "method": "POST",
            "session": {"csrf_token": session_token},
        }
        request = Request(scope=scope)

        result = verify_csrf_token(request, provided_token)
        assert result is False

    def test_require_https_with_http(self):
        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "headers": [(b"x-forwarded-proto", b"http")],
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            require_https(request)
        assert exc_info.value.status_code == 426

    def test_require_https_with_https(self):
        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "headers": [(b"x-forwarded-proto", b"https")],
            }
        )

        require_https(request)

    def test_require_https_no_header(self):
        request = Request(scope={"type": "http", "method": "GET", "headers": []})

        require_https(request)

    def test_csrf_token_timing_safe_comparison(self):
        """Test that CSRF token verification uses timing-safe comparison."""
        token = "test_token_123"

        scope = {"type": "http", "method": "POST", "session": {"csrf_token": token}}
        request = Request(scope=scope)

        assert verify_csrf_token(request, token) is True

        wrong_token = "test_token_456"  # Same length, different content
        assert verify_csrf_token(request, wrong_token) is False

        short_token = "short"
        assert verify_csrf_token(request, short_token) is False

    def test_admin_credentials_timing_safe_comparison(self):
        """Test that admin credential verification uses timing-safe comparison."""
        with patch.dict(
            os.environ, {"ADMIN_USERNAME": "admin", "ADMIN_PASSWORD": "secret"}
        ):
            correct_creds = HTTPBasicCredentials(username="admin", password="secret")
            result = verify_admin_credentials(correct_creds)
            assert result == "admin"

            wrong_user_creds = HTTPBasicCredentials(username="wrong", password="secret")
            with pytest.raises(HTTPException):
                verify_admin_credentials(wrong_user_creds)

            wrong_pass_creds = HTTPBasicCredentials(username="admin", password="wrongp")
            with pytest.raises(HTTPException):
                verify_admin_credentials(wrong_pass_creds)
