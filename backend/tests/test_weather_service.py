"""Unit tests for weather service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import City, WeatherRecord, WeatherSource
from app.schemas.weather import AggregatedWeather
from app.services.weather_service import WeatherService


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Add test data
        city = City(
            id=1,
            name="Moscow",
            local_name="Москва",
            country="RU",
            lat=55.7558,
            lon=37.6173,
        )
        session.add(city)

        source1 = WeatherSource(
            id=1,
            slug="openweathermap",
            display_name="OpenWeatherMap",
            source_type="rest",
            priority=3,
            is_enabled=True,
            config_file="openweathermap.yaml",
        )
        source2 = WeatherSource(
            id=2,
            slug="weatherapi",
            display_name="WeatherAPI",
            source_type="rest",
            priority=2,
            is_enabled=True,
            config_file="weatherapi.yaml",
        )
        session.add(source1)
        session.add(source2)

        await session.commit()

        yield session

    await engine.dispose()


@pytest.fixture
def weather_service(db_session):
    """Create a WeatherService instance for testing."""
    return WeatherService(db_session)


def create_weather_record(
    city_id: int,
    source_id: int,
    record_type: str,
    temperature: float = 20.0,
    fetched_at: datetime | None = None,
    forecast_dt: datetime | None = None,
) -> WeatherRecord:
    """Helper to create a WeatherRecord for testing."""
    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)

    return WeatherRecord(
        city_id=city_id,
        source_id=source_id,
        record_type=record_type,
        forecast_dt=forecast_dt,
        temperature=temperature,
        feels_like=temperature - 2,
        wind_speed=5.0,
        wind_direction=180,
        humidity=60,
        pressure=1013.0,
        precipitation_type="none",
        precipitation_amount=0.0,
        cloudiness=20,
        description="Clear sky",
        icon_code="01d",
        fetched_at=fetched_at,
    )


class TestWeatherService:
    """Test suite for WeatherService."""

    @pytest.mark.asyncio
    async def test_get_aggregated_current_no_data(self, weather_service):
        """Test getting aggregated current weather when no data exists."""
        with patch.object(weather_service, "fetch_and_save", new_callable=AsyncMock) as mock_fetch:
            result = await weather_service.get_aggregated_current(city_id=1)

            # Should trigger fetch since no data exists
            mock_fetch.assert_called_once_with(1)
            assert result is None  # No data after fetch (mocked)

    @pytest.mark.asyncio
    async def test_get_aggregated_current_fresh_data(self, db_session, weather_service):
        """Test getting aggregated current weather with fresh data."""
        # Add fresh weather records
        now = datetime.now(timezone.utc)
        record1 = create_weather_record(
            city_id=1, source_id=1, record_type="current", temperature=20.0, fetched_at=now
        )
        record2 = create_weather_record(
            city_id=1, source_id=2, record_type="current", temperature=22.0, fetched_at=now
        )

        db_session.add(record1)
        db_session.add(record2)
        await db_session.commit()

        # Get aggregated data
        with patch.object(weather_service, "fetch_and_save", new_callable=AsyncMock) as mock_fetch:
            result = await weather_service.get_aggregated_current(city_id=1)

            # Should not trigger fetch since data is fresh
            mock_fetch.assert_not_called()

            # Check aggregated result
            assert isinstance(result, AggregatedWeather)
            assert result.temperature is not None
            # Weighted average: (20*3 + 22*2) / (3+2) = 104/5 = 20.8
            assert result.temperature == pytest.approx(20.8, rel=0.01)

    @pytest.mark.asyncio
    async def test_get_aggregated_current_stale_data(self, db_session, weather_service):
        """Test getting aggregated current weather with stale data."""
        # Add stale weather records (older than 30 minutes)
        stale_time = datetime.now(timezone.utc) - timedelta(minutes=45)
        record = create_weather_record(
            city_id=1, source_id=1, record_type="current", temperature=20.0, fetched_at=stale_time
        )

        db_session.add(record)
        await db_session.commit()

        # Get aggregated data
        with patch.object(weather_service, "fetch_and_save", new_callable=AsyncMock) as mock_fetch:
            result = await weather_service.get_aggregated_current(city_id=1)

            # Should trigger fetch since data is stale
            mock_fetch.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_aggregated_forecast(self, db_session, weather_service):
        """Test getting aggregated forecast data."""
        # Add forecast records
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)

        record1 = create_weather_record(
            city_id=1,
            source_id=1,
            record_type="forecast",
            temperature=18.0,
            fetched_at=now,
            forecast_dt=tomorrow,
        )
        record2 = create_weather_record(
            city_id=1,
            source_id=2,
            record_type="forecast",
            temperature=20.0,
            fetched_at=now,
            forecast_dt=tomorrow,
        )

        db_session.add(record1)
        db_session.add(record2)
        await db_session.commit()

        # Get forecast data
        with patch.object(weather_service, "fetch_and_save", new_callable=AsyncMock):
            result = await weather_service.get_aggregated_forecast(city_id=1, days=5)

            assert isinstance(result, list)
            assert len(result) > 0

            # Check first forecast item
            first_item = result[0]
            assert "forecast_dt" in first_item
            assert "data" in first_item
            assert first_item["data"]["temperature"] == pytest.approx(18.8, rel=0.01)

    @pytest.mark.asyncio
    async def test_get_by_source(self, db_session, weather_service):
        """Test getting weather data grouped by source."""
        # Add records from different sources
        now = datetime.now(timezone.utc)
        record1 = create_weather_record(
            city_id=1, source_id=1, record_type="current", temperature=20.0, fetched_at=now
        )
        record2 = create_weather_record(
            city_id=1, source_id=2, record_type="current", temperature=22.0, fetched_at=now
        )

        db_session.add(record1)
        db_session.add(record2)
        await db_session.commit()

        # Get by source
        result = await weather_service.get_by_source(city_id=1)

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "openweathermap" in result
        assert "weatherapi" in result

        # Check structure
        owm_data = result["openweathermap"]
        assert owm_data["source_name"] == "OpenWeatherMap"
        assert owm_data["priority"] == 3
        assert owm_data["data"]["temperature"] == 20.0

    @pytest.mark.asyncio
    async def test_get_chart_hourly(self, db_session, weather_service):
        """Test getting hourly chart data."""
        # Add hourly forecast records
        now = datetime.now(timezone.utc)

        for hour in range(24):
            forecast_time = now + timedelta(hours=hour)
            record = create_weather_record(
                city_id=1,
                source_id=1,
                record_type="forecast",
                temperature=20.0 + hour * 0.5,
                fetched_at=now,
                forecast_dt=forecast_time,
            )
            db_session.add(record)

        await db_session.commit()

        # Get hourly data
        result = await weather_service.get_chart_hourly(city_id=1)

        assert isinstance(result, list)
        assert len(result) > 0

        # Check structure
        first_hour = result[0]
        assert "hour" in first_hour
        assert "temperature" in first_hour
        assert "feels_like" in first_hour
        assert "precipitation_amount" in first_hour
        assert "wind_speed" in first_hour
        assert "humidity" in first_hour

    @pytest.mark.asyncio
    async def test_get_chart_daily(self, db_session, weather_service):
        """Test getting daily chart data with min/max temperatures."""
        # Add daily forecast records with varying temperatures
        now = datetime.now(timezone.utc)

        for day in range(5):
            for hour in range(0, 24, 3):  # Every 3 hours
                forecast_time = now + timedelta(days=day, hours=hour)
                # Simulate temperature variation throughout the day
                temp = 15.0 + day * 2 + (hour / 24) * 10  # Day avg increases, varies within day
                record = create_weather_record(
                    city_id=1,
                    source_id=1,
                    record_type="forecast",
                    temperature=temp,
                    fetched_at=now,
                    forecast_dt=forecast_time,
                )
                db_session.add(record)

        await db_session.commit()

        # Get daily data
        result = await weather_service.get_chart_daily(city_id=1, days=5)

        assert isinstance(result, list)
        assert len(result) > 0

        # Check structure
        first_day = result[0]
        assert "date" in first_day
        assert "temp_min" in first_day
        assert "temp_max" in first_day
        assert "temp_avg" in first_day

        # Check that min < avg < max
        assert first_day["temp_min"] <= first_day["temp_avg"] <= first_day["temp_max"]

    @pytest.mark.asyncio
    async def test_get_source_priorities(self, weather_service):
        """Test getting source priorities."""
        priorities = await weather_service._get_source_priorities()

        assert isinstance(priorities, dict)
        assert len(priorities) == 2
        assert priorities[1] == 3  # OpenWeatherMap
        assert priorities[2] == 2  # WeatherAPI

    @pytest.mark.asyncio
    async def test_get_source_priorities_filtered(self, weather_service):
        """Test getting source priorities with filtering."""
        priorities = await weather_service._get_source_priorities(
            source_slugs=["openweathermap"]
        )

        assert isinstance(priorities, dict)
        assert len(priorities) == 1
        assert priorities[1] == 3

    @pytest.mark.asyncio
    async def test_is_data_stale_no_data(self, weather_service):
        """Test checking if data is stale when no data exists."""
        is_stale = await weather_service._is_data_stale(city_id=1, record_type="current")
        assert is_stale is True

    @pytest.mark.asyncio
    async def test_is_data_stale_fresh_data(self, db_session, weather_service):
        """Test checking if data is stale with fresh data."""
        # Add fresh record
        now = datetime.now(timezone.utc)
        record = create_weather_record(
            city_id=1, source_id=1, record_type="current", fetched_at=now
        )
        db_session.add(record)
        await db_session.commit()

        is_stale = await weather_service._is_data_stale(city_id=1, record_type="current")
        assert is_stale is False

    @pytest.mark.asyncio
    async def test_is_data_stale_old_data(self, db_session, weather_service):
        """Test checking if data is stale with old data."""
        # Add old record (45 minutes ago)
        old_time = datetime.now(timezone.utc) - timedelta(minutes=45)
        record = create_weather_record(
            city_id=1, source_id=1, record_type="current", fetched_at=old_time
        )
        db_session.add(record)
        await db_session.commit()

        is_stale = await weather_service._is_data_stale(city_id=1, record_type="current")
        assert is_stale is True

    @pytest.mark.asyncio
    async def test_fetch_and_save(self, db_session, weather_service):
        """Test fetching and saving weather data."""
        # Mock fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.get_name.return_value = "OpenWeatherMap"
        mock_fetcher.fetch_current = AsyncMock(
            return_value={
                "temperature": 20.0,
                "feels_like": 18.0,
                "wind_speed": 5.0,
                "wind_direction": 180,
                "humidity": 60,
                "pressure": 1013.0,
                "precipitation_type": "none",
                "precipitation_amount": 0.0,
                "cloudiness": 20,
                "description": "Clear sky",
                "icon_code": "01d",
            }
        )
        mock_fetcher.fetch_forecast = AsyncMock(
            return_value=[
                {
                    "temperature": 22.0,
                    "feels_like": 20.0,
                    "wind_speed": 4.0,
                    "wind_direction": 170,
                    "humidity": 55,
                    "pressure": 1015.0,
                    "precipitation_type": "none",
                    "precipitation_amount": 0.0,
                    "cloudiness": 10,
                    "description": "Clear sky",
                    "icon_code": "01d",
                    "forecast_time": int(datetime.now(timezone.utc).timestamp()),
                }
            ]
        )

        with patch(
            "app.services.weather_service.load_fetchers_from_config_dir",
            return_value=[mock_fetcher],
        ):
            with patch("app.services.weather_service.register_all_fetchers"):
                await weather_service.fetch_and_save(city_id=1)

        # Check that records were saved
        query = select(WeatherRecord).where(WeatherRecord.city_id == 1)
        result = await db_session.execute(query)
        records = result.scalars().all()

        assert len(records) > 0

        # Check current record
        current_records = [r for r in records if r.record_type == "current"]
        assert len(current_records) == 1
        assert current_records[0].temperature == 20.0

        # Check forecast records
        forecast_records = [r for r in records if r.record_type == "forecast"]
        assert len(forecast_records) == 1
        assert forecast_records[0].temperature == 22.0
