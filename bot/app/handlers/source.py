"""Handler for /source command."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.api_client import BackendAPIClient
from app.services.formatters import format_sources

logger = logging.getLogger(__name__)
router = Router(name="source")


@router.message(Command("source"))
async def cmd_source(
    message: Message,
    api_client: BackendAPIClient,
) -> None:
    """/source — показать список источников данных."""
    sources = await api_client.get_sources()
    text = format_sources(sources)
    await message.answer(text, parse_mode="HTML")
