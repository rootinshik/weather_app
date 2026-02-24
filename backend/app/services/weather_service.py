"""Weather service for fetching, aggregating, and managing weather data.

Provides methods for:
- Getting aggregated weather data (current and forecast)
- On-demand data fetching when data is stale
- Chart data generation (hourly and daily)
- Per-source data retrieval
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.aggregator.engine import aggregate
from app.fetchers.factory import FetcherFactory, load_fetchers_from_config_dir
from app.fetchers.registry import register_all_fetchers
from app.models import City, WeatherRecord, WeatherSource
from app.schemas.weather import AggregatedWeather

logger = logging.getLogger(__name__)

# Data is considered stale after 30 minutes
STALE_DATA_THRESHOLD = timedelta(minutes=30)


class WeatherService:
    """Service for managing weather data operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize weather service with database session.

        Args:
            db: SQLAlchemy async database session
        """
        self.db = db

    async def get_aggregated_current(
        self, city_id: int, source_slugs: list[str] | None = None
    ) -> AggregatedWeather | None:
        """Get aggregated current weather data for a city.

        If data is stale (>30 minutes old), triggers on-demand fetch.

        Args:
            city_id: ID of the city
            source_slugs: Optional list of source slugs to filter by

        Returns:
            Aggregated weather data or None if no data available
        """
        # Check if data is stale and fetch if needed
        needs_fetch = await self._is_data_stale(city_id, "current")
        if needs_fetch:
            logger.info(f"Data for city {city_id} is stale, triggering on-demand fetch")
            await self.fetch_and_save(city_id)

        # Get current weather records
        records = await self._get_records(city_id, "current", source_slugs)

        if not records:
            logger.warning(f"No current weather data found for city {city_id}")
            return None

        # Get priorities for aggregation
        priorities = await self._get_source_priorities(source_slugs)

        # Aggregate the records
        aggregated = aggregate(records, priorities)
        return aggregated

    async def get_aggregated_forecast(
        self,
        city_id: int,
        days: int = 5,
        source_slugs: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get aggregated weather forecast for a city.

        Args:
            city_id: ID of the city
            days: Number of days to forecast
            source_slugs: Optional list of source slugs to filter by

        Returns:
            List of aggregated forecast data grouped by datetime
        """
        # Check if data is stale and fetch if needed
        needs_fetch = await self._is_data_stale(city_id, "forecast")
        if needs_fetch:
            logger.info(f"Forecast for city {city_id} is stale, triggering on-demand fetch")
            await self.fetch_and_save(city_id)

        # Get forecast records
        records = await self._get_records(city_id, "forecast", source_slugs)

        if not records:
            logger.warning(f"No forecast data found for city {city_id}")
            return []

        # Group records by forecast_dt and aggregate each group
        forecast_groups: dict[datetime, list[WeatherRecord]] = {}
        for record in records:
            if record.forecast_dt:
                forecast_groups.setdefault(record.forecast_dt, []).append(record)

        # Get priorities for aggregation
        priorities = await self._get_source_priorities(source_slugs)

        # Aggregate each group
        result = []
        for forecast_dt, group_records in sorted(forecast_groups.items()):
            if len(result) >= days * 8:  # Approximate: 3-hour intervals
                break

            aggregated = aggregate(group_records, priorities)
            result.append({
                "forecast_dt": forecast_dt,
                "data": aggregated.model_dump(),
            })

        return result

    async def get_by_source(self, city_id: int) -> dict[str, dict[str, Any]]:
        """Get weather data grouped by source (non-aggregated).

        Args:
            city_id: ID of the city

        Returns:
            Dictionary mapping source name to weather data
        """
        # Get all current weather records for the city
        query = (
            select(WeatherRecord, WeatherSource)
            .join(WeatherSource, WeatherRecord.source_id == WeatherSource.id)
            .where(WeatherRecord.city_id == city_id)
            .where(WeatherRecord.record_type == "current")
            .order_by(WeatherRecord.fetched_at.desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Group by source
        by_source: dict[str, dict[str, Any]] = {}
        for record, source in rows:
            if source.slug not in by_source:
                by_source[source.slug] = {
                    "source_name": source.display_name,
                    "priority": source.priority,
                    "fetched_at": record.fetched_at,
                    "data": {
                        "temperature": record.temperature,
                        "feels_like": record.feels_like,
                        "wind_speed": record.wind_speed,
                        "wind_direction": record.wind_direction,
                        "humidity": record.humidity,
                        "pressure": record.pressure,
                        "precipitation_type": record.precipitation_type,
                        "precipitation_amount": record.precipitation_amount,
                        "cloudiness": record.cloudiness,
                        "description": record.description,
                        "icon_code": record.icon_code,
                    },
                }

        return by_source

    async def get_chart_hourly(self, city_id: int) -> list[dict[str, Any]]:
        """Get hourly weather data for charts (next 24 hours).

        Args:
            city_id: ID of the city

        Returns:
            List of 24 hourly data points with aggregated values
        """
        # Get forecast records for next 24 hours
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(hours=24)

        query = (
            select(WeatherRecord)
            .where(WeatherRecord.city_id == city_id)
            .where(WeatherRecord.record_type == "forecast")
            .where(WeatherRecord.forecast_dt.isnot(None))
            .where(WeatherRecord.forecast_dt >= now)
            .where(WeatherRecord.forecast_dt <= end_time)
            .order_by(WeatherRecord.forecast_dt)
        )

        result = await self.db.execute(query)
        records = result.scalars().all()

        if not records:
            return []

        # Group by hour and aggregate
        hourly_groups: dict[datetime, list[WeatherRecord]] = {}
        for record in records:
            if record.forecast_dt:
                # Round to nearest hour
                hour_key = record.forecast_dt.replace(minute=0, second=0, microsecond=0)
                hourly_groups.setdefault(hour_key, []).append(record)

        # Get priorities
        priorities = await self._get_source_priorities(None)

        # Aggregate each hour
        result_list = []
        for hour, group_records in sorted(hourly_groups.items())[:24]:
            aggregated = aggregate(group_records, priorities)
            result_list.append({
                "hour": hour,
                "temperature": aggregated.temperature,
                "feels_like": aggregated.feels_like,
                "precipitation_amount": aggregated.precipitation_amount,
                "wind_speed": aggregated.wind_speed,
                "humidity": aggregated.humidity,
            })

        return result_list

    async def get_chart_daily(self, city_id: int, days: int = 7) -> list[dict[str, Any]]:
        """Get daily weather data for charts with min/max temperatures.

        Args:
            city_id: ID of the city
            days: Number of days to retrieve

        Returns:
            List of daily data points with min/max temperatures
        """
        # Get forecast records for next N days
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(days=days)

        query = (
            select(WeatherRecord)
            .where(WeatherRecord.city_id == city_id)
            .where(WeatherRecord.record_type == "forecast")
            .where(WeatherRecord.forecast_dt.isnot(None))
            .where(WeatherRecord.forecast_dt >= now)
            .where(WeatherRecord.forecast_dt <= end_time)
            .order_by(WeatherRecord.forecast_dt)
        )

        result = await self.db.execute(query)
        records = result.scalars().all()

        if not records:
            return []

        # Group by day
        daily_groups: dict[str, list[WeatherRecord]] = {}
        for record in records:
            if record.forecast_dt and record.temperature is not None:
                day_key = record.forecast_dt.date().isoformat()
                daily_groups.setdefault(day_key, []).append(record)

        # Calculate min/max for each day
        result_list = []
        for day, group_records in sorted(daily_groups.items())[:days]:
            temperatures = [
                r.temperature for r in group_records if r.temperature is not None
            ]

            if temperatures:
                result_list.append({
                    "date": day,
                    "temp_min": min(temperatures),
                    "temp_max": max(temperatures),
                    "temp_avg": sum(temperatures) / len(temperatures),
                })

        return result_list

    async def fetch_and_save(self, city_id: int) -> None:
        """Fetch weather data from all sources and save to database.

        This is the on-demand fetch function that gets triggered when data is stale.

        Args:
            city_id: ID of the city to fetch data for
        """
        # Get city from database
        city_query = select(City).where(City.id == city_id)
        city_result = await self.db.execute(city_query)
        city = city_result.scalar_one_or_none()

        if not city:
            logger.error(f"City with id {city_id} not found")
            return

        # Get all weather sources
        sources_query = select(WeatherSource).where(WeatherSource.is_enabled == True)
        sources_result = await self.db.execute(sources_query)
        sources = sources_result.scalars().all()

        if not sources:
            logger.warning("No enabled weather sources found")
            return

        # Ensure fetchers are registered
        register_all_fetchers()

        # Load fetchers
        try:
            fetchers = load_fetchers_from_config_dir()
        except Exception as e:
            logger.error(f"Failed to load fetchers: {e}")
            return

        # Fetch data from each source
        for fetcher in fetchers:
            try:
                # Find corresponding source in database
                source = next(
                    (s for s in sources if s.display_name == fetcher.get_name()),
                    None
                )

                if not source:
                    logger.warning(f"Source not found in database: {fetcher.get_name()}")
                    continue

                # Fetch current weather
                logger.info(f"Fetching current weather for {city.name} from {fetcher.get_name()}")
                current_data = await fetcher.fetch_current(city.name)

                if current_data:
                    # Save current weather to database
                    current_record = WeatherRecord(
                        city_id=city.id,
                        source_id=source.id,
                        record_type="current",
                        forecast_dt=None,
                        temperature=current_data.get("temperature"),
                        feels_like=current_data.get("feels_like"),
                        wind_speed=current_data.get("wind_speed"),
                        wind_direction=current_data.get("wind_direction"),
                        humidity=current_data.get("humidity"),
                        pressure=current_data.get("pressure"),
                        precipitation_type=current_data.get("precipitation_type"),
                        precipitation_amount=current_data.get("precipitation_amount"),
                        cloudiness=current_data.get("cloudiness"),
                        description=current_data.get("description"),
                        icon_code=current_data.get("icon_code"),
                    )
                    self.db.add(current_record)

                # Fetch forecast
                logger.info(f"Fetching forecast for {city.name} from {fetcher.get_name()}")
                forecast_data = await fetcher.fetch_forecast(city.name, days=5)

                if forecast_data:
                    for forecast_item in forecast_data:
                        # Convert forecast_time (Unix timestamp) to datetime
                        forecast_dt = None
                        if "forecast_time" in forecast_item:
                            forecast_dt = datetime.fromtimestamp(
                                forecast_item["forecast_time"], tz=timezone.utc
                            )

                        forecast_record = WeatherRecord(
                            city_id=city.id,
                            source_id=source.id,
                            record_type="forecast",
                            forecast_dt=forecast_dt,
                            temperature=forecast_item.get("temperature"),
                            feels_like=forecast_item.get("feels_like"),
                            wind_speed=forecast_item.get("wind_speed"),
                            wind_direction=forecast_item.get("wind_direction"),
                            humidity=forecast_item.get("humidity"),
                            pressure=forecast_item.get("pressure"),
                            precipitation_type=forecast_item.get("precipitation_type"),
                            precipitation_amount=forecast_item.get("precipitation_amount"),
                            cloudiness=forecast_item.get("cloudiness"),
                            description=forecast_item.get("description"),
                            icon_code=forecast_item.get("icon_code"),
                        )
                        self.db.add(forecast_record)

                await self.db.commit()
                logger.info(f"Successfully saved weather data for {city.name} from {fetcher.get_name()}")

            except Exception as e:
                logger.error(f"Failed to fetch data from {fetcher.get_name()}: {e}")
                await self.db.rollback()
                continue

    async def _is_data_stale(self, city_id: int, record_type: str) -> bool:
        """Check if weather data for a city is stale.

        Args:
            city_id: ID of the city
            record_type: Type of record ("current" or "forecast")

        Returns:
            True if data is stale or missing, False otherwise
        """
        query = (
            select(WeatherRecord.fetched_at)
            .where(WeatherRecord.city_id == city_id)
            .where(WeatherRecord.record_type == record_type)
            .order_by(WeatherRecord.fetched_at.desc())
            .limit(1)
        )

        result = await self.db.execute(query)
        latest_fetch = result.scalar_one_or_none()

        if not latest_fetch:
            return True

        # Check if data is older than threshold
        now = datetime.now(timezone.utc)
        # Make latest_fetch timezone-aware if it's naive
        if latest_fetch.tzinfo is None:
            latest_fetch = latest_fetch.replace(tzinfo=timezone.utc)

        return (now - latest_fetch) > STALE_DATA_THRESHOLD

    async def _get_records(
        self,
        city_id: int,
        record_type: str,
        source_slugs: list[str] | None = None,
    ) -> list[WeatherRecord]:
        """Get weather records from database.

        Args:
            city_id: ID of the city
            record_type: Type of record ("current" or "forecast")
            source_slugs: Optional list of source slugs to filter by

        Returns:
            List of weather records
        """
        query = (
            select(WeatherRecord)
            .where(WeatherRecord.city_id == city_id)
            .where(WeatherRecord.record_type == record_type)
        )

        # Filter by source slugs if provided
        if source_slugs:
            source_ids_query = select(WeatherSource.id).where(
                WeatherSource.slug.in_(source_slugs)
            )
            source_ids_result = await self.db.execute(source_ids_query)
            source_ids = [row[0] for row in source_ids_result.all()]

            if source_ids:
                query = query.where(WeatherRecord.source_id.in_(source_ids))
            else:
                return []

        # Get most recent records (within stale threshold)
        cutoff_time = datetime.now(timezone.utc) - STALE_DATA_THRESHOLD
        query = query.where(WeatherRecord.fetched_at >= cutoff_time)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_source_priorities(
        self, source_slugs: list[str] | None = None
    ) -> dict[int, int]:
        """Get source priorities for aggregation.

        Args:
            source_slugs: Optional list of source slugs to filter by

        Returns:
            Dictionary mapping source_id to priority value
        """
        query = select(WeatherSource.id, WeatherSource.priority).where(
            WeatherSource.is_enabled == True
        )

        if source_slugs:
            query = query.where(WeatherSource.slug.in_(source_slugs))

        result = await self.db.execute(query)
        return {source_id: priority for source_id, priority in result.all()}
