"""Yandex.Weather HTML parser fetcher.

Fetches current weather data from Yandex.Weather by scraping HTML pages.
Yandex renders pages as a Next.js application that embeds weather data as
JSON inside ``__next_f.push`` script tags.  The fetcher uses two strategies:

1. **Primary – JSON extraction**: numeric fields (temperature, pressure, etc.)
   are read directly from the embedded JSON.  This is more reliable than CSS
   selectors because the JSON field names are part of the API contract and
   survive UI redesigns.

2. **Fallback – CSS selectors**: if the embedded JSON cannot be found the
   fetcher falls back to the CSS selectors stored in the YAML config.  The
   description text is always taken from the DOM because the JSON uses English
   enum values (e.g. ``OVERCAST``).

Pressure is in mmHg in the source and is converted to hPa using the factor
defined in the ``unit_conversions`` section of the YAML config.
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

# Yandex icon CDN prefix for constructing icon URLs from short codes like "ovc".
_YANDEX_ICON_URL = "https://yastatic.net/weather/i/icons/blueye/color/svg/{code}.svg"

# Mapping of common city names → Yandex.Weather URL slugs.
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

# Regex patterns for JSON fields extracted from __next_f.push script tags.
# Yandex Next.js pages JSON-encode keys as \"key\" (backslash-escaped quotes).
_JSON_PATTERNS: dict[str, re.Pattern[str]] = {
    "temperature": re.compile(r'\\"temperatureInCelsius\\":(-?\d+)'),
    "feels_like": re.compile(r'\\"feelsLike\\":(-?\d+)'),
    "pressure": re.compile(r'\\"pressure\\":(\d+)'),
    "humidity": re.compile(r'\\"humidity\\":(\d+)'),
    "wind_speed": re.compile(r'\\"windSpeed\\":([\d.]+)'),
    "visibility": re.compile(r'\\"visibility\\":(\d+)'),
}
# Icon code pattern — search within the fact block only
_JSON_ICON_PATTERN = re.compile(r'\\"icon\\":\\"([^\\"]+)\\"')


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
    Numeric weather values are extracted from embedded Next.js JSON; the
    ``css_selectors`` config section is used for the description text and as a
    fallback for numeric fields when the JSON is absent.
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

        Yandex does not expose a stable parseable forecast page without a paid
        API key.  Returns an empty list so the aggregator uses other sources.

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
        """Test connectivity by checking whether Moscow page loads with data.

        Tries JSON extraction first; falls back to the temperature CSS selector.

        Returns:
            True if weather data was found, False otherwise.
        """
        html = await self._fetch_html(f"{self.base_url}/moscow", "moscow")
        if html is None:
            return False

        # Try JSON extraction first
        json_data = self._extract_json_fact(html)
        if json_data.get("temperature") is not None:
            logger.info("%s connection test: OK (JSON)", self.name)
            return True

        # Fallback: CSS selector
        soup = BeautifulSoup(html, "html.parser")
        temp_selector = self.css_selectors.get("temperature", "")
        if temp_selector and soup.select_one(temp_selector) is not None:
            logger.info("%s connection test: OK (CSS)", self.name)
            return True

        logger.warning(
            "%s connection test: page loaded but no weather data found "
            "— HTML/JSON structure may have changed",
            self.name,
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

    def _extract_json_fact(self, html: str) -> dict[str, Any]:
        """Extract numeric weather data from the Next.js embedded JSON.

        Yandex renders weather values as a serialised React Server Components
        payload injected via ``self.__next_f.push([1, "..."])`` script tags.
        JSON keys inside these strings are backslash-escaped (``\\"key\\"``).

        Returns a dict with raw SI-ish values (temperature °C, pressure mmHg,
        wind_speed m/s, humidity %, visibility m).  Empty dict if not found.
        """
        soup = BeautifulSoup(html, "html.parser")
        fact_marker = '\\"fact\\":'

        for script in soup.find_all("script"):
            text = script.string
            if not text or fact_marker not in text:
                continue

            # Locate the fact JSON object by brace matching
            fact_start = text.find(fact_marker)
            brace_start = text.find("{", fact_start + len(fact_marker))
            if brace_start == -1:
                continue

            depth = 0
            end = brace_start
            for i in range(brace_start, min(brace_start + 2000, len(text))):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            fact_block = text[brace_start:end]
            result: dict[str, Any] = {}

            for field, pattern in _JSON_PATTERNS.items():
                m = pattern.search(fact_block)
                if m:
                    result[field] = float(m.group(1))

            # Icon code → construct CDN URL
            icon_m = _JSON_ICON_PATTERN.search(fact_block)
            if icon_m:
                result["icon"] = _YANDEX_ICON_URL.format(code=icon_m.group(1))

            if result:
                logger.debug(
                    "%s: JSON extraction successful for fact block", self.name
                )
                return result

        return {}

    def _parse_current(self, html: str, city: str) -> dict[str, Any]:
        """Build the normalised weather dict from a downloaded HTML page.

        Strategy:
        1. Extract numeric fields from embedded JSON (reliable across UI updates).
        2. Extract description text via CSS selector (JSON only has English enums).
        3. If JSON extraction yielded nothing, fall back to CSS selectors for all
           numeric fields.
        4. Apply unit conversions (pressure mmHg → hPa) and add timestamp.

        Args:
            html: Raw HTML content of the Yandex.Weather page
            city: City name (used for log messages)

        Returns:
            Normalised weather dict.
        """
        soup = BeautifulSoup(html, "html.parser")
        result: dict[str, Any] = {}

        # ---- 1. Primary: embedded JSON ---- #
        json_data = self._extract_json_fact(html)
        if json_data:
            result.update(json_data)
        else:
            logger.warning(
                "%s: embedded JSON not found for city '%s', falling back to CSS selectors",
                self.name, city,
            )
            # CSS fallback for numeric fields
            css_numeric: dict[str, Any] = {
                "temperature": (
                    self.css_selectors.get("temperature"), self._extract_temperature
                ),
                "feels_like": (
                    self.css_selectors.get("feels_like"), self._extract_temperature
                ),
                "humidity": (
                    self.css_selectors.get("humidity"), self._extract_int
                ),
                "pressure": (
                    self.css_selectors.get("pressure"), self._extract_float
                ),
                "wind_speed": (
                    self.css_selectors.get("wind_speed"), self._extract_float
                ),
            }
            for field, (selector, extractor) in css_numeric.items():
                if not selector:
                    continue
                element = soup.select_one(selector)
                if element is None:
                    logger.warning(
                        "%s: CSS selector '%s' not found for field '%s' in city '%s'",
                        self.name, selector, field, city,
                    )
                    continue
                value = extractor(element)
                if value is not None:
                    result[field] = value

        # ---- 2. Description from CSS (JSON has English enum codes) ---- #
        desc_selector = self.css_selectors.get("description")
        if desc_selector:
            desc_el = soup.select_one(desc_selector)
            if desc_el:
                text = desc_el.get_text(strip=True)
                if text:
                    result["description"] = text
            else:
                logger.warning(
                    "%s: description selector '%s' not found for city '%s' "
                    "— HTML structure may have changed",
                    self.name, desc_selector, city,
                )

        # ---- 3. Unit conversions ---- #
        self._apply_conversions(result)

        # ---- 4. Timestamp ---- #
        result["timestamp"] = int(time.time())

        return result

    def _apply_conversions(self, data: dict[str, Any]) -> None:
        """Apply unit conversions from ``unit_conversions`` config in-place."""
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

    # ---- CSS fallback extractors ---- #

    @staticmethod
    def _extract_temperature(element: Any) -> float | None:
        """Extract a numeric temperature value, stripping sign/degree chars."""
        raw = element.get_text(strip=True)
        # Yandex uses Unicode minus U+2212 and "°" (U+00B0)
        cleaned = raw.replace("\u2212", "-").replace("+", "").replace("\u00b0", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            # Fallback: extract first number including optional minus
            m = re.search(r"-?\d+(?:\.\d+)?", cleaned)
            return float(m.group()) if m else None

    @staticmethod
    def _extract_float(element: Any) -> float | None:
        """Extract the first numeric value (int or float) from element text."""
        raw = element.get_text(strip=True)
        m = re.search(r"-?\d+(?:\.\d+)?", raw)
        return float(m.group()) if m else None

    @staticmethod
    def _extract_int(element: Any) -> int | None:
        """Extract an integer value from element text."""
        raw = element.get_text(strip=True)
        cleaned = "".join(c for c in raw if c.isdigit())
        return int(cleaned) if cleaned else None

    @staticmethod
    def _extract_text(element: Any) -> str | None:
        """Extract plain text content from element."""
        text = element.get_text(strip=True)
        return text if text else None
