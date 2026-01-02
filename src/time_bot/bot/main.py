"""Bot bootstrap module."""
from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher

from time_bot.config import get_settings
from time_bot.bot.handlers import router


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def run_bot() -> None:
    settings = get_settings()
    bot = Bot(settings.telegram_bot_token.get_secret_value())
    dp = build_dispatcher()
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
