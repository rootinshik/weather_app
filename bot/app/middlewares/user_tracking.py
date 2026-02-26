"""User tracking middleware — registers every Telegram user in the backend."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from app.services.api_client import BackendAPIClient

logger = logging.getLogger(__name__)


class UserTrackingMiddleware(BaseMiddleware):
    """On every incoming message, identify the user via the backend API.

    Injects ``backend_user`` (dict or None) into handler data so handlers
    can access the backend user record without making extra API calls.
    """

    def __init__(self, api_client: BackendAPIClient) -> None:
        self.api = api_client
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        backend_user: dict | None = None

        if isinstance(event, Message) and event.from_user:
            tg_user = event.from_user
            try:
                backend_user = await self.api.identify_user(
                    platform="telegram",
                    external_id=str(tg_user.id),
                )
            except Exception as exc:
                logger.error("UserTracking: identify_user failed: %s", exc)

        data["backend_user"] = backend_user
        return await handler(event, data)
