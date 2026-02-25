"""City service: geocoding search and database operations."""

import logging

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.schemas.city import CityCreate, CitySearchResult

logger = logging.getLogger(__name__)

OWM_GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"


class CityService:
    """Service for city search and management."""

    def __init__(self, db: AsyncSession, owm_api_key: str) -> None:
        self.db = db
        self.owm_api_key = owm_api_key

    async def search(self, query: str, limit: int = 5) -> list[CitySearchResult]:
        """Search cities via OpenWeatherMap Geocoding API.

        Args:
            query: City name to search for
            limit: Maximum number of results (1-5)

        Returns:
            List of city search results (not saved to DB)
        """
        if not self.owm_api_key:
            logger.warning("OWM_API_KEY is not set; geocoding search unavailable")
            return []

        params = {"q": query, "limit": limit, "appid": self.owm_api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    OWM_GEOCODING_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        logger.error("OWM geocoding error: status %d", resp.status)
                        return []
                    data: list[dict] = await resp.json()
        except Exception as exc:
            logger.error("OWM geocoding request failed: %s", exc)
            return []

        results = []
        for item in data:
            local_names: dict = item.get("local_names", {})
            local_name = local_names.get("ru") or local_names.get("en")
            results.append(
                CitySearchResult(
                    name=item["name"],
                    local_name=local_name,
                    country=item.get("country", ""),
                    lat=item["lat"],
                    lon=item["lon"],
                )
            )
        return results

    async def get_by_id(self, city_id: int) -> City | None:
        """Get a city by its database ID."""
        result = await self.db.execute(select(City).where(City.id == city_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, data: CityCreate) -> City:
        """Get an existing city or create a new one.

        Matches by (name, country) pair. If a match is found, returns it
        without updating coordinates. Otherwise inserts a new record.

        Args:
            data: City data to look up or create

        Returns:
            Existing or newly created City ORM instance
        """
        result = await self.db.execute(
            select(City).where(City.name == data.name, City.country == data.country)
        )
        city = result.scalar_one_or_none()

        if city:
            return city

        city = City(
            name=data.name,
            local_name=data.local_name,
            country=data.country,
            lat=data.lat,
            lon=data.lon,
        )
        self.db.add(city)
        await self.db.commit()
        await self.db.refresh(city)
        return city
