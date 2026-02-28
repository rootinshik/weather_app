"""Micro-tests for weather text formatters."""

import pytest

from app.services.formatters import (
    format_current_weather,
    format_forecast,
    format_recommendation,
    format_sources,
)


class TestFormatCurrentWeather:
    def _weather(self, **kwargs) -> dict:
        base = {
            "temperature": 10.0,
            "feels_like": 8.0,
            "wind_speed": 5.0,
            "humidity": 70,
            "description": "ясно",
        }
        base.update(kwargs)
        return {"weather": base}

    def test_contains_city_name(self):
        text = format_current_weather("Москва", self._weather())
        assert "Москва" in text

    def test_contains_temperature(self):
        text = format_current_weather("City", self._weather(temperature=15.5))
        assert "15.5" in text

    def test_sunny_emoji(self):
        text = format_current_weather("City", self._weather(description="ясно"))
        assert "☀️" in text

    def test_rain_emoji(self):
        text = format_current_weather("City", self._weather(description="дождь"))
        assert "🌧" in text

    def test_snow_emoji(self):
        text = format_current_weather("City", self._weather(description="снег"))
        assert "❄️" in text

    def test_none_temperature_shows_dash(self):
        text = format_current_weather("City", self._weather(temperature=None))
        assert "—" in text

    def test_html_bold_city(self):
        text = format_current_weather("Питер", self._weather())
        assert "<b>" in text and "Питер" in text


class TestFormatForecast:
    def _forecast_data(self, n: int = 3) -> dict:
        forecasts = []
        for i in range(n):
            forecasts.append({
                "forecast_dt": f"2026-02-0{i + 1}T12:00:00",
                "weather": {"temperature": float(i), "description": "облачно"},
            })
        return {"forecasts": forecasts}

    def test_contains_city_name(self):
        text = format_forecast("Казань", self._forecast_data())
        assert "Казань" in text

    def test_contains_all_points(self):
        text = format_forecast("City", self._forecast_data(3))
        assert text.count("01.02") == 1
        assert text.count("02.02") == 1
        assert text.count("03.02") == 1

    def test_empty_forecasts(self):
        text = format_forecast("City", {"forecasts": []})
        assert "City" in text

    def test_invalid_date_shows_dash(self):
        data = {"forecasts": [{"forecast_dt": "bad-date", "weather": {}}]}
        text = format_forecast("City", data)
        assert "—" in text


class TestFormatRecommendation:
    def test_label_shown(self):
        rec = {"label": "Лёгкая куртка", "tips": []}
        text = format_recommendation(rec)
        assert "Лёгкая куртка" in text

    def test_tips_shown(self):
        rec = {"label": "X", "tips": ["Возьми зонт", "Шарф"]}
        text = format_recommendation(rec)
        assert "Возьми зонт" in text
        assert "Шарф" in text

    def test_fallback_to_recommendation_key(self):
        rec = {"recommendation": "Пальто"}
        text = format_recommendation(rec)
        assert "Пальто" in text

    def test_empty_rec_shows_dash(self):
        text = format_recommendation({})
        assert "—" in text


class TestFormatSources:
    def test_lists_source_slugs(self):
        sources = [
            {"slug": "openweathermap", "priority": 3, "is_enabled": True},
            {"slug": "weatherapi", "priority": 2, "is_enabled": False},
        ]
        text = format_sources(sources)
        assert "openweathermap" in text
        assert "weatherapi" in text

    def test_enabled_checkmark(self):
        text = format_sources([{"slug": "s", "priority": 1, "is_enabled": True}])
        assert "✅" in text

    def test_disabled_cross(self):
        text = format_sources([{"slug": "s", "priority": 1, "is_enabled": False}])
        assert "❌" in text

    def test_empty_list(self):
        text = format_sources([])
        assert "не найдены" in text.lower()
