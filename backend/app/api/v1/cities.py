"""Cities API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.dependencies import get_db
from app.schemas.city import CityCreate, CityResponse, CitySearchResult
from app.services.city_service import CityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cities", tags=["cities"])


def _get_city_service(db: AsyncSession = Depends(get_db)) -> CityService:
    return CityService(db, owm_api_key=settings.owm_api_key)


@router.get("/search", response_model=list[CitySearchResult])
async def search_cities(
    q: str = Query(..., min_length=1, description="City name to search for"),
    limit: int = Query(5, ge=1, le=5, description="Maximum number of results"),
    service: CityService = Depends(_get_city_service),
) -> list[CitySearchResult]:
    """Search cities by name using OpenWeatherMap Geocoding API.

    Results are not saved to the database — use POST /cities for that.
    """
    return await service.search(q, limit=limit)


@router.get("/{city_id}", response_model=CityResponse)
async def get_city(
    city_id: int,
    service: CityService = Depends(_get_city_service),
) -> CityResponse:
    """Get a city by its database ID."""
    city = await service.get_by_id(city_id)
    if not city:
        raise HTTPException(status_code=404, detail=f"City {city_id} not found")
    return CityResponse.model_validate(city)


@router.post("", response_model=CityResponse, status_code=201)
async def create_city(
    body: CityCreate,
    service: CityService = Depends(_get_city_service),
) -> CityResponse:
    """Add a city to the database (idempotent: returns existing if (name, country) matches)."""
    city = await service.get_or_create(body)
    return CityResponse.model_validate(city)
