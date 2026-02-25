"""Weather API endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.weather import (
    AggregatedWeather,
    AggregatedWeatherResponse,
    ChartPoint,
    DailyChartPoint,
    ForecastPoint,
    ForecastResponse,
    SourceWeatherData,
    SourceWeatherResponse,
)
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/current", response_model=AggregatedWeatherResponse)
async def get_current_weather(
    city_id: int = Query(..., description="City ID", gt=0),
    sources: list[str] | None = Query(None, description="Source slugs to filter by"),
    db: AsyncSession = Depends(get_db),
) -> AggregatedWeatherResponse:
    """Get aggregated current weather for a city.

    Triggers on-demand fetch if data is older than 30 minutes.
    """
    service = WeatherService(db)
    result = await service.get_aggregated_current(city_id, source_slugs=sources)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No weather data available for city_id={city_id}",
        )

    return AggregatedWeatherResponse(
        city_id=city_id,
        fetched_at=datetime.now(timezone.utc),
        weather=result,
    )


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    city_id: int = Query(..., description="City ID", gt=0),
    days: int = Query(5, description="Number of forecast days", ge=3, le=7),
    sources: list[str] | None = Query(None, description="Source slugs to filter by"),
    db: AsyncSession = Depends(get_db),
) -> ForecastResponse:
    """Get weather forecast for a city.

    Returns aggregated forecast data grouped by datetime.
    """
    service = WeatherService(db)
    result = await service.get_aggregated_forecast(city_id, days=days, source_slugs=sources)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No forecast data available for city_id={city_id}",
        )

    forecasts = [
        ForecastPoint(
            forecast_dt=item["forecast_dt"],
            weather=AggregatedWeather(**item["data"]),
        )
        for item in result
    ]

    return ForecastResponse(city_id=city_id, days=days, forecasts=forecasts)


@router.get("/current/by-source", response_model=SourceWeatherResponse)
async def get_current_by_source(
    city_id: int = Query(..., description="City ID", gt=0),
    db: AsyncSession = Depends(get_db),
) -> SourceWeatherResponse:
    """Get current weather data broken down by individual source.

    Useful for comparing values across different data providers.
    """
    service = WeatherService(db)
    result = await service.get_by_source(city_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No weather data available for city_id={city_id}",
        )

    sources_data = {
        slug: SourceWeatherData(
            source_name=data["source_name"],
            priority=data["priority"],
            fetched_at=data["fetched_at"],
            weather=AggregatedWeather(**data["data"]),
        )
        for slug, data in result.items()
    }

    return SourceWeatherResponse(city_id=city_id, sources=sources_data)


@router.get("/chart/hourly", response_model=list[ChartPoint])
async def get_chart_hourly(
    city_id: int = Query(..., description="City ID", gt=0),
    db: AsyncSession = Depends(get_db),
) -> list[ChartPoint]:
    """Get hourly weather data for charts (next 24 hours)."""
    service = WeatherService(db)
    result = await service.get_chart_hourly(city_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No hourly chart data available for city_id={city_id}",
        )

    return [
        ChartPoint(
            hour=item["hour"],
            temperature=item.get("temperature"),
            feels_like=item.get("feels_like"),
            precipitation_amount=item.get("precipitation_amount"),
            wind_speed=item.get("wind_speed"),
            humidity=item.get("humidity"),
        )
        for item in result
    ]


@router.get("/chart/daily", response_model=list[DailyChartPoint])
async def get_chart_daily(
    city_id: int = Query(..., description="City ID", gt=0),
    days: int = Query(7, description="Number of days", ge=3, le=7),
    db: AsyncSession = Depends(get_db),
) -> list[DailyChartPoint]:
    """Get daily weather data for charts with min/max temperatures."""
    service = WeatherService(db)
    result = await service.get_chart_daily(city_id, days=days)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No daily chart data available for city_id={city_id}",
        )

    return [
        DailyChartPoint(
            date=item["date"],
            temp_min=item["temp_min"],
            temp_max=item["temp_max"],
            temp_avg=item["temp_avg"],
        )
        for item in result
    ]
