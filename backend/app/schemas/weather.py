"""Pydantic schemas for weather data."""

from datetime import datetime

from pydantic import BaseModel, Field


class AggregatedWeather(BaseModel):
    """Schema for aggregated weather data from multiple sources.

    All numeric values are stored in SI units:
    - Temperature: Celsius (°C)
    - Wind speed: meters per second (m/s)
    - Pressure: hectopascals (hPa)
    - Precipitation: millimeters (mm)
    """

    temperature: float | None = Field(
        None, description="Temperature in Celsius", ge=-100, le=60
    )
    feels_like: float | None = Field(
        None, description="Feels like temperature in Celsius", ge=-100, le=60
    )
    wind_speed: float | None = Field(
        None, description="Wind speed in m/s", ge=0, le=200
    )
    wind_direction: int | None = Field(
        None, description="Wind direction in degrees (0-360)", ge=0, le=360
    )
    humidity: int | None = Field(
        None, description="Relative humidity in percent", ge=0, le=100
    )
    pressure: float | None = Field(
        None, description="Atmospheric pressure in hPa", ge=800, le=1100
    )
    precipitation_type: str | None = Field(
        None, description="Type of precipitation (rain, snow, sleet, none)"
    )
    precipitation_amount: float | None = Field(
        None, description="Precipitation amount in mm", ge=0
    )
    cloudiness: int | None = Field(
        None, description="Cloudiness in percent", ge=0, le=100
    )
    description: str | None = Field(
        None, description="Weather description"
    )
    icon_code: str | None = Field(
        None, description="Weather icon code"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "temperature": 15.5,
                "feels_like": 13.2,
                "wind_speed": 5.5,
                "wind_direction": 270,
                "humidity": 65,
                "pressure": 1013.25,
                "precipitation_type": "none",
                "precipitation_amount": 0.0,
                "cloudiness": 40,
                "description": "Partly cloudy",
                "icon_code": "02d"
            }
        }
    }
