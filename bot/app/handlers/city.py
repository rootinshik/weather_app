"""Handlers for /city command and city-selection callbacks."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import cities_keyboard
from app.services.api_client import BackendAPIClient

logger = logging.getLogger(__name__)
router = Router(name="city")


@router.message(Command("city"))
async def cmd_city(
    message: Message,
    command: CommandObject,
    api_client: BackendAPIClient,
    backend_user: dict | None = None,
) -> None:
    """/city — показать текущий город; /city <название> — поиск и выбор города."""
    city_query = (command.args or "").strip()

    if not city_query:
        preferred = backend_user.get("preferred_city_id") if backend_user else None
        if preferred:
            text = (
                f"Текущий город по умолчанию: <b>#{preferred}</b>\n\n"
                "Чтобы сменить, отправь /city название_города."
            )
        else:
            text = "Город не задан.\n\nОтправь /city название_города, чтобы выбрать."
        await message.answer(text, parse_mode="HTML")
        return

    cities = await api_client.search_cities(city_query)
    if not cities:
        await message.answer(f"❌ Город <b>{city_query}</b> не найден.", parse_mode="HTML")
        return

    kb = cities_keyboard(cities)
    await message.answer("Выбери город из списка:", reply_markup=kb)


@router.callback_query(F.data.startswith("city_select:"))
async def on_city_select(
    callback: CallbackQuery,
    api_client: BackendAPIClient,
) -> None:
    """Handle city selection from the inline keyboard."""
    parts = (callback.data or "").split(":", 2)
    if len(parts) < 3:
        await callback.answer("Некорректный запрос.", show_alert=True)
        return

    city_id = int(parts[1])
    city_name = parts[2]

    user = await api_client.identify_user("telegram", str(callback.from_user.id))
    if not user:
        await callback.answer("Не удалось получить профиль.", show_alert=True)
        return

    updated = await api_client.update_preferences(user["id"], preferred_city_id=city_id)
    if updated:
        if callback.message:
            await callback.message.edit_text(
                f"✅ Город установлен: <b>{city_name}</b>",
                parse_mode="HTML",
            )
    else:
        await callback.answer("Не удалось сохранить выбор.", show_alert=True)
        return

    await callback.answer()
