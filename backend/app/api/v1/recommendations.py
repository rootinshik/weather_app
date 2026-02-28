"""Clothing recommendation API endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.recommendation import ClothingRecommendationResponse
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/clothing", response_model=ClothingRecommendationResponse)
async def get_clothing_recommendation(
    city_id: int = Query(..., ge=1, description="City ID to get clothing recommendations for"),
    db: AsyncSession = Depends(get_db),
) -> ClothingRecommendationResponse:
    """Get ML-based clothing recommendations for current weather in a city.

    Returns 503 if the ML model has not been trained yet.
    Returns 404 if no weather data is available for the city.
    """
    if not RecommendationService.is_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "ML model is not loaded. "
                "Run: docker compose --profile training run ml-train"
            ),
        )

    service = RecommendationService(db)
    try:
        result = await service.get_recommendation(city_id)
    except RuntimeError as exc:
        logger.error("Recommendation error for city_id=%d: %s", city_id, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No weather data available for city_id={city_id}",
        )

    return result
