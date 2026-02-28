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
            "temperature": '[class*="AppFactTemperature_content"]',
            "feels_like": '[class*="AppFact_feels__base"]',
            "description": '[class*="AppFact_warning__first_text"]',
            "wind_speed": '[class*="AppFact_details__item"]:first-child',
            "pressure": '[class*="AppFact_details__item"]:nth-child(2)',
            "humidity": '[class*="AppFact_details__item"]:nth-child(3)',
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
    """Build a mock aiohttp.ClientSession returning the given HTML text."""
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


# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

# Realistic Next.js payload: JSON data embedded in a script tag.
# Keys use escaped double-quotes (\") as produced by React Server Components.
_NEXTJS_HTML = """
<html><body>
  <script>self.__next_f.push([1,"data:{\\"fact\\":{\\"temperature\\":1,\
\\"temperatureInCelsius\\":1,\\"feelsLike\\":-2,\\"waterTemperature\\":0,\
\\"icon\\":\\"ovc\\",\\"windSpeed\\":1,\\"windGust\\":4.5,\\"pressure\\":761,\
\\"condition\\":\\"OVERCAST\\",\\"humidity\\":96,\\"visibility\\":10000}}"])</script>
  <span class="AppFact_warning__first_text___wtkV" data-has-dot="true">Пасмурно</span>
</body></html>
"""

# HTML with NO embedded JSON — only CSS elements (CSS-fallback path).
_CSS_ONLY_HTML = """
<html><body>
  <p class="AppFactTemperature_content__XYZ">+12°</p>
  <span class="AppFact_feels__base__ABC">Ощущается как −1°</span>
  <span class="AppFact_warning__first_text___DEF">Облачно</span>
</body></html>
"""

# Completely empty page — no data at all.
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
        assert "AppFact_warning__first_text" in fetcher.css_selectors["description"]
        assert "AppFactTemperature_content" in fetcher.css_selectors["temperature"]

    def test_is_enabled(self, fetcher):
        assert fetcher.is_enabled() is True


# ---------------------------------------------------------------------------
# _fetch_html
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
            assert await fetcher._fetch_html("https://yandex.ru/pogoda/xyz", "xyz") is None

    @pytest.mark.asyncio
    async def test_returns_none_on_500(self, fetcher):
        mock_session = _mock_http(500, "")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher._fetch_html("https://yandex.ru/pogoda/moscow", "moscow") is None

    @pytest.mark.asyncio
    async def test_returns_none_on_client_error(self, fetcher):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.side_effect = aiohttp.ClientError("refused")
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher._fetch_html("https://yandex.ru/pogoda/moscow", "moscow") is None

    @pytest.mark.asyncio
    async def test_returns_none_on_timeout(self, fetcher):
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.side_effect = asyncio.TimeoutError()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher._fetch_html("https://yandex.ru/pogoda/moscow", "moscow") is None


# ---------------------------------------------------------------------------
# _extract_json_fact
# ---------------------------------------------------------------------------

class TestExtractJsonFact:
    def test_extracts_temperature(self, fetcher):
        data = fetcher._extract_json_fact(_NEXTJS_HTML)
        assert data["temperature"] == 1.0

    def test_extracts_feels_like(self, fetcher):
        data = fetcher._extract_json_fact(_NEXTJS_HTML)
        assert data["feels_like"] == -2.0

    def test_extracts_pressure_mmhg(self, fetcher):
        data = fetcher._extract_json_fact(_NEXTJS_HTML)
        assert data["pressure"] == 761.0

    def test_extracts_humidity(self, fetcher):
        data = fetcher._extract_json_fact(_NEXTJS_HTML)
        assert data["humidity"] == 96.0

    def test_extracts_wind_speed_ms(self, fetcher):
        data = fetcher._extract_json_fact(_NEXTJS_HTML)
        assert data["wind_speed"] == 1.0

    def test_extracts_visibility_m(self, fetcher):
        data = fetcher._extract_json_fact(_NEXTJS_HTML)
        assert data["visibility"] == 10000.0

    def test_extracts_icon_url(self, fetcher):
        data = fetcher._extract_json_fact(_NEXTJS_HTML)
        assert data["icon"] == "https://yastatic.net/weather/i/icons/blueye/color/svg/ovc.svg"

    def test_returns_empty_dict_when_no_json(self, fetcher):
        assert fetcher._extract_json_fact(_CSS_ONLY_HTML) == {}

    def test_returns_empty_dict_on_empty_html(self, fetcher):
        assert fetcher._extract_json_fact(_EMPTY_HTML) == {}


# ---------------------------------------------------------------------------
# _parse_current — primary JSON path
# ---------------------------------------------------------------------------

