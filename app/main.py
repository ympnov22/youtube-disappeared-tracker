import os
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware

from app.api.channels import router as channels_router
from app.api.videos import router as videos_router
from app.services.background_jobs import background_job_service
from app.web.routes import router as web_router

app = FastAPI(
    title="YouTube Disappeared Video Tracker",
    description="Track YouTube channel uploads and detect disappeared videos",
    version="0.1.0",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

session_secret = os.getenv("SESSION_SECRET", "dev-secret-key-change-in-production")
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    max_age=3600,  # 1 hour
    same_site="strict",
    https_only=os.getenv("APP_ENV") == "production",  # HTTPS only in production
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

app.include_router(channels_router, prefix="/api")
app.include_router(videos_router, prefix="/api")

app.include_router(web_router)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "YouTube Disappeared Video Tracker API"}


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "youtube-tracker",
    }


@app.get("/healthz")
async def health_check_detailed() -> Dict:
    """Detailed health check including scheduler status."""
    scheduler_status = background_job_service.get_status()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "youtube-tracker",
        "scheduler": scheduler_status,
    }


@app.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """Readiness check endpoint for deployment verification."""
    return {
        "status": "ready",
        "version": "0.1.0",
        "service": "youtube-tracker",
    }


@app.on_event("startup")
async def startup_event() -> None:
    """Start background services on application startup."""
    background_job_service.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Stop background services on application shutdown."""
    background_job_service.stop()
