"""Background scheduler for periodic weather data fetching.

The scheduler runs as an asyncio background task and periodically fetches
weather data for "tracked" cities (cities that were requested in the last 24 hours).
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models import City, RequestLog
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class WeatherScheduler:
    """Background scheduler for weather data fetching."""

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self.is_running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the scheduler background task."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        # Check if scheduler is enabled in config
        scheduler_enabled = settings.app_config.get("scheduler", "enabled", default=True)
        if not scheduler_enabled:
            logger.info("Scheduler is disabled in configuration")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Weather scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler background task."""
        if not self.is_running:
            return

        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Weather scheduler stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop that runs periodically."""
        # Get fetch interval from config (in minutes)
        fetch_interval_minutes = settings.app_config.get(
            "scheduler", "fetch_interval_minutes", default=30
        )
        fetch_interval = timedelta(minutes=fetch_interval_minutes)

        logger.info(f"Scheduler fetch interval: {fetch_interval_minutes} minutes")

        while self.is_running:
            try:
                logger.info("=" * 60)
                logger.info("Scheduler cycle started")
                logger.info("=" * 60)

                await self._fetch_tracked_cities()

                logger.info("=" * 60)
                logger.info(f"Scheduler cycle completed. Next run in {fetch_interval_minutes} minutes")
                logger.info("=" * 60)

                # Wait for next cycle
                await asyncio.sleep(fetch_interval.total_seconds())

            except asyncio.CancelledError:
                logger.info("Scheduler loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                # Wait a bit before retrying to avoid rapid error loops
                await asyncio.sleep(60)

    async def _fetch_tracked_cities(self) -> None:
        """Fetch weather data for all tracked cities.

        Tracked cities are those that were requested in the last 24 hours.
        """
        async with AsyncSessionLocal() as db:
            try:
                # Find cities requested in the last 24 hours
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

                query = (
                    select(City)
                    .join(RequestLog, RequestLog.city_id == City.id)
                    .where(RequestLog.created_at >= cutoff_time)
                    .distinct()
                )

                result = await db.execute(query)
                tracked_cities = result.scalars().all()

                if not tracked_cities:
                    logger.info("No tracked cities found (no requests in last 24 hours)")
                    return

                logger.info(f"Found {len(tracked_cities)} tracked city/cities to update")

                # Fetch weather data for each tracked city
                weather_service = WeatherService(db)

                for city in tracked_cities:
                    try:
                        logger.info(f"Fetching weather data for: {city.name}, {city.country}")
                        await weather_service.fetch_and_save(city.id)
                        logger.info(f"Successfully updated weather for: {city.name}")
                    except Exception as e:
                        logger.error(
                            f"Failed to fetch weather for {city.name} (id={city.id}): {e}",
                            exc_info=True,
                        )
                        # Continue with next city even if one fails
                        continue

                logger.info(f"Completed fetching weather for {len(tracked_cities)} city/cities")

            except Exception as e:
                logger.error(f"Error fetching tracked cities: {e}", exc_info=True)


# Global scheduler instance
scheduler = WeatherScheduler()
