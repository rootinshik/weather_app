"""Handler for /start command."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, backend_user: dict | None = None) -> None:
    """Greet the user and confirm registration in the backend."""
    first_name = message.from_user.first_name if message.from_user else "друг"

    if backend_user:
        user_id = backend_user.get("id")
        greeting = (
            f"Привет, {first_name}! 👋\n\n"
            f"Я бот агрегатора погоды. Твой ID в системе: <b>{user_id}</b>.\n\n"
            "Используй /help, чтобы узнать о доступных командах."
        )
    else:
        greeting = (
            f"Привет, {first_name}! 👋\n\n"
            "Я бот агрегатора погоды, но сейчас не могу связаться с сервером. "
            "Попробуй позже.\n\n"
            "Используй /help, чтобы узнать о доступных командах."
        )

    await message.answer(greeting, parse_mode="HTML")
