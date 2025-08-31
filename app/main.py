import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

from app.api.channels import router as channels_router
from app.api.videos import router as videos_router
from app.core.database import Base, SessionLocal, engine
from app.models import Channel, DisappearanceEvent, Video  # noqa: F401
from app.services.background_jobs import background_job_service
from app.web.routes import router as web_router

app = FastAPI(
    title="YouTube Disappeared Video Tracker",
    description="Track YouTube channel uploads and detect disappeared videos",
    version="0.1.0",
)

templates = Jinja2Templates(directory="app/web/templates")

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
app.include_router(videos_router)
app.include_router(web_router)


@app.get("/")
async def root(request: Request) -> Any:
    return templates.TemplateResponse("public_index.html", {"request": request})


@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "youtube-tracker",
    }


@app.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """Readiness check including database connectivity."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "version": "0.1.0",
            "service": "youtube-tracker",
        }
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not ready",
                "error": "Database connection failed",
                "message": str(e),
            },
        )


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


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database schema and start background services."""
    Base.metadata.create_all(bind=engine)
    background_job_service.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Stop background services on application shutdown."""
    background_job_service.stop()
