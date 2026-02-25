"""Micro-tests for weather API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.weather import AggregatedWeather

client = TestClient(app)

SAMPLE_WEATHER = AggregatedWeather(
    temperature=15.0,
    feels_like=13.0,
    wind_speed=5.0,
    wind_direction=270,
    humidity=65,
    pressure=1013.0,
    precipitation_type="none",
    precipitation_amount=0.0,
    cloudiness=40,
    description="Partly cloudy",
    icon_code="02d",
)

SAMPLE_FORECAST_ITEM = {
    "forecast_dt": datetime(2026, 2, 27, 12, 0, tzinfo=timezone.utc),
    "data": SAMPLE_WEATHER.model_dump(),
}

SAMPLE_BY_SOURCE = {
    "openweathermap": {
        "source_name": "OpenWeatherMap",
        "priority": 3,
        "fetched_at": datetime(2026, 2, 26, 10, 0, tzinfo=timezone.utc),
        "data": SAMPLE_WEATHER.model_dump(),
    }
}

SAMPLE_HOURLY = [
    {
        "hour": datetime(2026, 2, 26, h, 0, tzinfo=timezone.utc),
        "temperature": 15.0 + h * 0.5,
        "feels_like": 13.0,
        "precipitation_amount": 0.0,
        "wind_speed": 5.0,
        "humidity": 65,
    }
    for h in range(3)
]

SAMPLE_DAILY = [
    {"date": "2026-02-26", "temp_min": 8.0, "temp_max": 16.0, "temp_avg": 12.0},
    {"date": "2026-02-27", "temp_min": 7.0, "temp_max": 15.0, "temp_avg": 11.0},
]


# ---------------------------------------------------------------------------
# GET /api/v1/weather/current
# ---------------------------------------------------------------------------

class TestGetCurrentWeather:
    def test_returns_200_with_weather(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_aggregated_current",
            new=AsyncMock(return_value=SAMPLE_WEATHER),
        ):
            resp = client.get("/api/v1/weather/current?city_id=1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["city_id"] == 1
        assert body["weather"]["temperature"] == 15.0
        assert "fetched_at" in body

    def test_returns_404_when_no_data(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_aggregated_current",
            new=AsyncMock(return_value=None),
        ):
            resp = client.get("/api/v1/weather/current?city_id=999")

        assert resp.status_code == 404

    def test_returns_422_without_city_id(self):
        resp = client.get("/api/v1/weather/current")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/weather/forecast
# ---------------------------------------------------------------------------

class TestGetForecast:
    def test_returns_200_with_forecasts(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_aggregated_forecast",
            new=AsyncMock(return_value=[SAMPLE_FORECAST_ITEM]),
        ):
            resp = client.get("/api/v1/weather/forecast?city_id=1&days=5")

        assert resp.status_code == 200
        body = resp.json()
        assert body["city_id"] == 1
        assert body["days"] == 5
        assert len(body["forecasts"]) == 1
        assert body["forecasts"][0]["weather"]["temperature"] == 15.0

    def test_returns_404_when_no_data(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_aggregated_forecast",
            new=AsyncMock(return_value=[]),
        ):
            resp = client.get("/api/v1/weather/forecast?city_id=999")

        assert resp.status_code == 404

    def test_returns_422_when_days_out_of_range(self):
        resp = client.get("/api/v1/weather/forecast?city_id=1&days=10")
        assert resp.status_code == 422

    def test_returns_422_when_days_too_small(self):
        resp = client.get("/api/v1/weather/forecast?city_id=1&days=2")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/weather/current/by-source
# ---------------------------------------------------------------------------

class TestGetCurrentBySource:
    def test_returns_200_with_sources(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_by_source",
            new=AsyncMock(return_value=SAMPLE_BY_SOURCE),
        ):
            resp = client.get("/api/v1/weather/current/by-source?city_id=1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["city_id"] == 1
        assert "openweathermap" in body["sources"]
        assert body["sources"]["openweathermap"]["source_name"] == "OpenWeatherMap"

    def test_returns_404_when_no_data(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_by_source",
            new=AsyncMock(return_value={}),
        ):
            resp = client.get("/api/v1/weather/current/by-source?city_id=999")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/weather/chart/hourly
# ---------------------------------------------------------------------------

class TestGetChartHourly:
    def test_returns_200_with_hourly_points(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_chart_hourly",
            new=AsyncMock(return_value=SAMPLE_HOURLY),
        ):
            resp = client.get("/api/v1/weather/chart/hourly?city_id=1")

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 3
        assert "hour" in body[0]
        assert "temperature" in body[0]

    def test_returns_404_when_no_data(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_chart_hourly",
            new=AsyncMock(return_value=[]),
        ):
            resp = client.get("/api/v1/weather/chart/hourly?city_id=999")

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/weather/chart/daily
# ---------------------------------------------------------------------------

class TestGetChartDaily:
    def test_returns_200_with_daily_points(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_chart_daily",
            new=AsyncMock(return_value=SAMPLE_DAILY),
        ):
            resp = client.get("/api/v1/weather/chart/daily?city_id=1&days=7")

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 2
        assert body[0]["date"] == "2026-02-26"
        assert body[0]["temp_min"] == 8.0
        assert body[0]["temp_max"] == 16.0

    def test_returns_404_when_no_data(self):
        with patch(
            "app.api.v1.weather.WeatherService.get_chart_daily",
            new=AsyncMock(return_value=[]),
        ):
            resp = client.get("/api/v1/weather/chart/daily?city_id=999")

        assert resp.status_code == 404

    def test_returns_422_when_days_too_small(self):
        resp = client.get("/api/v1/weather/chart/daily?city_id=1&days=2")
        assert resp.status_code == 422
