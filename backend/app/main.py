import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import api_router
from app.core.scheduler import scheduler
from app.dependencies import get_db
from app.middleware.logging import RequestLoggingMiddleware
from app.services.recommendation_service import RecommendationService
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

    # Load ML model for clothing recommendations
    RecommendationService.load_model()

    # Start background scheduler
    await scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Application shutdown")
    await scheduler.stop()
    logger.info("Background scheduler stopped")


app = FastAPI(
    title="Weather Aggregator API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Check that the application can reach the database."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
