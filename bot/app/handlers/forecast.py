"""Handler for /forecast command."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from app.services.api_client import BackendAPIClient
from app.services.formatters import format_forecast

logger = logging.getLogger(__name__)
router = Router(name="forecast")

_DEFAULT_DAYS = 3


@router.message(Command("forecast"))
async def cmd_forecast(
    message: Message,
    command: CommandObject,
    api_client: BackendAPIClient,
    backend_user: dict | None = None,
) -> None:
    """/forecast [город] — прогноз на 3 дня."""
    city_query = (command.args or "").strip()
    city_id: int | None = None
    city_name: str = "Unknown"

    if city_query:
        cities = await api_client.search_cities(city_query, limit=1)
        if not cities:
            await message.answer(f"❌ Город <b>{city_query}</b> не найден.")
            return
        city = cities[0]
        city_id = city.get("id") or city.get("city_id")
        city_name = city.get("name", city_query)
    elif backend_user:
        city_id = backend_user.get("preferred_city_id")
        if not city_id:
            await message.answer(
                "Город не задан. Используй /city <название>, чтобы выбрать город по умолчанию."
            )
            return
        city_name = f"город #{city_id}"
    else:
        await message.answer("Не удалось получить профиль. Попробуй позже.")
        return

    forecast_data = await api_client.get_forecast(city_id=city_id, days=_DEFAULT_DAYS)
    if not forecast_data:
        await message.answer("❌ Не удалось получить прогноз. Попробуй позже.")
        return

    text = format_forecast(city_name, forecast_data)
    await message.answer(text, parse_mode="HTML")
