"""Unit tests for weather data aggregation engine."""

from datetime import datetime

import pytest

from app.aggregator.engine import aggregate
from app.models.weather import WeatherRecord
from app.schemas.weather import AggregatedWeather


@pytest.fixture
def source_priorities():
    """Mock source priorities for testing."""
    return {
        1: 3,  # Source 1 has priority 3 (highest)
        2: 2,  # Source 2 has priority 2
        3: 1,  # Source 3 has priority 1 (lowest)
    }


def create_weather_record(
    source_id: int,
    temperature: float | None = None,
    feels_like: float | None = None,
    wind_speed: float | None = None,
    wind_direction: int | None = None,
    humidity: int | None = None,
    pressure: float | None = None,
    precipitation_type: str | None = None,
    precipitation_amount: float | None = None,
    cloudiness: int | None = None,
    description: str | None = None,
    icon_code: str | None = None,
) -> WeatherRecord:
    """Helper to create a WeatherRecord for testing."""
    record = WeatherRecord()
    record.id = source_id
    record.city_id = 1
    record.source_id = source_id
    record.record_type = "current"
    record.temperature = temperature
    record.feels_like = feels_like
    record.wind_speed = wind_speed
    record.wind_direction = wind_direction
    record.humidity = humidity
    record.pressure = pressure
    record.precipitation_type = precipitation_type
    record.precipitation_amount = precipitation_amount
    record.cloudiness = cloudiness
    record.description = description
    record.icon_code = icon_code
    record.fetched_at = datetime.now()
    return record


