"""Weather data aggregation engine.

Implements weighted averaging for numeric fields and mode selection
for categorical fields based on source priorities.
"""

from collections import Counter
from typing import Any

from app.models.weather import WeatherRecord
from app.schemas.weather import AggregatedWeather


# Fields to aggregate using weighted average
NUMERIC_FIELDS = [
    "temperature",
    "feels_like",
    "wind_speed",
    "wind_direction",
    "humidity",
    "pressure",
    "precipitation_amount",
    "cloudiness",
]

# Fields to aggregate using mode (most frequent value)
CATEGORICAL_FIELDS = [
    "precipitation_type",
    "description",
]

# Fields that are not aggregated but taken from first available source
PASSTHROUGH_FIELDS = [
    "icon_code",
]


def aggregate(
    records: list[WeatherRecord], priorities: dict[int, int]
) -> AggregatedWeather:
    """Aggregate weather data from multiple sources with weighted averaging.

    Args:
        records: List of WeatherRecord objects to aggregate
        priorities: Dictionary mapping source_id to priority value (higher = more important)

    Returns:
        AggregatedWeather object with aggregated values

    Algorithm:
        - Numeric fields: weighted average Σ(value × priority) / Σ(priority)
        - Categorical fields: mode (most frequent), tie-break by highest priority
        - None values are skipped in calculations
    """
    if not records:
        return AggregatedWeather()

    if len(records) == 1:
        # Single source - return its values directly
        return _record_to_aggregated(records[0])

    aggregated_data: dict[str, Any] = {}

    # Aggregate numeric fields using weighted average
    for field in NUMERIC_FIELDS:
        aggregated_data[field] = _weighted_average(records, field, priorities)

    # Aggregate categorical fields using mode
    for field in CATEGORICAL_FIELDS:
        aggregated_data[field] = _mode_with_priority(records, field, priorities)

    # Passthrough fields - take first non-None value
    for field in PASSTHROUGH_FIELDS:
        aggregated_data[field] = _first_non_none(records, field)

    return AggregatedWeather(**aggregated_data)


def _weighted_average(
    records: list[WeatherRecord], field: str, priorities: dict[int, int]
) -> float | int | None:
    """Calculate weighted average for a numeric field.

    Args:
        records: List of weather records
        field: Field name to aggregate
        priorities: Source priorities

    Returns:
        Weighted average value or None if no valid values
    """
    weighted_sum = 0.0
    total_weight = 0.0

    for record in records:
        value = getattr(record, field, None)
        if value is None:
            continue

        priority = priorities.get(record.source_id, 1)
        weighted_sum += value * priority
        total_weight += priority

    if total_weight == 0:
        return None

    result = weighted_sum / total_weight

    # Return integer for fields that should be integers
    if field in ("wind_direction", "humidity", "cloudiness"):
        return round(result)

    return result


def _mode_with_priority(
    records: list[WeatherRecord], field: str, priorities: dict[int, int]
) -> str | None:
    """Select most frequent value (mode) for a categorical field.

    In case of a tie, selects the value from the source with highest priority.

    Args:
        records: List of weather records
        field: Field name to aggregate
        priorities: Source priorities

    Returns:
        Most common value or None if no valid values
    """
    # Collect non-None values with their source priorities
    values_with_priority: list[tuple[str, int, int]] = []

    for record in records:
        value = getattr(record, field, None)
        if value is None:
            continue

        priority = priorities.get(record.source_id, 1)
        values_with_priority.append((value, priority, record.source_id))

    if not values_with_priority:
        return None

    # Count occurrences of each value
    value_counts = Counter(v[0] for v in values_with_priority)

    # Find the maximum frequency
    max_count = max(value_counts.values())

    # Get all values with max frequency
    most_common_values = [v for v, count in value_counts.items() if count == max_count]

    # If only one value has max frequency, return it
    if len(most_common_values) == 1:
        return most_common_values[0]

    # Tie-break: among most common values, select the one with highest priority
    candidates = [
        (value, priority)
        for value, priority, _ in values_with_priority
        if value in most_common_values
    ]

    # Sort by priority (descending) and take the highest
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def _first_non_none(records: list[WeatherRecord], field: str) -> Any:
    """Get first non-None value for a field.

    Args:
        records: List of weather records
        field: Field name

    Returns:
        First non-None value or None
    """
    for record in records:
        value = getattr(record, field, None)
        if value is not None:
            return value
    return None


def _record_to_aggregated(record: WeatherRecord) -> AggregatedWeather:
    """Convert a single WeatherRecord to AggregatedWeather.

    Args:
        record: Weather record to convert

    Returns:
        AggregatedWeather with the same values
    """
    return AggregatedWeather(
        temperature=record.temperature,
        feels_like=record.feels_like,
        wind_speed=record.wind_speed,
        wind_direction=record.wind_direction,
        humidity=record.humidity,
        pressure=record.pressure,
        precipitation_type=record.precipitation_type,
        precipitation_amount=record.precipitation_amount,
        cloudiness=record.cloudiness,
        description=record.description,
        icon_code=record.icon_code,
    )
