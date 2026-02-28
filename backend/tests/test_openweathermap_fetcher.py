"""Unit tests for OpenWeatherMap fetcher."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.fetchers.openweathermap import OpenWeatherMapFetcher


@pytest.fixture
def mock_config():
    """Mock configuration for OpenWeatherMap fetcher."""
    return {
        "name": "OpenWeatherMap",
        "type": "rest",
        "priority": 1,
        "enabled": True,
        "connection": {
            "base_url": "https://api.openweathermap.org/data/2.5",
            "api_key": "test_api_key_12345",
            "timeout": 10,
        },
        "endpoints": {
            "current": {
                "path": "/weather",
                "params": {
                    "q": "{city}",
                    "appid": "${OWM_API_KEY}",
                    "units": "metric",
                },
            },
            "forecast": {
                "path": "/forecast",
                "params": {
                    "q": "{city}",
                    "appid": "${OWM_API_KEY}",
                    "units": "metric",
                    "cnt": "40",
                },
            },
        },
        "field_mapping": {
            "temperature": "main.temp",
            "feels_like": "main.feels_like",
            "humidity": "main.humidity",
            "pressure": "main.pressure",
            "wind_speed": "wind.speed",
            "wind_direction": "wind.deg",
            "description": "weather.0.description",
            "icon_code": "weather.0.icon",
            "cloudiness": "clouds.all",
            "visibility": "visibility",
            "timestamp": "dt",
        },
    }


@pytest.fixture
def fetcher(mock_config):
    """Create OpenWeatherMap fetcher instance."""
    return OpenWeatherMapFetcher(mock_config)


@pytest.fixture
def mock_current_weather_response():
    """Mock API response for current weather."""
    return {
        "main": {
            "temp": 15.5,
            "feels_like": 14.2,
            "humidity": 72,
            "pressure": 1013,
        },
        "wind": {
            "speed": 3.5,
            "deg": 180,
        },
        "weather": [
            {
                "description": "light rain",
                "icon": "10d",
            }
        ],
        "clouds": {
            "all": 75,
        },
        "visibility": 10000,
        "dt": 1700000000,
    }


@pytest.fixture
def mock_forecast_response():
    """Mock API response for forecast."""
    return {
        "list": [
            {
                "main": {"temp": 16.0, "feels_like": 15.0, "humidity": 70, "pressure": 1012},
                "wind": {"speed": 4.0, "deg": 190},
                "weather": [{"description": "cloudy", "icon": "04d"}],
                "clouds": {"all": 80},
                "visibility": 9000,
                "dt": 1700003600,
            },
            {
                "main": {"temp": 14.5, "feels_like": 13.5, "humidity": 75, "pressure": 1011},
                "wind": {"speed": 3.0, "deg": 170},
                "weather": [{"description": "rain", "icon": "10d"}],
                "clouds": {"all": 90},
                "visibility": 8000,
                "dt": 1700007200,
            },
        ]
    }


def _mock_http(status: int, json_data: dict) -> MagicMock:
    """Create a properly-wired aiohttp session mock.

    aiohttp.ClientSession.get() returns a *synchronous* context manager, so
    the session and the request context must be MagicMock (not AsyncMock).
    Only __aenter__ / __aexit__ and .json() are coroutines and use AsyncMock.
    """
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data)
    mock_resp.raise_for_status = MagicMock()

    mock_get_ctx = MagicMock()
    mock_get_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_get_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get.return_value = mock_get_ctx

    return mock_session


class TestOpenWeatherMapFetcher:
    """Test suite for OpenWeatherMap fetcher."""

    def test_initialization(self, fetcher, mock_config):
        """Test fetcher initialization."""
        assert fetcher.name == "OpenWeatherMap"
        assert fetcher.source_type == "rest"
        assert fetcher.priority == 1
        assert fetcher.enabled is True
        assert fetcher.base_url == "https://api.openweathermap.org/data/2.5"
        assert fetcher.api_key == "test_api_key_12345"
        assert fetcher.timeout == 10

    def test_prepare_params(self, fetcher):
        """Test parameter preparation with city substitution."""
        params_config = {
            "q": "{city}",
            "appid": "${OWM_API_KEY}",
            "units": "metric",
        }

        result = fetcher._prepare_params(params_config, "Moscow")

        assert result["q"] == "Moscow"
        assert result["appid"] == "test_api_key_12345"
        assert result["units"] == "metric"

    def test_map_fields(self, fetcher, mock_current_weather_response):
        """Test field mapping from API response to normalized format."""
        result = fetcher._map_fields(mock_current_weather_response)

        assert result["temperature"] == 15.5
        assert result["feels_like"] == 14.2
        assert result["humidity"] == 72
        assert result["pressure"] == 1013
        assert result["wind_speed"] == 3.5
        assert result["wind_direction"] == 180
        assert result["description"] == "light rain"
        assert result["icon_code"] == "10d"
        assert result["cloudiness"] == 75
        assert result["visibility"] == 10000
        assert result["timestamp"] == 1700000000

    @pytest.mark.asyncio
    async def test_fetch_current_success(
        self, fetcher, mock_current_weather_response
    ):
        """Test successful current weather fetch."""
        mock_session = _mock_http(200, mock_current_weather_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")

        assert result["temperature"] == 15.5
        assert result["description"] == "light rain"

    @pytest.mark.asyncio
    async def test_fetch_current_city_not_found(self, fetcher):
        """Test fetch_current with non-existent city (404)."""
        mock_response = AsyncMock()
        mock_response.status = 404

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session.get.return_value.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("NonExistentCity")

        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_current_api_error(self, fetcher):
        """Test fetch_current with API error (500)."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session.get.return_value.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")

        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_forecast_success(self, fetcher, mock_forecast_response):
        """Test successful forecast fetch."""
        mock_session = _mock_http(200, mock_forecast_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_forecast("London")

        assert len(result) == 2
        assert result[0]["temperature"] == 16.0
        assert result[0]["forecast_time"] == 1700003600
        assert result[1]["temperature"] == 14.5
        assert result[1]["forecast_time"] == 1700007200

    @pytest.mark.asyncio
    async def test_fetch_forecast_empty_list(self, fetcher):
        """Test forecast with empty list response."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"list": []})
        mock_response.raise_for_status = MagicMock()

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session.get.return_value.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_forecast("Moscow")

        assert result == []

    @pytest.mark.asyncio
    async def test_test_connection_success(self, fetcher, mock_current_weather_response):
        """Test successful connection test."""
        mock_session = _mock_http(200, mock_current_weather_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, fetcher):
        """Test connection test failure."""
        mock_response = AsyncMock()
        mock_response.status = 401  # Unauthorized

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get.return_value.__aenter__.return_value = mock_response
        mock_session.get.return_value.__aexit__.return_value = None

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.test_connection()

        assert result is False
