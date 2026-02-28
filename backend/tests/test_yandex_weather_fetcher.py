"""Unit tests for YandexWeatherFetcher."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from app.fetchers.yandex_weather import YandexWeatherFetcher, _city_to_slug


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**overrides) -> dict:
    base = {
        "name": "YandexWeather",
        "type": "parser",
        "priority": 3,
        "enabled": True,
        "connection": {
            "base_url": "https://yandex.ru/pogoda",
            "timeout": 15,
            "headers": {
                "User-Agent": "Mozilla/5.0 (compatible; WeatherAggregator/1.0)",
                "Accept-Language": "ru-RU,ru;q=0.9",
            },
        },
        "endpoints": {
            "current": {"path": "/{city}"},
        },
        "css_selectors": {
            "temperature": ".temp__value",
            "feels_like": ".term__feels-like .temp__value",
            "humidity": ".fact__humidity .fact__unit",
            "pressure": ".fact__pressure .fact__unit",
            "wind_speed": ".fact__wind-speed .wind-speed",
            "description": ".fact__condition",
            "icon": ".fact__icon img",
        },
        "field_mapping": {},
        "unit_conversions": {
            "pressure": {"from": "mmhg", "to": "hpa", "factor": 1.33322},
        },
    }
    base.update(overrides)
    return base


@pytest.fixture
def fetcher():
    return YandexWeatherFetcher(_make_config())


def _mock_http(status: int, text: str) -> MagicMock:
    """Build a mock aiohttp.ClientSession that returns the given HTML text."""
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.text = AsyncMock(return_value=text)

    mock_get_ctx = MagicMock()
    mock_get_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_get_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.get.return_value = mock_get_ctx

    return mock_session


# Minimal Yandex.Weather-like HTML fragment with all expected elements present
_FULL_HTML = """
<html><body>
  <div class="fact__temp">
    <span class="temp__value">−3</span>
  </div>
  <div class="term__feels-like">
    <span class="temp__value">−7</span>
  </div>
  <div class="fact__humidity">
    <span class="fact__unit">85%</span>
  </div>
  <div class="fact__pressure">
    <span class="fact__unit">750 мм рт. ст.</span>
  </div>
  <div class="fact__wind-speed">
    <span class="wind-speed">4</span>
  </div>
  <div class="fact__condition">Пасмурно</div>
  <div class="fact__icon">
    <img src="//yandex.ru/icons/cloudy.png">
  </div>
</body></html>
"""

# HTML with temperature element only (other selectors absent)
_PARTIAL_HTML = """
<html><body>
  <span class="temp__value">+12</span>
