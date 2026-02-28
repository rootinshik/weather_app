"""WeatherAPI.com fetcher implementation.

Fetches current weather and 7-day hourly forecast from WeatherAPI.com.
Wind speed is returned by the API in kph and converted to m/s here.
Visibility is returned in km and converted to metres.
"""

import asyncio
import logging
from typing import Any

import aiohttp

from .base import AbstractWeatherFetcher

logger = logging.getLogger(__name__)

# Field mapping for individual hourly forecast entries.
# WeatherAPI nests each hour dict directly inside forecastday[].hour[],
# so paths have no "current." prefix (unlike the current-weather field_mapping).
_FORECAST_HOUR_MAPPING: dict[str, str] = {
    "temperature": "temp_c",
    "feels_like": "feelslike_c",
    "humidity": "humidity",
    "pressure": "pressure_mb",
    "wind_speed": "wind_kph",
    "wind_direction": "wind_degree",
    "description": "condition.text",
    "icon_code": "condition.icon",
    "cloudiness": "cloud",
    "visibility": "vis_km",
    "timestamp": "time_epoch",
}


class WeatherAPIFetcher(AbstractWeatherFetcher):
    """Fetcher for WeatherAPI.com Current Weather and Forecast APIs.

    API documentation:
    - Current: https://www.weatherapi.com/docs/#apis-realtime
    - Forecast: https://www.weatherapi.com/docs/#apis-forecast
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.base_url: str = self.connection.get("base_url", "")
        self.api_key: str = self.connection.get("api_key", "")
        self.timeout: int = self.connection.get("timeout", 10)
        self.endpoints: dict[str, Any] = config.get("endpoints", {})

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    async def fetch_current(self, city: str) -> dict[str, Any]:
        """Fetch current weather from WeatherAPI.com.

        Args:
            city: City name or ``lat,lon`` string

        Returns:
            Normalised weather dict in SI units, or empty dict on error
        """
        endpoint_cfg = self.endpoints.get("current", {})
        path = endpoint_cfg.get("path", "/current.json")
        params = self._prepare_params(endpoint_cfg.get("params", {}), city)
        url = f"{self.base_url}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status == 400:
                        body = await response.json()
                        msg = body.get("error", {}).get("message", "unknown")
                        logger.error("WeatherAPI city '%s' not found: %s", city, msg)
                        return {}
                    if response.status >= 400:
                        logger.error(
                            "WeatherAPI error %d for city '%s'", response.status, city
                        )
                        return {}
                    response.raise_for_status()
                    data = await response.json()
                    return self._map_current(data)

        except aiohttp.ClientError as exc:
            logger.error("WeatherAPI connection error for '%s': %s", city, exc)
            return {}
        except asyncio.TimeoutError:
            logger.error("WeatherAPI timeout for '%s' after %ds", city, self.timeout)
            return {}
        except Exception as exc:
            logger.error("WeatherAPI unexpected error for '%s': %s", city, exc)
            return {}

    async def fetch_forecast(self, city: str, days: int = 7) -> list[dict[str, Any]]:
        """Fetch hourly forecast from WeatherAPI.com.

        Args:
            city: City name or ``lat,lon`` string
            days: Days to request (1–7 on the free plan)

        Returns:
            List of hourly forecast dicts in SI units, or empty list on error
        """
        endpoint_cfg = self.endpoints.get("forecast", {})
        path = endpoint_cfg.get("path", "/forecast.json")
        params = self._prepare_params(endpoint_cfg.get("params", {}), city)
        params["days"] = str(min(max(days, 1), 7))
        url = f"{self.base_url}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status == 400:
                        body = await response.json()
                        msg = body.get("error", {}).get("message", "unknown")
                        logger.error(
                            "WeatherAPI forecast city '%s' not found: %s", city, msg
                        )
                        return []
                    if response.status >= 400:
                        logger.error(
                            "WeatherAPI forecast error %d for city '%s'",
                            response.status,
                            city,
                        )
                        return []
                    response.raise_for_status()
                    data = await response.json()
                    return self._extract_forecast_hours(data)

        except aiohttp.ClientError as exc:
            logger.error("WeatherAPI forecast connection error for '%s': %s", city, exc)
            return []
        except asyncio.TimeoutError:
            logger.error(
                "WeatherAPI forecast timeout for '%s' after %ds", city, self.timeout
            )
            return []
        except Exception as exc:
            logger.error("WeatherAPI forecast unexpected error for '%s': %s", city, exc)
            return []

    async def test_connection(self) -> bool:
        """Test connectivity by fetching current weather for London."""
        endpoint_cfg = self.endpoints.get("current", {})
        path = endpoint_cfg.get("path", "/current.json")
        params = self._prepare_params(endpoint_cfg.get("params", {}), "London")
        url = f"{self.base_url}{path}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    if response.status == 200:
                        logger.info("WeatherAPI connection test: OK")
                        return True
                    logger.warning(
                        "WeatherAPI connection test failed: status %d", response.status
                    )
                    return False
        except Exception as exc:
            logger.error("WeatherAPI connection test failed: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _prepare_params(
        self, params_config: dict[str, Any], city: str
    ) -> dict[str, str]:
        """Substitute ``{city}`` placeholder and API key references."""
        params: dict[str, str] = {}
        for key, value in params_config.items():
            value_str = str(value)
            if "{city}" in value_str:
                params[key] = value_str.replace("{city}", city)
            elif value_str.startswith("${") and value_str.endswith("}"):
                # Env-var reference — already resolved by config loader, use api_key
                params[key] = self.api_key
            else:
                params[key] = value_str
        return params

    def _apply_conversions(self, data: dict[str, Any]) -> None:
        """Apply unit conversions from config in-place (e.g. kph → m/s)."""
        for field, conv in self.unit_conversions.items():
            if field in data and data[field] is not None:
                factor = float(conv.get("factor", 1.0))
                data[field] = round(float(data[field]) * factor, 4)

    def _map_current(self, api_response: dict[str, Any]) -> dict[str, Any]:
        """Map fields from the current-weather response and convert units."""
        result: dict[str, Any] = {}
        for target, path in self.field_mapping.items():
            value = self._get_nested_value(api_response, path)
            if value is not None:
                result[target] = value
        self._apply_conversions(result)
        return result

    def _map_hour(self, hour: dict[str, Any]) -> dict[str, Any]:
        """Map fields from a single hourly forecast entry and convert units."""
        result: dict[str, Any] = {}
        for target, path in _FORECAST_HOUR_MAPPING.items():
            value = self._get_nested_value(hour, path)
            if value is not None:
                result[target] = value
        # Expose time_epoch as forecast_time to match OWM pattern
        result["forecast_time"] = hour.get("time_epoch")
        self._apply_conversions(result)
        return result

    def _extract_forecast_hours(
        self, api_response: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract every hourly entry from a forecast response."""
        forecast_days = api_response.get("forecast", {}).get("forecastday", [])
        result: list[dict[str, Any]] = []
        for day in forecast_days:
            for hour in day.get("hour", []):
                mapped = self._map_hour(hour)
                if mapped:
                    result.append(mapped)
        return result
