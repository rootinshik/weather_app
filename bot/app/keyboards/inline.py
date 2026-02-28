"""Inline keyboards for city selection and source display."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

_MAX_CITIES = 8


def cities_keyboard(cities: list[dict]) -> InlineKeyboardMarkup:
    """Build an inline keyboard from a list of city search results.

    Each city dict must contain ``id`` (or ``city_id``), ``name``,
    and optionally ``country``.
    Callback data format: ``city_select:<city_id>:<city_name>``
    """
    builder = InlineKeyboardBuilder()
    for city in cities[:_MAX_CITIES]:
        city_id = city.get("id") or city.get("city_id")
        name = city.get("name", "?")
        country = city.get("country", "")
        label = f"{name}, {country}" if country else name
        builder.button(
            text=label,
            callback_data=f"city_select:{city_id}:{name}",
        )
    builder.adjust(1)
    return builder.as_markup()