class TestAggregationEngine:
    """Test suite for weather data aggregation engine."""

    def test_empty_records_list(self):
        """Test aggregation with empty records list."""
        result = aggregate([], {})

        assert isinstance(result, AggregatedWeather)
        assert result.temperature is None
        assert result.description is None

    def test_single_source(self):
        """Test that single source returns its values unchanged."""
        record = create_weather_record(
            source_id=1,
            temperature=15.5,
            feels_like=14.2,
            wind_speed=5.5,
            wind_direction=270,
            humidity=65,
            pressure=1013.25,
            precipitation_type="none",
            precipitation_amount=0.0,
            cloudiness=40,
            description="Partly cloudy",
            icon_code="02d",
        )

        result = aggregate([record], {1: 3})

        assert result.temperature == 15.5
        assert result.feels_like == 14.2
        assert result.wind_speed == 5.5
        assert result.wind_direction == 270
        assert result.humidity == 65
        assert result.pressure == 1013.25
        assert result.precipitation_type == "none"
        assert result.precipitation_amount == 0.0
        assert result.cloudiness == 40
        assert result.description == "Partly cloudy"
        assert result.icon_code == "02d"

    def test_weighted_average_two_sources(self, source_priorities):
        """Test weighted average calculation for two sources."""
        # Source 1 (priority 3): temp 20°C
        # Source 2 (priority 2): temp 10°C
        # Expected: (20*3 + 10*2) / (3+2) = 80/5 = 16°C
        record1 = create_weather_record(source_id=1, temperature=20.0)
        record2 = create_weather_record(source_id=2, temperature=10.0)

        result = aggregate([record1, record2], source_priorities)

        assert result.temperature == 16.0

    def test_weighted_average_three_sources(self, source_priorities):
        """Test weighted average calculation for three sources."""
        # Source 1 (priority 3): temp 18°C
        # Source 2 (priority 2): temp 15°C
        # Source 3 (priority 1): temp 12°C
        # Expected: (18*3 + 15*2 + 12*1) / (3+2+1) = 96/6 = 16°C
        record1 = create_weather_record(source_id=1, temperature=18.0)
        record2 = create_weather_record(source_id=2, temperature=15.0)
        record3 = create_weather_record(source_id=3, temperature=12.0)

        result = aggregate([record1, record2, record3], source_priorities)

        assert result.temperature == 16.0

    def test_weighted_average_multiple_fields(self, source_priorities):
        """Test weighted average for multiple numeric fields."""
        record1 = create_weather_record(
            source_id=1,
            temperature=20.0,
            wind_speed=10.0,
            pressure=1020.0,
            humidity=80,
        )
        record2 = create_weather_record(
            source_id=2,
            temperature=10.0,
            wind_speed=5.0,
            pressure=1000.0,
            humidity=60,
        )

        result = aggregate([record1, record2], source_priorities)

        # Temperature: (20*3 + 10*2) / 5 = 16
        assert result.temperature == 16.0
        # Wind speed: (10*3 + 5*2) / 5 = 8
        assert result.wind_speed == 8.0
        # Pressure: (1020*3 + 1000*2) / 5 = 1012
        assert result.pressure == 1012.0
        # Humidity (integer): (80*3 + 60*2) / 5 = 72 (rounded)
        assert result.humidity == 72

    def test_none_values_skipped_in_weighted_average(self, source_priorities):
        """Test that None values are properly skipped in calculations."""
        # Source 1 (priority 3): temp 20°C
        # Source 2 (priority 2): temp None (should be skipped)
        # Source 3 (priority 1): temp 10°C
        # Expected: (20*3 + 10*1) / (3+1) = 70/4 = 17.5°C
        record1 = create_weather_record(source_id=1, temperature=20.0)
        record2 = create_weather_record(source_id=2, temperature=None)
        record3 = create_weather_record(source_id=3, temperature=10.0)

        result = aggregate([record1, record2, record3], source_priorities)

        assert result.temperature == 17.5

    def test_all_none_values_returns_none(self, source_priorities):
        """Test that all None values result in None."""
        record1 = create_weather_record(source_id=1, temperature=None)
        record2 = create_weather_record(source_id=2, temperature=None)

        result = aggregate([record1, record2], source_priorities)

        assert result.temperature is None

    def test_mode_for_categorical_field(self, source_priorities):
        """Test mode selection for categorical fields."""
        # "rain" appears twice, should be selected
        record1 = create_weather_record(source_id=1, precipitation_type="rain")
        record2 = create_weather_record(source_id=2, precipitation_type="rain")
        record3 = create_weather_record(source_id=3, precipitation_type="snow")

        result = aggregate([record1, record2, record3], source_priorities)

        assert result.precipitation_type == "rain"

    def test_mode_tie_break_by_priority(self, source_priorities):
        """Test mode tie-break: select value from source with highest priority."""
        # Both "rain" and "snow" appear once each
        # Source 1 (priority 3) says "rain"
        # Source 2 (priority 2) says "snow"
        # Should select "rain" because source 1 has higher priority
        record1 = create_weather_record(source_id=1, precipitation_type="rain")
        record2 = create_weather_record(source_id=2, precipitation_type="snow")

        result = aggregate([record1, record2], source_priorities)

        assert result.precipitation_type == "rain"

    def test_mode_multiple_descriptions(self, source_priorities):
        """Test mode for description field."""
        # "Cloudy" appears twice, should be selected
        record1 = create_weather_record(source_id=1, description="Cloudy")
        record2 = create_weather_record(source_id=2, description="Cloudy")
        record3 = create_weather_record(source_id=3, description="Clear")

        result = aggregate([record1, record2, record3], source_priorities)

        assert result.description == "Cloudy"

    def test_mode_with_none_values(self, source_priorities):
        """Test mode with None values (should be skipped)."""
        # Source 1: "rain"
        # Source 2: None (skipped)
        # Source 3: "snow"
        # Both "rain" and "snow" appear once, tie-break by priority
        record1 = create_weather_record(source_id=1, precipitation_type="rain")
        record2 = create_weather_record(source_id=2, precipitation_type=None)
        record3 = create_weather_record(source_id=3, precipitation_type="snow")

        result = aggregate([record1, record2, record3], source_priorities)

        assert result.precipitation_type == "rain"

    def test_icon_code_passthrough(self, source_priorities):
        """Test that icon_code takes first non-None value."""
        record1 = create_weather_record(source_id=1, icon_code=None)
        record2 = create_weather_record(source_id=2, icon_code="02d")
        record3 = create_weather_record(source_id=3, icon_code="03d")

        result = aggregate([record1, record2, record3], source_priorities)

        # Should take the first non-None value (02d from source 2)
        assert result.icon_code == "02d"

    def test_integer_rounding_for_integer_fields(self, source_priorities):
        """Test that integer fields are properly rounded."""
        # Wind direction should be rounded to integer
        # (270*3 + 260*2) / 5 = 1330/5 = 266
        record1 = create_weather_record(source_id=1, wind_direction=270)
        record2 = create_weather_record(source_id=2, wind_direction=260)

        result = aggregate([record1, record2], source_priorities)

        assert isinstance(result.wind_direction, int)
        assert result.wind_direction == 266

    def test_comprehensive_aggregation(self, source_priorities):
        """Test comprehensive aggregation with mixed data."""
        record1 = create_weather_record(
            source_id=1,
            temperature=20.0,
            feels_like=18.0,
            wind_speed=8.0,
            wind_direction=270,
            humidity=70,
            pressure=1015.0,
            precipitation_type="none",
            precipitation_amount=0.0,
            cloudiness=30,
            description="Clear",
            icon_code="01d",
        )
        record2 = create_weather_record(
            source_id=2,
            temperature=18.0,
            feels_like=16.0,
            wind_speed=6.0,
            wind_direction=260,
            humidity=65,
            pressure=1013.0,
            precipitation_type="none",
            precipitation_amount=0.0,
            cloudiness=40,
            description="Clear",
            icon_code="02d",
        )
        record3 = create_weather_record(
            source_id=3,
            temperature=16.0,
            feels_like=14.0,
            wind_speed=5.0,
            wind_direction=250,
            humidity=60,
            pressure=1010.0,
            precipitation_type="rain",
            precipitation_amount=1.5,
            cloudiness=50,
            description="Rainy",
            icon_code="10d",
        )

        result = aggregate([record1, record2, record3], source_priorities)

        # Numeric fields: weighted average
        # Temperature: (20*3 + 18*2 + 16*1) / 6 = 112/6 ≈ 18.67
        assert abs(result.temperature - 18.666666666666668) < 0.01
        # Feels like: (18*3 + 16*2 + 14*1) / 6 = 100/6 ≈ 16.67
        assert abs(result.feels_like - 16.666666666666668) < 0.01
        # Humidity: (70*3 + 65*2 + 60*1) / 6 = 410/6 ≈ 68 (rounded)
        assert result.humidity == 67

        # Categorical fields: mode (with tie-break)
        # "none" appears twice, "rain" once -> "none"
        assert result.precipitation_type == "none"
        # "Clear" appears twice, "Rainy" once -> "Clear"
        assert result.description == "Clear"

        # Passthrough: first non-None
        assert result.icon_code == "01d"

    def test_default_priority_when_not_specified(self):
        """Test that missing priorities default to 1."""
        record1 = create_weather_record(source_id=1, temperature=20.0)
        record2 = create_weather_record(source_id=2, temperature=10.0)

        # Empty priorities dict - should default to 1 for both
        result = aggregate([record1, record2], {})

        # Expected: (20*1 + 10*1) / 2 = 15.0
        assert result.temperature == 15.0
