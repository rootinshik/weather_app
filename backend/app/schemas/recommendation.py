"""Pydantic schemas for clothing recommendation responses."""

from pydantic import BaseModel, Field


class ClothingRecommendationResponse(BaseModel):
    """Response for GET /api/v1/recommendations/clothing."""

    city_id: int = Field(description="City ID used for prediction")
    category: str = Field(
        description="ML-predicted clothing category key (e.g. 'winter_heavy')"
    )
    description: str = Field(
        description="Human-readable description of the predicted category"
    )
    items: list[str] = Field(description="Recommended clothing and accessory items")

    model_config = {
        "json_schema_extra": {
            "example": {
                "city_id": 1,
                "category": "warm_rain",
                "description": "Холодно и дождливо — непромокаемая одежда",
                "items": [
                    "непромокаемая куртка",
                    "свитер",
                    "джинсы",
                    "резиновые сапоги",
                    "зонт",
                ],
            }
        }
    }
