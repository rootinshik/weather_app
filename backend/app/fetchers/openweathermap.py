"""OpenWeatherMap API fetcher implementation.

Fetches current weather and forecast data from OpenWeatherMap API.
Supports both Current Weather API and 5-Day Forecast API.
"""

import asyncio
import logging
from typing import Any

import aiohttp

from .base import AbstractWeatherFetcher

logger = logging.getLogger(__name__)


class OpenWeatherMapFetcher(AbstractWeatherFetcher):
    """Fetcher for OpenWeatherMap Current Weather and 5-Day Forecast APIs.

    API documentation:
    - Current: https://openweathermap.org/current
    - Forecast: https://openweathermap.org/forecast5
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize OpenWeatherMap fetcher.

        Args:
            config: Configuration dictionary from YAML file
        """
        super().__init__(config)
        self.base_url: str = self.connection.get("base_url", "")
        self.api_key: str = self.connection.get("api_key", "")
        self.timeout: int = self.connection.get("timeout", 10)
        self.endpoints: dict[str, Any] = config.get("endpoints", {})

    async def fetch_current(self, city: str) -> dict[str, Any]:
        """Fetch current weather data from OpenWeatherMap API.

        Args:
            city: City name (e.g., "Moscow", "London")

        Returns:
            Dictionary with normalized weather data in SI units

        Raises:
            Exception: If API request fails or returns invalid data
        """
        endpoint_config = self.endpoints.get("current", {})
        path = endpoint_config.get("path", "/weather")
        params = self._prepare_params(endpoint_config.get("params", {}), city)

        url = f"{self.base_url}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 404:
                        logger.error(f"City '{city}' not found in {self.name}")
                        return {}

                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(
                            f"{self.name} API error {response.status}: {error_text}"
                        )
                        return {}

                    response.raise_for_status()
                    data = await response.json()

                    return self._map_fields(data)

        except aiohttp.ClientError as e:
            logger.error(f"{self.name} connection error for city '{city}': {e}")
            return {}
        except asyncio.TimeoutError:
            logger.error(f"{self.name} timeout for city '{city}' after {self.timeout}s")
            return {}
        except Exception as e:
            logger.error(f"{self.name} unexpected error for city '{city}': {e}")
            return {}

    async def fetch_forecast(self, city: str, days: int = 5) -> list[dict[str, Any]]:
        """Fetch 5-day weather forecast from OpenWeatherMap API.

        Args:
            city: City name
            days: Number of days (ignored, OpenWeatherMap returns fixed 5 days)

        Returns:
            List of forecast dictionaries with normalized weather data

        Raises:
            Exception: If API request fails or returns invalid data
        """
        endpoint_config = self.endpoints.get("forecast", {})
        path = endpoint_config.get("path", "/forecast")
        params = self._prepare_params(endpoint_config.get("params", {}), city)

        url = f"{self.base_url}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 404:
                        logger.error(f"City '{city}' not found in {self.name}")
                        return []

                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(
                            f"{self.name} API error {response.status}: {error_text}"
                        )
                        return []

                    response.raise_for_status()
                    data = await response.json()

                    # OpenWeatherMap returns list of forecasts in 'list' field
                    forecast_list = data.get("list", [])

                    result = []
                    for item in forecast_list:
                        mapped_data = self._map_fields(item)
                        if mapped_data:
                            # Add forecast timestamp
                            mapped_data["forecast_time"] = item.get("dt")
                            result.append(mapped_data)

                    return result

        except aiohttp.ClientError as e:
            logger.error(f"{self.name} connection error for city '{city}': {e}")
            return []
        except asyncio.TimeoutError:
            logger.error(f"{self.name} timeout for city '{city}' after {self.timeout}s")
            return []
        except Exception as e:
            logger.error(f"{self.name} unexpected error for city '{city}': {e}")
            return []

    async def test_connection(self) -> bool:
        """Test if OpenWeatherMap API is accessible.

        Returns:
            True if API responds successfully, False otherwise
        """
        # Test with a known city (London)
        endpoint_config = self.endpoints.get("current", {})
        path = endpoint_config.get("path", "/weather")
        params = self._prepare_params(endpoint_config.get("params", {}), "London")

        url = f"{self.base_url}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info(f"{self.name} connection test: OK")
                        return True
                    else:
                        logger.warning(
                            f"{self.name} connection test failed with status {response.status}"
                        )
                        return False

        except Exception as e:
            logger.error(f"{self.name} connection test failed: {e}")
            return False

    def _prepare_params(self, params_config: dict[str, str], city: str) -> dict[str, str]:
        """Prepare request parameters by substituting placeholders.

        Args:
            params_config: Parameters template from config
            city: City name to substitute

        Returns:
            Dictionary with prepared parameters
        """
        params = {}

        for key, value in params_config.items():
            # Substitute placeholders
            if "{city}" in value:
                params[key] = value.replace("{city}", city)
            elif value.startswith("${") and value.endswith("}"):
                # Environment variable reference - already substituted by config loader
                # Use api_key from connection config
                if "API_KEY" in value or "appid" in key:
                    params[key] = self.api_key
                else:
                    params[key] = value
            else:
                params[key] = value

        return params

    def _map_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map API response fields to normalized format using field_mapping.

        Args:
            data: Raw API response data

        Returns:
            Dictionary with normalized field names and values in SI units
        """
        result: dict[str, Any] = {}

        for target_field, source_path in self.field_mapping.items():
            value = self._get_nested_value(data, source_path)

            if value is not None:
                result[target_field] = value

        # OpenWeatherMap returns data in metric units by default (units=metric)
        # Temperature: Celsius
        # Wind speed: m/s
        # Pressure: hPa
        # No conversion needed

        return result
