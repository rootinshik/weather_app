"""Bot entry point."""

import asyncio
import logging

from app.bot import create_api_client, create_bot, create_dispatcher
from app.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    api_client = create_api_client()
    bot = create_bot()
    dp = create_dispatcher(api_client)

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await api_client.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
