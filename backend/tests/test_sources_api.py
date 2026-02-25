"""Micro-tests for sources API endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Result

from app.dependencies import get_db
from app.main import app


def _make_source(id, slug, name, priority=1, enabled=True):
    return type("WeatherSource", (), {
        "id": id,
        "slug": slug,
        "display_name": name,
        "source_type": "rest",
        "priority": priority,
        "is_enabled": enabled,
    })()


OWM = _make_source(1, "openweathermap", "OpenWeatherMap", priority=3)
WAPI = _make_source(2, "weatherapi", "WeatherAPI", priority=2)


def _make_session_scalars(items):
    mock_result = MagicMock(spec=Result)
    mock_result.scalars.return_value.all.return_value = items
    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)
    return session


def _make_session_scalar_one(item):
    mock_result = MagicMock(spec=Result)
    mock_result.scalar_one_or_none.return_value = item
    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)
    return session


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


class TestListSources:
    def test_returns_all_sources(self):
        session = _make_session_scalars([OWM, WAPI])

        async def override():
            yield session

        app.dependency_overrides[get_db] = override
        resp = TestClient(app).get("/api/v1/sources")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        assert body[0]["slug"] == "openweathermap"
        assert body[1]["slug"] == "weatherapi"

    def test_returns_empty_list_when_no_sources(self):
        session = _make_session_scalars([])

        async def override():
            yield session

        app.dependency_overrides[get_db] = override
        resp = TestClient(app).get("/api/v1/sources")

        assert resp.status_code == 200
        assert resp.json() == []


class TestGetSource:
    def test_returns_source_by_slug(self):
        session = _make_session_scalar_one(OWM)

        async def override():
            yield session

        app.dependency_overrides[get_db] = override
        resp = TestClient(app).get("/api/v1/sources/openweathermap")

        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == "openweathermap"
        assert body["display_name"] == "OpenWeatherMap"
        assert body["priority"] == 3

    def test_returns_404_for_unknown_slug(self):
        session = _make_session_scalar_one(None)

        async def override():
            yield session

        app.dependency_overrides[get_db] = override
        resp = TestClient(app).get("/api/v1/sources/unknown")

        assert resp.status_code == 404
