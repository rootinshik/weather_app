"""Yandex.Weather HTML parser fetcher.

Fetches current weather data from Yandex.Weather by scraping HTML pages.
CSS selectors and connection settings come from the YAML config file.
Pressure is reported in mmHg by Yandex and converted to hPa using the
factor from the config's unit_conversions section.
"""

import asyncio
import logging
import re
import time
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from .base import AbstractWeatherFetcher

logger = logging.getLogger(__name__)

# Mapping of common city names → Yandex.Weather URL slugs.
# Yandex uses Cyrillic transliteration slugs (e.g. "moscow" for Москва).
CITY_SLUG_MAP: dict[str, str] = {
    # Russian
    "moscow": "moscow",
    "moskva": "moscow",
    "москва": "moscow",
    "saint-petersburg": "saint-petersburg",
    "saint petersburg": "saint-petersburg",
    "spb": "saint-petersburg",
    "санкт-петербург": "saint-petersburg",
    "novosibirsk": "novosibirsk",
    "новосибирск": "novosibirsk",
    "yekaterinburg": "yekaterinburg",
    "екатеринбург": "yekaterinburg",
    "kazan": "kazan",
    "казань": "kazan",
    "nizhny-novgorod": "nizhny-novgorod",
    "nizhny novgorod": "nizhny-novgorod",
    "нижний новгород": "nizhny-novgorod",
    "chelyabinsk": "chelyabinsk",
    "челябинск": "chelyabinsk",
    "samara": "samara",
    "самара": "samara",
    "omsk": "omsk",
    "омск": "omsk",
    "rostov-on-don": "rostov-on-don",
    "ростов-на-дону": "rostov-on-don",
    "ufa": "ufa",
    "уфа": "ufa",
    "krasnoyarsk": "krasnoyarsk",
    "красноярск": "krasnoyarsk",
    "perm": "perm",
    "пермь": "perm",
    "voronezh": "voronezh",
    "воронеж": "voronezh",
    "volgograd": "volgograd",
    "волгоград": "volgograd",
    # International
    "london": "london",
    "paris": "paris",
    "berlin": "berlin",
    "new york": "new-york",
    "new-york": "new-york",
    "beijing": "beijing",
    "tokyo": "tokyo",
}


def _city_to_slug(city: str) -> str:
    """Convert a city name to a Yandex.Weather URL slug.

    Looks up the city in the known mapping first; if not found, falls back to
    lowercasing and replacing spaces with hyphens (best-effort).

    Args:
        city: City name in any case (English or Russian)

    Returns:
        URL slug suitable for https://yandex.ru/pogoda/{slug}
    """
    normalized = city.strip().lower()
    return CITY_SLUG_MAP.get(normalized, normalized.replace(" ", "-"))