</body></html>
"""

# HTML with no matching elements at all
_EMPTY_HTML = "<html><body></body></html>"


# ---------------------------------------------------------------------------
# _city_to_slug
# ---------------------------------------------------------------------------

class TestCityToSlug:
    def test_known_english_city(self):
        assert _city_to_slug("Moscow") == "moscow"

    def test_known_russian_city(self):
        assert _city_to_slug("Москва") == "moscow"

    def test_known_city_with_space(self):
        assert _city_to_slug("Saint Petersburg") == "saint-petersburg"

    def test_unknown_city_fallback(self):
        # Unknown city → lowercase + spaces replaced with hyphens
        assert _city_to_slug("Some Unknown City") == "some-unknown-city"

    def test_case_insensitive(self):
        assert _city_to_slug("MOSCOW") == "moscow"


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

class TestYandexWeatherFetcherInit:
    def test_reads_config_fields(self, fetcher):
        assert fetcher.name == "YandexWeather"
        assert fetcher.source_type == "parser"
        assert fetcher.priority == 3
        assert fetcher.base_url == "https://yandex.ru/pogoda"
        assert fetcher.timeout == 15

    def test_css_selectors_loaded(self, fetcher):
        assert fetcher.css_selectors["temperature"] == ".temp__value"
        assert fetcher.css_selectors["pressure"] == ".fact__pressure .fact__unit"

    def test_is_enabled(self, fetcher):
        assert fetcher.is_enabled() is True


# ---------------------------------------------------------------------------
# _fetch_html (private, tested via mocks)
# ---------------------------------------------------------------------------

class TestFetchHtml:
    @pytest.mark.asyncio
    async def test_returns_html_on_200(self, fetcher):
        mock_session = _mock_http(200, "<html>ok</html>")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            html = await fetcher._fetch_html("https://yandex.ru/pogoda/moscow", "moscow")
        assert html == "<html>ok</html>"

    @pytest.mark.asyncio
    async def test_returns_none_on_404(self, fetcher):
        mock_session = _mock_http(404, "")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            html = await fetcher._fetch_html("https://yandex.ru/pogoda/xyz", "xyz")
        assert html is None

    @pytest.mark.asyncio
    async def test_returns_none_on_500(self, fetcher):
        mock_session = _mock_http(500, "")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            html = await fetcher._fetch_html("https://yandex.ru/pogoda/moscow", "moscow")
        assert html is None

    @pytest.mark.asyncio
    async def test_returns_none_on_client_error(self, fetcher):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.side_effect = aiohttp.ClientError("refused")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            html = await fetcher._fetch_html("https://yandex.ru/pogoda/moscow", "moscow")
        assert html is None

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self, fetcher):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.side_effect = asyncio.TimeoutError()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            html = await fetcher._fetch_html("https://yandex.ru/pogoda/moscow", "moscow")
        assert html is None


# ---------------------------------------------------------------------------
# _parse_current
# ---------------------------------------------------------------------------

class TestParseCurrentHtml:
    def test_extracts_temperature(self, fetcher):
        result = fetcher._parse_current(_FULL_HTML, "moscow")
        assert result["temperature"] == -3.0

    def test_extracts_feels_like(self, fetcher):
        result = fetcher._parse_current(_FULL_HTML, "moscow")
        assert result["feels_like"] == -7.0

    def test_extracts_humidity(self, fetcher):
        result = fetcher._parse_current(_FULL_HTML, "moscow")
        assert result["humidity"] == 85

    def test_extracts_wind_speed(self, fetcher):
        result = fetcher._parse_current(_FULL_HTML, "moscow")
        assert result["wind_speed"] == 4.0

    def test_extracts_description(self, fetcher):
        result = fetcher._parse_current(_FULL_HTML, "moscow")
        assert result["description"] == "Пасмурно"

    def test_converts_pressure_mmhg_to_hpa(self, fetcher):
        result = fetcher._parse_current(_FULL_HTML, "moscow")
        # 750 mmHg * 1.33322 ≈ 999.915
        expected = round(750 * 1.33322, 4)
        assert abs(result["pressure"] - expected) < 0.01

    def test_extracts_icon_url_with_https(self, fetcher):
        result = fetcher._parse_current(_FULL_HTML, "moscow")
        assert result["icon"] == "https://yandex.ru/icons/cloudy.png"

    def test_timestamp_is_set(self, fetcher):
        result = fetcher._parse_current(_FULL_HTML, "moscow")
        assert "timestamp" in result
        assert isinstance(result["timestamp"], int)

    def test_partial_html_returns_partial_result(self, fetcher):
        # Only temperature selector matches
        result = fetcher._parse_current(_PARTIAL_HTML, "moscow")
        assert result["temperature"] == 12.0
        assert "humidity" not in result

    def test_empty_html_returns_only_timestamp(self, fetcher):
        result = fetcher._parse_current(_EMPTY_HTML, "moscow")
        # Nothing parsed except the auto-added timestamp
        assert set(result.keys()) == {"timestamp"}


# ---------------------------------------------------------------------------
# Static extractors
# ---------------------------------------------------------------------------

class TestExtractors:
    def _el(self, html: str):
        """Parse a single element from HTML snippet."""
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, "html.parser").find()

    def test_temperature_negative_unicode_minus(self):
        el = self._el("<span>\u22125</span>")
        assert YandexWeatherFetcher._extract_temperature(el) == -5.0

    def test_temperature_positive_with_plus(self):
        el = self._el("<span>+18</span>")
        assert YandexWeatherFetcher._extract_temperature(el) == 18.0

    def test_temperature_zero(self):
        el = self._el("<span>0</span>")
        assert YandexWeatherFetcher._extract_temperature(el) == 0.0

    def test_extract_float_strips_units(self):
        el = self._el("<span>750 мм рт. ст.</span>")
        assert YandexWeatherFetcher._extract_float(el) == 750.0

    def test_extract_int_strips_percent(self):
        el = self._el("<span>85%</span>")
        assert YandexWeatherFetcher._extract_int(el) == 85

    def test_extract_text_returns_stripped(self):
        el = self._el("<div>  Ясно  </div>")
        assert YandexWeatherFetcher._extract_text(el) == "Ясно"

    def test_extract_icon_url_adds_https(self):
        el = self._el('<img src="//cdn.example.com/icon.png">')
        assert YandexWeatherFetcher._extract_icon_url(el) == "https://cdn.example.com/icon.png"

    def test_extract_icon_url_absolute(self):
        el = self._el('<img src="https://cdn.example.com/icon.png">')
        assert YandexWeatherFetcher._extract_icon_url(el) == "https://cdn.example.com/icon.png"

    def test_extract_icon_url_no_src(self):
        el = self._el("<img>")
        assert YandexWeatherFetcher._extract_icon_url(el) is None


# ---------------------------------------------------------------------------
# _apply_conversions
# ---------------------------------------------------------------------------

class TestApplyConversions:
    def test_pressure_converted(self, fetcher):
        data = {"pressure": 750.0}
        fetcher._apply_conversions(data)
        assert abs(data["pressure"] - 750 * 1.33322) < 0.001

    def test_missing_field_ignored(self, fetcher):
        data = {}
        fetcher._apply_conversions(data)
        assert data == {}

    def test_none_field_ignored(self, fetcher):
        data = {"pressure": None}
        fetcher._apply_conversions(data)
        assert data["pressure"] is None


# ---------------------------------------------------------------------------
# fetch_current (full integration via mock HTTP)
# ---------------------------------------------------------------------------

class TestFetchCurrentAsync:
    @pytest.mark.asyncio
    async def test_returns_data_on_200(self, fetcher):
        mock_session = _mock_http(200, _FULL_HTML)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")
        assert result["temperature"] == -3.0
        assert result["description"] == "Пасмурно"

    @pytest.mark.asyncio
    async def test_returns_empty_on_404(self, fetcher):
        mock_session = _mock_http(404, "")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_on_network_error(self, fetcher):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.side_effect = aiohttp.ClientError("refused")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_on_timeout(self, fetcher):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.side_effect = asyncio.TimeoutError()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Moscow")
        assert result == {}

    @pytest.mark.asyncio
    async def test_uses_correct_slug_in_url(self, fetcher):
        """Ensure city name is converted to slug before building URL."""
        mock_session = _mock_http(200, _EMPTY_HTML)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            await fetcher.fetch_current("Москва")
        call_url = mock_session.get.call_args[0][0]
        assert call_url == "https://yandex.ru/pogoda/moscow"


# ---------------------------------------------------------------------------
# fetch_forecast — always returns empty list
# ---------------------------------------------------------------------------

class TestFetchForecast:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, fetcher):
        result = await fetcher.fetch_forecast("Moscow")
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_any_days(self, fetcher):
        result = await fetcher.fetch_forecast("Moscow", days=7)
        assert result == []


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------

class TestConnectionTest:
    @pytest.mark.asyncio
    async def test_returns_true_when_selector_matches(self, fetcher):
        mock_session = _mock_http(200, _FULL_HTML)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher.test_connection() is True

    @pytest.mark.asyncio
    async def test_returns_false_when_selector_missing(self, fetcher):
        mock_session = _mock_http(200, _EMPTY_HTML)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher.test_connection() is False

    @pytest.mark.asyncio
    async def test_returns_false_on_http_error(self, fetcher):
        mock_session = _mock_http(500, "")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher.test_connection() is False

    @pytest.mark.asyncio
    async def test_returns_false_on_network_error(self, fetcher):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.side_effect = aiohttp.ClientError("refused")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher.test_connection() is False
