"""Admin API endpoints (require X-Admin-API-Key header)."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin
from app.dependencies import get_db
from app.models.city import City
from app.models.source import WeatherSource
from app.schemas.admin import (
    AdminAuthResponse,
    FetchNowResponse,
    LogsResponse,
    SourceUpdateRequest,
    StatsRow,
)
from app.schemas.admin import LogEntryResponse
from app.schemas.source import SourceResponse
from app.services.stats_service import StatsService
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.post("/auth", response_model=AdminAuthResponse)
async def admin_auth() -> AdminAuthResponse:
    """Validate the admin API key. Returns 200 if key is correct, 401 otherwise."""
    return AdminAuthResponse(authenticated=True)


@router.get("/stats", response_model=list[StatsRow])
async def get_stats(
    from_date: str | None = Query(None, description="Start date YYYY-MM-DD"),
    to_date: str | None = Query(None, description="End date YYYY-MM-DD"),
    platform: str | None = Query(None, description="Filter by platform"),
    db: AsyncSession = Depends(get_db),
) -> list[StatsRow]:
    """Get daily usage statistics with optional filters."""
    from datetime import date as date_type

    from_date_parsed = date_type.fromisoformat(from_date) if from_date else None
    to_date_parsed = date_type.fromisoformat(to_date) if to_date else None

    service = StatsService(db)
    stats = await service.get_stats(from_date_parsed, to_date_parsed, platform)
    return [StatsRow.model_validate(s) for s in stats]


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    platform: str | None = Query(None),
    action: str | None = Query(None, description="Partial match on action field"),
    db: AsyncSession = Depends(get_db),
) -> LogsResponse:
    """Get paginated request logs with optional filters."""
    service = StatsService(db)
    total, logs = await service.get_logs(limit, offset, platform, action)
    return LogsResponse(
        total=total,
        offset=offset,
        limit=limit,
        items=[LogEntryResponse.model_validate(log) for log in logs],
    )


@router.get("/sources", response_model=list[SourceResponse])
async def admin_list_sources(
    db: AsyncSession = Depends(get_db),
) -> list[SourceResponse]:
    """List all weather sources including disabled ones."""
    result = await db.execute(
        select(WeatherSource).order_by(WeatherSource.priority.desc())
    )
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.patch("/sources/{slug}", response_model=SourceResponse)
async def update_source(
    slug: str,
    body: SourceUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Toggle enabled state or update priority of a weather source."""
    result = await db.execute(
        select(WeatherSource).where(WeatherSource.slug == slug)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{slug}' not found")

    if body.is_enabled is not None:
        source.is_enabled = body.is_enabled
    if body.priority is not None:
        source.priority = body.priority

    await db.commit()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.post("/fetch-now", response_model=FetchNowResponse)
async def fetch_now(
    city_id: int | None = Query(None, description="Fetch for specific city; all cities if omitted"),
    db: AsyncSession = Depends(get_db),
) -> FetchNowResponse:
    """Trigger an immediate weather data fetch (background task)."""
    service = WeatherService(db)

    if city_id is not None:
        asyncio.create_task(service.fetch_and_save(city_id))
        return FetchNowResponse(triggered=True, cities_count=1)

    result = await db.execute(select(City))
    cities = result.scalars().all()

    for city in cities:
        asyncio.create_task(service.fetch_and_save(city.id))

    logger.info("fetch-now triggered for %d cities", len(cities))
    return FetchNowResponse(triggered=True, cities_count=len(cities))
