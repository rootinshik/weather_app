"""Micro-tests for BackendAPIClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.api_client import BackendAPIClient

BASE_URL = "http://backend:8000"


def _mock_response(status: int, data) -> MagicMock:
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _patch_session(client: BackendAPIClient, method: str, response: MagicMock):
    """Patch the aiohttp session to return the given response."""
    mock_session = MagicMock()
    mock_session.closed = False
    getattr(mock_session, method).return_value = response
    client._session = mock_session
    return mock_session


class TestGetCurrentWeather:
    @pytest.mark.asyncio
    async def test_returns_weather_on_200(self):
        client = BackendAPIClient(BASE_URL)
        data = {"city_id": 1, "weather": {"temperature": 15.0}}
        _patch_session(client, "get", _mock_response(200, data))

        result = await client.get_current_weather(city_id=1)
        assert result == data

    @pytest.mark.asyncio
    async def test_returns_none_on_404(self):
        client = BackendAPIClient(BASE_URL)
        _patch_session(client, "get", _mock_response(404, {}))

        result = await client.get_current_weather(city_id=999)
        assert result is None


class TestGetForecast:
    @pytest.mark.asyncio
    async def test_returns_forecast_on_200(self):
        client = BackendAPIClient(BASE_URL)
        data = {"city_id": 1, "days": 5, "forecasts": []}
        _patch_session(client, "get", _mock_response(200, data))

        result = await client.get_forecast(city_id=1, days=5)
        assert result == data


class TestSearchCities:
    @pytest.mark.asyncio
    async def test_returns_list_on_200(self):
        client = BackendAPIClient(BASE_URL)
        data = [{"name": "Moscow", "country": "RU", "lat": 55.75, "lon": 37.61}]
        _patch_session(client, "get", _mock_response(200, data))

        result = await client.search_cities("Moscow")
        assert len(result) == 1
        assert result[0]["name"] == "Moscow"

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_error(self):
        client = BackendAPIClient(BASE_URL)
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.get.side_effect = Exception("network error")
        client._session = mock_session

        result = await client.search_cities("Moscow")
        assert result == []


class TestIdentifyUser:
    @pytest.mark.asyncio
    async def test_returns_user_on_200(self):
        client = BackendAPIClient(BASE_URL)
        data = {"id": 1, "platform": "telegram", "external_id": "12345"}
        _patch_session(client, "post", _mock_response(200, data))

        result = await client.identify_user("telegram", "12345")
        assert result == data

    @pytest.mark.asyncio
    async def test_returns_none_on_server_error(self):
        client = BackendAPIClient(BASE_URL)
        _patch_session(client, "post", _mock_response(500, {}))

        result = await client.identify_user("telegram", "12345")
        assert result is None


class TestUpdatePreferences:
    @pytest.mark.asyncio
    async def test_patches_preferred_city(self):
        client = BackendAPIClient(BASE_URL)
        data = {"id": 1, "preferred_city_id": 2}
        _patch_session(client, "patch", _mock_response(200, data))

        result = await client.update_preferences(user_id=1, preferred_city_id=2)
        assert result["preferred_city_id"] == 2


class TestGetSources:
    @pytest.mark.asyncio
    async def test_returns_sources_list(self):
        client = BackendAPIClient(BASE_URL)
        data = [{"slug": "openweathermap", "priority": 3}]
        _patch_session(client, "get", _mock_response(200, data))

        result = await client.get_sources()
        assert len(result) == 1
        assert result[0]["slug"] == "openweathermap"