class YandexWeatherFetcher(AbstractWeatherFetcher):
    """Fetcher that parses Yandex.Weather HTML pages with BeautifulSoup.

    Configuration is loaded from ``backend/config/sources/yandex_weather.yaml``.
    The ``css_selectors`` section in that file drives all element lookups so that
    selector changes do not require code changes.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.base_url: str = self.connection.get("base_url", "https://yandex.ru/pogoda")
        self.timeout: int = self.connection.get("timeout", 15)
        self.headers: dict[str, str] = self.connection.get("headers", {})
        self.css_selectors: dict[str, str] = config.get("css_selectors", {})
        self.endpoints: dict[str, Any] = config.get("endpoints", {})

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    async def fetch_current(self, city: str) -> dict[str, Any]:
        """Fetch current weather for *city* by scraping Yandex.Weather.

        Args:
            city: City name (English or Russian)

        Returns:
            Normalised weather dict in SI units, or empty dict on error.
            Pressure is converted from mmHg to hPa.
        """
        slug = _city_to_slug(city)
        endpoint_path = self.endpoints.get("current", {}).get("path", "/{city}")
        path = endpoint_path.replace("{city}", slug)
        url = f"{self.base_url}{path}"

        html = await self._fetch_html(url, city)
        if html is None:
            return {}

        return self._parse_current(html, city)

    async def fetch_forecast(self, city: str, days: int = 5) -> list[dict[str, Any]]:
        """Yandex.Weather forecast scraping is not implemented.

        Yandex does not expose a stable machine-readable forecast endpoint
        without a paid API key. This method always returns an empty list so
        that the aggregator can fall back to other sources for forecast data.

        Args:
            city: City name (unused)
            days: Number of days (unused)

        Returns:
            Empty list
        """
        logger.info(
            "%s: forecast scraping not supported, skipping forecast for '%s'",
            self.name,
            city,
        )
        return []

    async def test_connection(self) -> bool:
        """Test connectivity by fetching the Moscow page and checking for content.

        Returns:
            True if the page loaded and the temperature selector matched,
            False otherwise.
        """
        html = await self._fetch_html(f"{self.base_url}/moscow", "moscow")
        if html is None:
            return False

        soup = BeautifulSoup(html, "html.parser")
        temp_selector = self.css_selectors.get("temperature", ".temp__value")
        element = soup.select_one(temp_selector)

        if element is not None:
            logger.info("%s connection test: OK", self.name)
            return True

        logger.warning(
            "%s connection test: page loaded but temperature element not found "
            "(selector: '%s') — HTML structure may have changed",
            self.name,
            temp_selector,
        )
        return False

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    async def _fetch_html(self, url: str, city: str) -> str | None:
        """Download the HTML page at *url*.

        Args:
            url: Full URL to fetch
            city: City name used only for log messages

        Returns:
            Raw HTML string, or None on any error.
        """
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    allow_redirects=True,
                ) as response:
                    if response.status == 404:
                        logger.error(
                            "%s: page not found for city '%s' (url: %s)",
                            self.name, city, url,
                        )
                        return None

                    if response.status >= 400:
                        logger.error(
                            "%s: HTTP %d for city '%s' (url: %s)",
                            self.name, response.status, city, url,
                        )
                        return None

                    return await response.text(encoding="utf-8", errors="replace")

        except aiohttp.ClientError as exc:
            logger.error("%s: connection error for '%s': %s", self.name, city, exc)
            return None
        except asyncio.TimeoutError:
            logger.error(
                "%s: timeout after %ds for city '%s'", self.name, self.timeout, city
            )
            return None
        except Exception as exc:
            logger.error("%s: unexpected error for '%s': %s", self.name, city, exc)
            return None

    def _parse_current(self, html: str, city: str) -> dict[str, Any]:
        """Parse current weather fields from the downloaded HTML.

        Uses ``css_selectors`` from the YAML config for all element lookups.
        Missing elements are logged as warnings and skipped.

        Args:
            html: Raw HTML content of the Yandex.Weather page
            city: City name (used only for log messages)

        Returns:
            Normalised weather dict.  Pressure is converted mmHg → hPa.
        """
        soup = BeautifulSoup(html, "html.parser")
        result: dict[str, Any] = {}

        # ---- Extract each field via its CSS selector ---- #
        field_extractors = {
            "temperature": self._extract_temperature,
            "feels_like": self._extract_temperature,
            "humidity": self._extract_int,
            "pressure": self._extract_float,
            "wind_speed": self._extract_float,
            "description": self._extract_text,
            "icon": self._extract_icon_url,
        }

        for field, extractor in field_extractors.items():
            selector = self.css_selectors.get(field)
            if not selector:
                continue

            element = soup.select_one(selector)
            if element is None:
                logger.warning(
                    "%s: element not found for field '%s' (selector: '%s') "
                    "for city '%s' — HTML structure may have changed",
                    self.name, field, selector, city,
                )
                continue

            value = extractor(element)
            if value is not None:
                result[field] = value

        # ---- Unit conversions ---- #
        self._apply_conversions(result)

        # ---- Add server-side timestamp ---- #
        result["timestamp"] = int(time.time())

        return result

    def _apply_conversions(self, data: dict[str, Any]) -> None:
        """Apply unit conversions from ``unit_conversions`` config in-place.

        Args:
            data: Weather data dict to mutate
        """
        for field, conv in self.unit_conversions.items():
            if field in data and data[field] is not None:
                try:
                    factor = float(conv.get("factor", 1.0))
                    data[field] = round(float(data[field]) * factor, 4)
                except (ValueError, TypeError) as exc:
                    logger.warning(
                        "%s: unit conversion failed for field '%s': %s",
                        self.name, field, exc,
                    )

    # ---- Field-specific text extractors ---- #

    @staticmethod
    def _extract_temperature(element: Any) -> float | None:
        """Extract a numeric temperature value, stripping sign characters."""
        raw = element.get_text(strip=True)
        # Yandex renders "−5" with a Unicode minus (U+2212) and "+" for positive
        cleaned = raw.replace("\u2212", "-").replace("+", "").replace("\u00b0", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            # Try stripping any remaining non-numeric characters except '-' and '.'
            digits = "".join(c for c in cleaned if c.isdigit() or c in "-.")
            try:
                return float(digits) if digits else None
            except ValueError:
                return None

    @staticmethod
    def _extract_float(element: Any) -> float | None:
        """Extract the first numeric value (int or float) from element text."""
        raw = element.get_text(strip=True)
        # Match optional leading minus + digits + optional decimal part
        match = re.search(r"-?\d+(?:\.\d+)?", raw)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_int(element: Any) -> int | None:
        """Extract an integer value from element text."""
        raw = element.get_text(strip=True)
        cleaned = "".join(c for c in raw if c.isdigit())
        try:
            return int(cleaned) if cleaned else None
        except ValueError:
            return None

    @staticmethod
    def _extract_text(element: Any) -> str | None:
        """Extract plain text content from element."""
        text = element.get_text(strip=True)
        return text if text else None

    @staticmethod
    def _extract_icon_url(element: Any) -> str | None:
        """Extract icon URL from an <img> element's src attribute."""
        src = element.get("src") or element.get("data-src")
        if src:
            # Yandex URLs may start with "//" — normalise to https
            if src.startswith("//"):
                return f"https:{src}"
            return src
        return None
