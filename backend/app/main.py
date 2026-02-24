import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.scheduler import scheduler
from app.services.source_manager import source_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Application startup")

    # Load source configurations
    source_manager.load()
    logger.info("Source configs loaded: %d sources", len(source_manager.get_all()))

    # Start background scheduler
    await scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Application shutdown")
    await scheduler.stop()
    logger.info("Background scheduler stopped")


app = FastAPI(title="Weather Aggregator API", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
