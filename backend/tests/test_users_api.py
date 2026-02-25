"""Micro-tests for users API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_user(id=1, platform="web", external_id="uuid-abc", preferred_city_id=None):
    return type("User", (), {
        "id": id,
        "platform": platform,
        "external_id": external_id,
        "preferred_city_id": preferred_city_id,
        "settings_json": None,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "last_active_at": datetime(2026, 2, 26, tzinfo=timezone.utc),
    })()


SAMPLE_USER = _make_user()
USER_WITH_CITY = _make_user(preferred_city_id=1)


class TestIdentifyUser:
    def test_creates_new_user(self):
        with patch(
            "app.api.v1.users.UserService.identify",
            new=AsyncMock(return_value=SAMPLE_USER),
        ):
            resp = client.post("/api/v1/users/identify", json={
                "platform": "web",
                "external_id": "uuid-abc",
            })

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 1
        assert body["platform"] == "web"
        assert body["external_id"] == "uuid-abc"

    def test_returns_existing_user(self):
        with patch(
            "app.api.v1.users.UserService.identify",
            new=AsyncMock(return_value=SAMPLE_USER),
        ):
            resp = client.post("/api/v1/users/identify", json={
                "platform": "web",
                "external_id": "uuid-abc",
            })

        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_returns_422_without_platform(self):
        resp = client.post("/api/v1/users/identify", json={"external_id": "uuid"})
        assert resp.status_code == 422

    def test_returns_422_without_external_id(self):
        resp = client.post("/api/v1/users/identify", json={"platform": "web"})
        assert resp.status_code == 422


class TestGetUser:
    def test_returns_user_by_id(self):
        with patch(
            "app.api.v1.users.UserService.get_by_id",
            new=AsyncMock(return_value=SAMPLE_USER),
        ):
            resp = client.get("/api/v1/users/1")

        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_returns_404_when_not_found(self):
        with patch(
            "app.api.v1.users.UserService.get_by_id",
            new=AsyncMock(return_value=None),
        ):
            resp = client.get("/api/v1/users/999")

        assert resp.status_code == 404


class TestUpdatePreferences:
    def test_updates_preferred_city(self):
        with patch(
            "app.api.v1.users.UserService.update_preferences",
            new=AsyncMock(return_value=USER_WITH_CITY),
        ):
            resp = client.patch("/api/v1/users/1/preferences", json={
                "preferred_city_id": 1,
            })

        assert resp.status_code == 200
        assert resp.json()["preferred_city_id"] == 1

    def test_returns_404_when_user_not_found(self):
        with patch(
            "app.api.v1.users.UserService.update_preferences",
            new=AsyncMock(return_value=None),
        ):
            resp = client.patch("/api/v1/users/999/preferences", json={
                "preferred_city_id": 1,
            })

        assert resp.status_code == 404

    def test_accepts_empty_body(self):
        with patch(
            "app.api.v1.users.UserService.update_preferences",
            new=AsyncMock(return_value=SAMPLE_USER),
        ):
            resp = client.patch("/api/v1/users/1/preferences", json={})

        assert resp.status_code == 200
