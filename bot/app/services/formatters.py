"""Text formatters for weather bot responses (pure functions — no I/O)."""

from datetime import datetime


def _weather_emoji(description: str | None) -> str:
    if not description:
        return "🌡"
    d = description.lower()
    if any(w in d for w in ("ясно", "clear", "sunny")):
        return "☀️"
    if any(w in d for w in ("гроза", "thunder", "storm")):
        return "⛈"
    if any(w in d for w in ("снег", "snow", "blizzard", "метель")):
        return "❄️"
    if any(w in d for w in ("дождь", "rain", "drizzle", "ливень", "showers")):
        return "🌧"
    if any(w in d for w in ("туман", "fog", "mist")):
        return "🌫"
    if any(w in d for w in ("ветер", "wind")):
        return "💨"
    if any(w in d for w in ("облач", "cloud", "overcast", "пасмур")):
        return "☁️"
    return "🌡"


def format_current_weather(city_name: str, data: dict) -> str:
    """Format AggregatedWeatherResponse dict into an HTML string."""
    weather = data.get("weather", {})
    emoji = _weather_emoji(weather.get("description"))
    temp = weather.get("temperature")
    feels = weather.get("feels_like")
    wind = weather.get("wind_speed")
    humidity = weather.get("humidity")
    desc = weather.get("description") or "—"

    lines = [
        f"{emoji} <b>Погода в {city_name}</b>",
        "",
        f"🌡 Температура: <b>{temp:.1f}°C</b>" if temp is not None else "🌡 Температура: —",
        f"🤔 Ощущается как: {feels:.1f}°C" if feels is not None else "",
        f"💨 Ветер: {wind:.1f} м/с" if wind is not None else "",
        f"💧 Влажность: {humidity}%" if humidity is not None else "",
        f"📝 {desc.capitalize()}",
    ]
    return "\n".join(line for line in lines if line != "")


def format_forecast(city_name: str, data: dict) -> str:
    """Format ForecastResponse dict into an HTML string."""
    forecasts = data.get("forecasts", [])
    lines = [f"📅 <b>Прогноз для {city_name}</b>", ""]
    for point in forecasts:
        try:
            dt = datetime.fromisoformat(str(point["forecast_dt"]).replace("Z", "+00:00"))
            date_str = dt.strftime("%d.%m %H:%M")
        except (KeyError, ValueError):
            date_str = "—"
        weather = point.get("weather", {})
        temp = weather.get("temperature")
        desc = weather.get("description") or "—"
        emoji = _weather_emoji(desc)
        temp_str = f"{temp:.1f}°C" if temp is not None else "—°C"
        lines.append(f"{emoji} <b>{date_str}</b>  {temp_str} — {desc}")
    return "\n".join(lines)


def format_recommendation(rec: dict) -> str:
    """Format ML recommendation dict into an HTML string."""
    label = rec.get("description") or rec.get("label") or rec.get("recommendation") or "—"
    tips: list[str] = rec.get("items") or rec.get("tips") or []
    lines = ["", "👔 <b>Рекомендация:</b>", f"  {label}"]
    for tip in tips:
        lines.append(f"  • {tip}")
    return "\n".join(lines)


def format_sources(sources: list[dict]) -> str:
    """Format a list of source dicts into an HTML string."""
    if not sources:
        return "Источники данных не найдены."
    lines = ["📡 <b>Источники данных:</b>", ""]
    for src in sources:
        slug = src.get("slug", "?")
        priority = src.get("priority", "?")
        enabled = "✅" if src.get("is_enabled", True) else "❌"
        lines.append(f"{enabled} <b>{slug}</b> — приоритет {priority}")
    return "\n".join(lines)
