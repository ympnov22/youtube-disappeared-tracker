import logging
import os
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.channel import Channel

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import apscheduler.schedulers.background  # type: ignore[import-untyped] # noqa

    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

logger = logging.getLogger(__name__)


class BackgroundJobService:
    def __init__(self) -> None:
        self.scheduler: Optional[Any] = None
        self.redis_client: Optional[Any] = None
        self.enabled = os.getenv("SCAN_ENABLED", "false").lower() == "true"
        self.scan_interval_minutes = int(os.getenv("SCAN_INTERVAL_MINUTES", "60"))
        self.scan_concurrency = int(os.getenv("SCAN_CONCURRENCY", "1"))
        self.scan_batch_size = int(os.getenv("SCAN_BATCH_SIZE", "10"))

        if self.enabled:
            if REDIS_AVAILABLE and SCHEDULER_AVAILABLE:
                self._setup_redis()
                self._setup_scheduler()
            else:
                logger.warning("Background jobs enabled but dependencies not available")
                self.enabled = False

    def _setup_redis(self) -> None:
        """Setup Redis connection for distributed locking."""
        if not REDIS_AVAILABLE:
            return

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url)
            if self.redis_client is not None:
                self.redis_client.ping()
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False

    def _setup_scheduler(self) -> None:
        """Setup APScheduler for background jobs."""
        if not self.enabled or not SCHEDULER_AVAILABLE:
            return

        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import (  # type: ignore[import-untyped]
            IntervalTrigger,
        )

        self.scheduler = BackgroundScheduler()
        if self.scheduler is not None:
            self.scheduler.add_job(
                func=self._scan_all_channels,
                trigger=IntervalTrigger(minutes=self.scan_interval_minutes),
                id="scan_channels",
                name="Scan all channels for video updates",
                replace_existing=True,
            )

    def start(self) -> None:
        """Start the background job scheduler."""
        if self.enabled and self.scheduler:
            self.scheduler.start()
            logger.info("Background job scheduler started")

    def stop(self) -> None:
        """Stop the background job scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Background job scheduler stopped")

    def get_status(self) -> dict:
        """Get scheduler status for health checks."""
        if not self.enabled:
            return {"enabled": False, "next_run": None}

        next_run = None
        if self.scheduler:
            job = self.scheduler.get_job("scan_channels")
            if job and job.next_run_time:
                next_run = job.next_run_time.isoformat()

        return {
            "enabled": True,
            "running": self.scheduler.running if self.scheduler else False,
            "next_run": next_run,
        }

    def _acquire_lock(self, channel_id: str, timeout: int = 300) -> bool:
        """Acquire a distributed lock for channel scanning."""
        if not self.redis_client:
            return True

        lock_key = f"scan_lock:{channel_id}"
        result = self.redis_client.set(lock_key, "1", nx=True, ex=timeout)
        return bool(result)

    def _release_lock(self, channel_id: str) -> None:
        """Release the distributed lock for channel scanning."""
        if not self.redis_client:
            return

        lock_key = f"scan_lock:{channel_id}"
        self.redis_client.delete(lock_key)

    def _scan_all_channels(self) -> None:
        """Scan all active channels for video updates."""
        logger.info("Starting scheduled channel scan")

        db = SessionLocal()
        try:
            channels = (
                db.query(Channel)
                .filter(Channel.is_active.is_(True))
                .limit(self.scan_batch_size)
                .all()
            )

            for channel in channels:
                if self._acquire_lock(str(channel.channel_id)):
                    try:
                        self._scan_single_channel(db, str(channel.channel_id))
                    except Exception as e:
                        logger.error(
                            f"Failed to scan channel {channel.channel_id}: {e}"
                        )
                    finally:
                        self._release_lock(str(channel.channel_id))
                else:
                    logger.info(
                        f"Channel {channel.channel_id} is already being scanned"
                    )

        finally:
            db.close()

        logger.info("Completed scheduled channel scan")

    def _scan_single_channel(self, db: Session, channel_id: str) -> None:
        """Scan a single channel for video updates."""
        try:
            from app.services.video_ingestion import VideoIngestionService
            from app.services.youtube_client import YouTubeClient

            youtube_client = YouTubeClient()
            ingestion_service = VideoIngestionService(db, youtube_client)
            added, updated, events = ingestion_service.scan_channel(channel_id)
            logger.info(
                f"Scanned channel {channel_id}: "
                f"added={added}, updated={updated}, events={events}"
            )
        except Exception as e:
            logger.error(f"Error scanning channel {channel_id}: {e}")
            raise


background_job_service = BackgroundJobService()
