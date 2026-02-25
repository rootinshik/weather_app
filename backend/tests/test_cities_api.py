"""Micro-tests for cities API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.city import CitySearchResult

client = TestClient(app)

SAMPLE_SEARCH = [
    CitySearchResult(name="Moscow", local_name="Москва", country="RU", lat=55.75, lon=37.61),
    CitySearchResult(name="Moscow", local_name=None, country="US", lat=46.73, lon=-117.0),
]

SAMPLE_CITY_ORM = type("City", (), {
    "id": 1,
    "name": "Moscow",
    "local_name": "Москва",
    "country": "RU",
    "lat": 55.75,
    "lon": 37.61,
    "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
})()


class TestSearchCities:
    def test_returns_list_from_geocoding(self):
        with patch(
            "app.api.v1.cities.CityService.search",
            new=AsyncMock(return_value=SAMPLE_SEARCH),
        ):
            resp = client.get("/api/v1/cities/search?q=Moscow")

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 2
        assert body[0]["name"] == "Moscow"
        assert body[0]["country"] == "RU"

    def test_returns_empty_list_when_no_results(self):
        with patch(
            "app.api.v1.cities.CityService.search",
            new=AsyncMock(return_value=[]),
        ):
            resp = client.get("/api/v1/cities/search?q=Xyzzy")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_422_without_query(self):
        resp = client.get("/api/v1/cities/search")
        assert resp.status_code == 422

    def test_limit_param_accepted(self):
        with patch(
            "app.api.v1.cities.CityService.search",
            new=AsyncMock(return_value=SAMPLE_SEARCH[:1]),
        ):
            resp = client.get("/api/v1/cities/search?q=Moscow&limit=1")

        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetCity:
    def test_returns_city_by_id(self):
        with patch(
            "app.api.v1.cities.CityService.get_by_id",
            new=AsyncMock(return_value=SAMPLE_CITY_ORM),
        ):
            resp = client.get("/api/v1/cities/1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 1
        assert body["name"] == "Moscow"
        assert body["country"] == "RU"

    def test_returns_404_when_not_found(self):
        with patch(
            "app.api.v1.cities.CityService.get_by_id",
            new=AsyncMock(return_value=None),
        ):
            resp = client.get("/api/v1/cities/999")

        assert resp.status_code == 404


class TestCreateCity:
    def test_creates_and_returns_city(self):
        with patch(
            "app.api.v1.cities.CityService.get_or_create",
            new=AsyncMock(return_value=SAMPLE_CITY_ORM),
        ):
            resp = client.post("/api/v1/cities", json={
                "name": "Moscow",
                "local_name": "Москва",
                "country": "RU",
                "lat": 55.75,
                "lon": 37.61,
            })

        assert resp.status_code == 201
        body = resp.json()
        assert body["id"] == 1
        assert body["name"] == "Moscow"

    def test_returns_422_with_invalid_country_code(self):
        resp = client.post("/api/v1/cities", json={
            "name": "Moscow",
            "country": "RUS",  # must be 2 chars
            "lat": 55.75,
            "lon": 37.61,
        })
        assert resp.status_code == 422
