import os
import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

security = HTTPBasic()
limiter = Limiter(key_func=get_remote_address)


def get_admin_credentials() -> tuple[str, str]:
    """Get admin credentials from environment variables."""
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin credentials not configured",
        )

    return username, password


def verify_admin_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
) -> str:
    """Verify admin credentials with rate limiting for failed attempts."""
    try:
        admin_username, admin_password = get_admin_credentials()
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured",
        )

    is_correct_username = secrets.compare_digest(credentials.username, admin_username)
    is_correct_password = secrets.compare_digest(credentials.password, admin_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(request: Request, token: str) -> bool:
    """Verify CSRF token from session."""
    session_token = request.session.get("csrf_token")
    if not session_token:
        return False
    return secrets.compare_digest(session_token, token)


def require_https(request: Request) -> None:
    """Require HTTPS in production (Fly.io terminates TLS)."""
    if request.headers.get("x-forwarded-proto") == "http":
        raise HTTPException(
            status_code=status.HTTP_426_UPGRADE_REQUIRED, detail="HTTPS required"
        )
