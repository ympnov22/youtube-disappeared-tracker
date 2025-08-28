from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.channels import router as channels_router
from app.api.videos import router as videos_router
from app.services.background_jobs import background_job_service

app = FastAPI(
    title="YouTube Disappeared Video Tracker",
    description="Track YouTube channel uploads and detect disappeared videos",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels_router, prefix="/api")
app.include_router(videos_router, prefix="/api")


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


@app.on_event("startup")
async def startup_event() -> None:
    """Start background services on application startup."""
    background_job_service.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Stop background services on application shutdown."""
    background_job_service.stop()