class TestParseCurrentJson:
    def test_temperature_from_json(self, fetcher):
        result = fetcher._parse_current(_NEXTJS_HTML, "spb")
        assert result["temperature"] == 1.0

    def test_feels_like_from_json(self, fetcher):
        result = fetcher._parse_current(_NEXTJS_HTML, "spb")
        assert result["feels_like"] == -2.0

    def test_pressure_converted_mmhg_to_hpa(self, fetcher):
        result = fetcher._parse_current(_NEXTJS_HTML, "spb")
        expected = round(761 * 1.33322, 4)
        assert abs(result["pressure"] - expected) < 0.01

    def test_humidity_from_json(self, fetcher):
        result = fetcher._parse_current(_NEXTJS_HTML, "spb")
        assert result["humidity"] == 96.0

    def test_wind_speed_from_json(self, fetcher):
        result = fetcher._parse_current(_NEXTJS_HTML, "spb")
        assert result["wind_speed"] == 1.0

    def test_description_from_css(self, fetcher):
        result = fetcher._parse_current(_NEXTJS_HTML, "spb")
        assert result["description"] == "Пасмурно"

    def test_icon_url_constructed(self, fetcher):
        result = fetcher._parse_current(_NEXTJS_HTML, "spb")
        assert result["icon"].endswith("/ovc.svg")

    def test_timestamp_added(self, fetcher):
        result = fetcher._parse_current(_NEXTJS_HTML, "spb")
        assert "timestamp" in result
        assert isinstance(result["timestamp"], int)


# ---------------------------------------------------------------------------
# _parse_current — CSS fallback path
# ---------------------------------------------------------------------------

class TestParseCurrentCssFallback:
    def test_temperature_from_css(self, fetcher):
        result = fetcher._parse_current(_CSS_ONLY_HTML, "moscow")
        assert result["temperature"] == 12.0

    def test_feels_like_from_css(self, fetcher):
        result = fetcher._parse_current(_CSS_ONLY_HTML, "moscow")
        assert result["feels_like"] == -1.0

    def test_description_from_css(self, fetcher):
        result = fetcher._parse_current(_CSS_ONLY_HTML, "moscow")
        assert result["description"] == "Облачно"

    def test_empty_html_returns_only_timestamp(self, fetcher):
        result = fetcher._parse_current(_EMPTY_HTML, "moscow")
        assert set(result.keys()) == {"timestamp"}


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

    def test_none_field_skipped(self, fetcher):
        data = {"pressure": None}
        fetcher._apply_conversions(data)
        assert data["pressure"] is None


# ---------------------------------------------------------------------------
# CSS fallback static extractors
# ---------------------------------------------------------------------------

class TestExtractors:
    def _el(self, html: str):
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, "html.parser").find()

    def test_temperature_unicode_minus(self):
        el = self._el("<span>\u22125</span>")
        assert YandexWeatherFetcher._extract_temperature(el) == -5.0

    def test_temperature_positive_with_plus(self):
        el = self._el("<span>+18°</span>")
        assert YandexWeatherFetcher._extract_temperature(el) == 18.0

    def test_temperature_from_full_text(self):
        # "Ощущается как −2°" → extracts -2
        el = self._el("<span>Ощущается как \u22122°</span>")
        assert YandexWeatherFetcher._extract_temperature(el) == -2.0

    def test_extract_float_strips_units(self):
        el = self._el("<span>750 мм рт. ст.</span>")
        assert YandexWeatherFetcher._extract_float(el) == 750.0

    def test_extract_int_strips_percent(self):
        el = self._el("<span>85%</span>")
        assert YandexWeatherFetcher._extract_int(el) == 85

    def test_extract_text_stripped(self):
        el = self._el("<div>  Ясно  </div>")
        assert YandexWeatherFetcher._extract_text(el) == "Ясно"


# ---------------------------------------------------------------------------
# fetch_current (full pipeline via mocked HTTP)
# ---------------------------------------------------------------------------

class TestFetchCurrentAsync:
    @pytest.mark.asyncio
    async def test_returns_data_from_json_on_200(self, fetcher):
        mock_session = _mock_http(200, _NEXTJS_HTML)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch_current("Санкт-Петербург")
        assert result["temperature"] == 1.0
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
        assert await fetcher.fetch_forecast("Moscow") == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_any_days(self, fetcher):
        assert await fetcher.fetch_forecast("Moscow", days=7) == []


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------

class TestConnectionTest:
    @pytest.mark.asyncio
    async def test_returns_true_when_json_present(self, fetcher):
        mock_session = _mock_http(200, _NEXTJS_HTML)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher.test_connection() is True

    @pytest.mark.asyncio
    async def test_returns_true_when_css_fallback_matches(self, fetcher):
        mock_session = _mock_http(200, _CSS_ONLY_HTML)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            assert await fetcher.test_connection() is True

    @pytest.mark.asyncio
    async def test_returns_false_when_no_data(self, fetcher):
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
