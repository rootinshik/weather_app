"""Micro-tests for admin API endpoints."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_current_admin
from app.dependencies import get_db
from app.main import app

VALID_KEY = "test-admin-key"
HEADERS = {"X-Admin-API-Key": VALID_KEY}


@pytest.fixture(autouse=True)
def override_admin_auth():
    """Replace admin auth with a passthrough that accepts VALID_KEY."""
    async def _auth(api_key=None):
        if api_key != VALID_KEY:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid or missing admin API key")
        return api_key

    app.dependency_overrides[get_current_admin] = lambda: VALID_KEY
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


# ---------------------------------------------------------------------------
# POST /api/v1/admin/auth
# ---------------------------------------------------------------------------

class TestAdminAuth:
    def test_returns_200_with_valid_key(self):
        resp = client.post("/api/v1/admin/auth", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == {"authenticated": True}

    def test_returns_401_without_key(self):
        app.dependency_overrides.clear()  # remove override for this test
        resp = client.post("/api/v1/admin/auth")
        assert resp.status_code == 401
        app.dependency_overrides[get_current_admin] = lambda: VALID_KEY

    def test_returns_401_with_wrong_key(self):
        app.dependency_overrides.clear()
        resp = client.post("/api/v1/admin/auth", headers={"X-Admin-API-Key": "wrong"})
        assert resp.status_code == 401
        app.dependency_overrides[get_current_admin] = lambda: VALID_KEY


# ---------------------------------------------------------------------------
# GET /api/v1/admin/stats
# ---------------------------------------------------------------------------

def _make_stat(d="2026-02-26", platform="web", total=10, unique=5):
    return type("UsageStat", (), {
        "date": date.fromisoformat(d),
        "platform": platform,
        "total_requests": total,
        "unique_users": unique,
        "city_queries_json": None,
    })()


class TestAdminStats:
    def test_returns_stats_list(self):
        with patch(
            "app.api.v1.admin.StatsService.get_stats",
            new=AsyncMock(return_value=[_make_stat()]),
        ):
            resp = client.get("/api/v1/admin/stats", headers=HEADERS)

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["platform"] == "web"
        assert body[0]["total_requests"] == 10

    def test_returns_empty_list_when_no_stats(self):
        with patch(
            "app.api.v1.admin.StatsService.get_stats",
            new=AsyncMock(return_value=[]),
        ):
            resp = client.get("/api/v1/admin/stats", headers=HEADERS)

        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /api/v1/admin/logs
# ---------------------------------------------------------------------------

def _make_log(id=1, platform="web", action="GET /api/v1/weather/current"):
    return type("RequestLog", (), {
        "id": id,
        "user_id": None,
        "platform": platform,
        "action": action,
        "city_id": None,
        "request_meta": {"status_code": 200},
        "created_at": datetime(2026, 2, 26, 12, 0, tzinfo=timezone.utc),
    })()


class TestAdminLogs:
    def test_returns_paginated_logs(self):
        with patch(
            "app.api.v1.admin.StatsService.get_logs",
            new=AsyncMock(return_value=(1, [_make_log()])),
        ):
            resp = client.get("/api/v1/admin/logs?limit=10&offset=0", headers=HEADERS)

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["limit"] == 10
        assert body["offset"] == 0
        assert len(body["items"]) == 1
        assert body["items"][0]["action"] == "GET /api/v1/weather/current"

    def test_returns_422_when_limit_too_large(self):
        resp = client.get("/api/v1/admin/logs?limit=9999", headers=HEADERS)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/admin/sources
# ---------------------------------------------------------------------------

def _make_source_orm(slug="openweathermap", enabled=True, priority=3):
    return type("WeatherSource", (), {
        "id": 1, "slug": slug, "display_name": "OWM",
        "source_type": "rest", "priority": priority, "is_enabled": enabled,
    })()


def _db_scalars(items):
    r = MagicMock()
    r.scalars.return_value.all.return_value = items
    s = AsyncMock()
    s.execute = AsyncMock(return_value=r)
    return s


def _db_scalar_one(item):
    r = MagicMock()
    r.scalar_one_or_none.return_value = item
    s = AsyncMock()
    s.execute = AsyncMock(return_value=r)
    s.commit = AsyncMock()
    s.refresh = AsyncMock()
    return s


class TestAdminSources:
    def test_returns_all_sources(self):
        session = _db_scalars([_make_source_orm()])

        async def override():
            yield session

        app.dependency_overrides[get_db] = override
        resp = client.get("/api/v1/admin/sources", headers=HEADERS)
        app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200
        assert resp.json()[0]["slug"] == "openweathermap"

    def test_patch_source_updates_fields(self):
        source_orm = _make_source_orm()
        session = _db_scalar_one(source_orm)

        async def override():
            yield session

        app.dependency_overrides[get_db] = override
        resp = client.patch(
            "/api/v1/admin/sources/openweathermap",
            json={"is_enabled": False, "priority": 1},
            headers=HEADERS,
        )
        app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200

    def test_patch_source_returns_404_for_unknown(self):
        session = _db_scalar_one(None)

        async def override():
            yield session

        app.dependency_overrides[get_db] = override
        resp = client.patch(
            "/api/v1/admin/sources/unknown",
            json={"is_enabled": False},
            headers=HEADERS,
        )
        app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/admin/fetch-now
# ---------------------------------------------------------------------------

class TestAdminFetchNow:
    def test_triggers_fetch_for_specific_city(self):
        with patch(
            "app.api.v1.admin.WeatherService.fetch_and_save",
            new=AsyncMock(),
        ):
            resp = client.post(
                "/api/v1/admin/fetch-now?city_id=1", headers=HEADERS
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["triggered"] is True
        assert body["cities_count"] == 1

    def test_triggers_fetch_for_all_cities(self):
        city_orm = type("City", (), {"id": 1})()
        session = _db_scalars([city_orm, city_orm])  # 2 cities

        async def override():
            yield session

        app.dependency_overrides[get_db] = override

        with patch("app.api.v1.admin.WeatherService.fetch_and_save", new=AsyncMock()):
            resp = client.post("/api/v1/admin/fetch-now", headers=HEADERS)

        app.dependency_overrides.pop(get_db, None)

        assert resp.status_code == 200
        assert resp.json()["cities_count"] == 2
