"""Pydantic schemas for city data."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CitySearchResult(BaseModel):
    """Single result from geocoding search (not yet saved in DB)."""

    name: str
    local_name: str | None = None
    country: str = Field(description="ISO 3166-1 alpha-2 country code")
    lat: float
    lon: float


class CityCreate(BaseModel):
    """Input for creating a new city in the database."""

    name: str = Field(min_length=1, max_length=100)
    local_name: str | None = Field(None, max_length=200)
    country: str = Field(min_length=2, max_length=2)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class CityResponse(BaseModel):
    """City record as stored in the database."""

    id: int
    name: str
    local_name: str | None
    country: str
    lat: float
    lon: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
