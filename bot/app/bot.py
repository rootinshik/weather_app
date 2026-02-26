"""Bot and Dispatcher factory."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.handlers import help, start
from app.middlewares.user_tracking import UserTrackingMiddleware
from app.services.api_client import BackendAPIClient


def create_api_client() -> BackendAPIClient:
    return BackendAPIClient(
        base_url=settings.backend_base_url,
        timeout=settings.backend_timeout,
    )


def create_bot() -> Bot:
    return Bot(
        token=settings.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(api_client: BackendAPIClient) -> Dispatcher:
    dp = Dispatcher()

    # Register middleware
    dp.message.middleware(UserTrackingMiddleware(api_client))

    # Register routers
    dp.include_router(start.router)
    dp.include_router(help.router)

    return dp
