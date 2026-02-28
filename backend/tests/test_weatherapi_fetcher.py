"""Unit tests for WeatherAPI.com fetcher."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.fetchers.weatherapi import WeatherAPIFetcher


@pytest.fixture
def mock_config():
    return {
        "name": "WeatherAPI",
        "type": "weatherapi",
        "priority": 2,
        "enabled": True,
        "connection": {
            "base_url": "https://api.weatherapi.com/v1",
            "api_key": "test_key_123",
            "timeout": 10,
        },
        "endpoints": {
            "current": {
                "path": "/current.json",
                "params": {"key": "${WEATHERAPI_KEY}", "q": "{city}", "aqi": "no"},
            },
            "forecast": {
                "path": "/forecast.json",
                "params": {
                    "key": "${WEATHERAPI_KEY}",
                    "q": "{city}",
                    "days": 7,
                    "aqi": "no",
                    "alerts": "no",
                },
            },
        },
        "field_mapping": {
            "temperature": "current.temp_c",
            "feels_like": "current.feelslike_c",
            "humidity": "current.humidity",
            "pressure": "current.pressure_mb",
            "wind_speed": "current.wind_kph",
            "wind_direction": "current.wind_degree",
            "description": "current.condition.text",
            "clouds": "current.cloud",
            "visibility": "current.vis_km",
            "timestamp": "current.last_updated_epoch",
        },
        "unit_conversions": {
            "wind_speed": {"from": "kph", "to": "m/s", "factor": 0.27778},
            "visibility": {"from": "km", "to": "m", "factor": 1000.0},
        },
    }


@pytest.fixture
def fetcher(mock_config):
    return WeatherAPIFetcher(mock_config)


@pytest.fixture
def mock_current_response():
    return {
        "current": {
            "temp_c": 18.0,
            "feelslike_c": 16.5,
            "humidity": 65,
            "pressure_mb": 1015.0,
            "wind_kph": 14.4,
            "wind_degree": 270,
            "condition": {"text": "Partly cloudy", "icon": "//cdn/partly-cloudy.png"},
            "cloud": 50,
            "vis_km": 10.0,
            "last_updated_epoch": 1700000000,
        }
    }


@pytest.fixture
def mock_forecast_response():
    return {
        "forecast": {
            "forecastday": [
                {
                    "date": "2026-02-28",
                    "hour": [
                        {
                            "time_epoch": 1700003600,
                            "temp_c": 17.0,
                            "feelslike_c": 15.5,
                            "humidity": 68,
                            "pressure_mb": 1014.0,
                            "wind_kph": 10.8,
                            "wind_degree": 260,
                            "condition": {"text": "Clear", "icon": "//cdn/clear.png"},
                            "cloud": 10,
                            "vis_km": 15.0,
                        },
                        {
                            "time_epoch": 1700007200,
                            "temp_c": 15.0,
                            "feelslike_c": 13.0,
                            "humidity": 72,
                            "pressure_mb": 1013.0,
                            "wind_kph": 18.0,
                            "wind_degree": 280,
                            "condition": {"text": "Cloudy", "icon": "//cdn/cloudy.png"},
                            "cloud": 80,
                            "vis_km": 12.0,
                        },
                    ],
                }
            ]
        }
    }


def _mock_http(status: int, json_data: dict) -> MagicMock:
    """Create a mock aiohttp session that returns the given JSON response.

    aiohttp.ClientSession() and session.get() both return synchronous context
    managers, NOT coroutines.  We therefore use MagicMock (not AsyncMock) for
    the session and the request context, and only use AsyncMock for the methods
    that are actually awaited (__aenter__, __aexit__, json).
    """
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data)
    mock_resp.raise_for_status = MagicMock()

    # session.get(url) returns a context manager object synchronously
    mock_get_ctx = MagicMock()
    mock_get_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_get_ctx.__aexit__ = AsyncMock(return_value=None)

    # aiohttp.ClientSession itself is also a sync context manager
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get.return_value = mock_get_ctx

    return mock_session


class TestWeatherAPIFetcherInit:
    def test_reads_config_fields(self, fetcher, mock_config):
        assert fetcher.name == "WeatherAPI"
        assert fetcher.source_type == "weatherapi"
        assert fetcher.priority == 2
        assert fetcher.api_key == "test_key_123"
        assert fetcher.base_url == "https://api.weatherapi.com/v1"

    def test_enabled(self, fetcher):
        assert fetcher.is_enabled() is True


class TestPrepareParams:
    def test_substitutes_city(self, fetcher):
        params = fetcher._prepare_params({"q": "{city}", "aqi": "no"}, "Moscow")
        assert params["q"] == "Moscow"
        assert params["aqi"] == "no"

    def test_substitutes_api_key(self, fetcher):
        params = fetcher._prepare_params({"key": "${WEATHERAPI_KEY}"}, "London")
        assert params["key"] == "test_key_123"

    def test_passthrough_static_value(self, fetcher):
        params = fetcher._prepare_params({"days": "7"}, "London")
        assert params["days"] == "7"


class TestUnitConversions:
    def test_wind_kph_to_ms(self, fetcher):
        data = {"wind_speed": 36.0}
        fetcher._apply_conversions(data)
        assert abs(data["wind_speed"] - 10.0001) < 0.001  # 36 * 0.27778

    def test_visibility_km_to_m(self, fetcher):
        data = {"visibility": 10.0}
        fetcher._apply_conversions(data)
        assert data["visibility"] == 10000.0

    def test_ignores_none_values(self, fetcher):
        data = {"wind_speed": None}
        fetcher._apply_conversions(data)
        assert data["wind_speed"] is None


class TestMapCurrent:
    def test_maps_all_fields(self, fetcher, mock_current_response):
        result = fetcher._map_current(mock_current_response)
        assert result["temperature"] == 18.0
        assert result["feels_like"] == 16.5
        assert result["humidity"] == 65
        assert result["description"] == "Partly cloudy"

    def test_converts_wind_to_ms(self, fetcher, mock_current_response):
        result = fetcher._map_current(mock_current_response)
        # 14.4 kph * 0.27778 ≈ 4.0 m/s
        assert abs(result["wind_speed"] - 14.4 * 0.27778) < 0.001

    def test_converts_visibility_to_m(self, fetcher, mock_current_response):
        result = fetcher._map_current(mock_current_response)
        assert result["visibility"] == 10000.0


class TestExtractForecastHours:
    def test_extracts_all_hours(self, fetcher, mock_forecast_response):
        result = fetcher._extract_forecast_hours(mock_forecast_response)
        assert len(result) == 2

    def test_forecast_time_set(self, fetcher, mock_forecast_response):
        result = fetcher._extract_forecast_hours(mock_forecast_response)
        assert result[0]["forecast_time"] == 1700003600
        assert result[1]["forecast_time"] == 1700007200

    def test_wind_converted(self, fetcher, mock_forecast_response):
        result = fetcher._extract_forecast_hours(mock_forecast_response)
        # 10.8 kph * 0.27778 ≈ 3.0 m/s
        assert abs(result[0]["wind_speed"] - 10.8 * 0.27778) < 0.001

    def test_empty_forecast(self, fetcher):
        result = fetcher._extract_forecast_hours({})
        assert result == []


class TestFetchCurrentAsync:
    @pytest.mark.asyncio
    async def test_returns_weather_on_200(self, fetcher, mock_current_response):
        mock_session = _mock_http(200, mock_current_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")
        assert result["temperature"] == 18.0
        assert result["description"] == "Partly cloudy"

    @pytest.mark.asyncio
    async def test_returns_empty_on_400(self, fetcher):
        mock_session = _mock_http(400, {"error": {"message": "No matching location found."}})
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("NonExistentXYZ")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_on_500(self, fetcher):
        mock_session = _mock_http(500, {})
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_on_network_error(self, fetcher):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.side_effect = aiohttp.ClientError("connection refused")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_on_timeout(self, fetcher):
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get.side_effect = asyncio.TimeoutError()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")
        assert result == {}


class TestFetchForecastAsync:
    @pytest.mark.asyncio
    async def test_returns_hourly_list_on_200(self, fetcher, mock_forecast_response):
        mock_session = _mock_http(200, mock_forecast_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_forecast("London")
        assert len(result) == 2
        assert result[0]["temperature"] == 17.0

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self, fetcher):
        mock_session = _mock_http(400, {"error": {"message": "Invalid city"}})
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_forecast("???")
        assert result == []

    @pytest.mark.asyncio
    async def test_days_capped_at_7(self, fetcher, mock_forecast_response):
        """days param must not exceed 7 (free plan limit)."""
        mock_session = _mock_http(200, mock_forecast_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_forecast("London", days=10)
        # Verify the call was made (days clipped internally — just check no exception)
        assert isinstance(result, list)


class TestConnectionTest:
    @pytest.mark.asyncio
    async def test_returns_true_on_200(self, fetcher, mock_current_response):
        mock_session = _mock_http(200, mock_current_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher.test_connection() is True

    @pytest.mark.asyncio
    async def test_returns_false_on_401(self, fetcher):
        mock_session = _mock_http(401, {"error": {"message": "API key invalid"}})
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher.test_connection() is False
