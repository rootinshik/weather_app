"""Base abstract class for weather data fetchers."""

from abc import ABC, abstractmethod
from typing import Any


class AbstractWeatherFetcher(ABC):
    """Abstract base class for all weather data fetchers.

    Defines the contract that all concrete fetcher implementations must follow.
    Supports both API-based and parser-based (HTML scraping) data sources.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize fetcher with configuration dictionary.

        Args:
            config: Configuration dictionary loaded from YAML file.
                   Must contain at least: name, type, priority, enabled, connection
        """
        self.config = config
        self.name: str = config.get("name", "Unknown")
        self.source_type: str = config.get("type", "unknown")
        self.priority: int = config.get("priority", 1)
        self.enabled: bool = config.get("enabled", True)
        self.connection: dict[str, Any] = config.get("connection", {})
        self.field_mapping: dict[str, str] = config.get("field_mapping", {})
        self.unit_conversions: dict[str, dict[str, Any]] = config.get("unit_conversions", {})

    @abstractmethod
    async def fetch_current(self, city: str) -> dict[str, Any]:
        """Fetch current weather data for a given city.

        Args:
            city: City name (e.g., "Moscow", "London")

        Returns:
            Dictionary with weather data in normalized format (SI units):
            - temperature: float (Celsius)
            - feels_like: float (Celsius)
            - humidity: int (%)
            - pressure: float (hPa)
            - wind_speed: float (m/s)
            - wind_direction: int (degrees)
            - description: str
            - icon: str
            - clouds: int (%)
            - visibility: int (meters)
            - timestamp: int (Unix epoch)

        Raises:
            Exception: If fetch fails or API returns error
        """
        pass

    @abstractmethod
    async def fetch_forecast(self, city: str, days: int = 5) -> list[dict[str, Any]]:
        """Fetch weather forecast for a given city.

        Args:
            city: City name
            days: Number of days to fetch (default: 5, max depends on source)

        Returns:
            List of dictionaries with forecast data (same format as fetch_current).
            Each item includes an additional 'forecast_time' field.

        Raises:
            Exception: If fetch fails or API returns error
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection to the data source is working.

        Returns:
            True if connection is successful, False otherwise
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this fetcher is enabled in configuration.

        Returns:
            True if enabled, False otherwise
        """
        return self.enabled

    def get_priority(self) -> int:
        """Get priority level for aggregation.

        Returns:
            Priority value (lower number = higher priority)
        """
        return self.priority

    def get_name(self) -> str:
        """Get human-readable name of the data source.

        Returns:
            Source name
        """
        return self.name

    def get_type(self) -> str:
        """Get type of the data source.

        Returns:
            Source type ('rest', 'parser', etc.)
        """
        return self.source_type

    def _get_nested_value(self, data: dict[str, Any], path: str) -> Any:
        """Extract nested value from dictionary using dot notation.

        Example:
            data = {"main": {"temp": 20.5}}
            path = "main.temp"
            returns 20.5

        Args:
            data: Source dictionary
            path: Dot-separated path (e.g., "main.temp" or "weather.0.description")

        Returns:
            Value at the specified path, or None if not found
        """
        keys = path.split(".")
        value: Any = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list):
                try:
                    index = int(key)
                    value = value[index] if 0 <= index < len(value) else None
                except (ValueError, IndexError):
                    return None
            else:
                return None

            if value is None:
                return None

        return value
