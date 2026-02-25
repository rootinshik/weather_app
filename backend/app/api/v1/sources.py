"""Weather sources API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.source import WeatherSource
from app.schemas.source import SourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db),
) -> list[SourceResponse]:
    """List all weather data sources ordered by priority."""
    result = await db.execute(
        select(WeatherSource).order_by(WeatherSource.priority.desc())
    )
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.get("/{slug}", response_model=SourceResponse)
async def get_source(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> SourceResponse:
    """Get a single weather source by its slug."""
    result = await db.execute(
        select(WeatherSource).where(WeatherSource.slug == slug)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{slug}' not found")
    return SourceResponse.model_validate(source)
