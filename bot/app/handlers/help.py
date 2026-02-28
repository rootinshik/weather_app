"""Handler for /help command."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

HELP_TEXT = """\
<b>Доступные команды:</b>

/start — приветствие и регистрация
/help — список команд

<b>Погода:</b>
/weather [город] — текущая погода + рекомендация по одежде
/forecast [город] — прогноз на 3 дня

<b>Настройки:</b>
/city — показать текущий город
/city &lt;название&gt; — выбрать город по умолчанию
/source — список источников данных

<i>Если город не указан — используется город по умолчанию.</i>
"""


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Show the list of available bot commands."""
    await message.answer(HELP_TEXT, parse_mode="HTML")
