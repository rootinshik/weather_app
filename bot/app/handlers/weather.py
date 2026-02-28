"""Handler for /weather command."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from app.services.api_client import BackendAPIClient
from app.services.formatters import format_current_weather, format_recommendation

logger = logging.getLogger(__name__)
router = Router(name="weather")


@router.message(Command("weather"))
async def cmd_weather(
    message: Message,
    command: CommandObject,
    api_client: BackendAPIClient,
    backend_user: dict | None = None,
) -> None:
    """/weather [город] — текущая погода + рекомендация по одежде."""
    city_query = (command.args or "").strip()
    city_id: int | None = None
    city_name: str = "Unknown"

    if city_query:
        cities = await api_client.search_cities(city_query, limit=1)
        if not cities:
            await message.answer(f"❌ Город <b>{city_query}</b> не найден.")
            return
        city = cities[0]
        city_name = city.get("name", city_query)
        created = await api_client.create_city(
            name=city_name,
            country=city.get("country", ""),
            lat=city.get("lat", 0.0),
            lon=city.get("lon", 0.0),
            local_name=city.get("local_name"),
        )
        city_id = created.get("id") if created else None
    elif backend_user:
        city_id = backend_user.get("preferred_city_id")
        if not city_id:
            await message.answer(
                "Город не задан. Используй /city название_города, чтобы выбрать город по умолчанию."
            )
            return
        city_name = f"город #{city_id}"
    else:
        await message.answer("Не удалось получить профиль. Попробуй позже.")
        return

    weather_data = await api_client.get_current_weather(city_id=city_id)
    if not weather_data:
        await message.answer("❌ Не удалось получить данные о погоде. Попробуй позже.")
        return

    text = format_current_weather(city_name, weather_data)

    rec = await api_client.get_recommendation(city_id=city_id)
    if rec:
        text += "\n" + format_recommendation(rec)

    await message.answer(text, parse_mode="HTML")
