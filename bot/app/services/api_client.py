"""HTTP client for the weather aggregator backend API."""

import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class BackendAPIClient:
    """Async HTTP client wrapping the backend REST API.

    Uses a shared aiohttp.ClientSession for connection pooling.
    Call close() when shutting down.
    """

    def __init__(self, base_url: str, timeout: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def _session_get(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get(self, path: str, params: dict | None = None) -> Any | None:
        session = await self._session_get()
        url = f"{self.base_url}{path}"
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("GET %s → %d", url, resp.status)
                return None
        except Exception as exc:
            logger.error("GET %s failed: %s", url, exc)
            return None

    async def _post(self, path: str, json: dict | None = None) -> Any | None:
        session = await self._session_get()
        url = f"{self.base_url}{path}"
        try:
            async with session.post(url, json=json) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                logger.warning("POST %s → %d", url, resp.status)
                return None
        except Exception as exc:
            logger.error("POST %s failed: %s", url, exc)
            return None

    async def _patch(self, path: str, json: dict | None = None) -> Any | None:
        session = await self._session_get()
        url = f"{self.base_url}{path}"
        try:
            async with session.patch(url, json=json) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning("PATCH %s → %d", url, resp.status)
                return None
        except Exception as exc:
            logger.error("PATCH %s failed: %s", url, exc)
            return None

    # ------------------------------------------------------------------ #
    # Public API methods
    # ------------------------------------------------------------------ #

    async def get_current_weather(
        self,
        city_id: int,
        sources: list[str] | None = None,
    ) -> dict | None:
        """GET /api/v1/weather/current"""
        params: dict = {"city_id": city_id}
        if sources:
            params["sources"] = sources
        return await self._get("/api/v1/weather/current", params)

    async def get_forecast(
        self,
        city_id: int,
        days: int = 5,
        sources: list[str] | None = None,
    ) -> dict | None:
        """GET /api/v1/weather/forecast"""
        params: dict = {"city_id": city_id, "days": days}
        if sources:
            params["sources"] = sources
        return await self._get("/api/v1/weather/forecast", params)

    async def search_cities(self, query: str, limit: int = 5) -> list[dict]:
        """GET /api/v1/cities/search"""
        result = await self._get("/api/v1/cities/search", {"q": query, "limit": limit})
        return result if isinstance(result, list) else []

    async def identify_user(self, platform: str, external_id: str) -> dict | None:
        """POST /api/v1/users/identify"""
        return await self._post(
            "/api/v1/users/identify",
            {"platform": platform, "external_id": external_id},
        )

    async def update_preferences(
        self,
        user_id: int,
        preferred_city_id: int | None = None,
        settings_json: dict | None = None,
    ) -> dict | None:
        """PATCH /api/v1/users/{user_id}/preferences"""
        body: dict = {}
        if preferred_city_id is not None:
            body["preferred_city_id"] = preferred_city_id
        if settings_json is not None:
            body["settings_json"] = settings_json
        return await self._patch(f"/api/v1/users/{user_id}/preferences", body)

    async def get_recommendation(self, city_id: int) -> dict | None:
        """GET /api/v1/weather/recommendation (ML endpoint, may not exist yet)"""
        return await self._get("/api/v1/weather/recommendation", {"city_id": city_id})

    async def get_sources(self) -> list[dict]:
        """GET /api/v1/sources"""
        result = await self._get("/api/v1/sources")
        return result if isinstance(result, list) else []
