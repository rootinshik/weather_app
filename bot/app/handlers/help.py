"""Handler for /help command."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

HELP_TEXT = """\
<b>Доступные команды:</b>

/start — приветствие и регистрация
/help — список команд

<i>Скоро появятся команды для получения погоды, прогноза и рекомендаций по одежде.</i>
"""


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Show the list of available bot commands."""
    await message.answer(HELP_TEXT, parse_mode="HTML")
