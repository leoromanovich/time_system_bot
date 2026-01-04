"""Bot bootstrap module."""
from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from time_bot.bot.handlers import router
from time_bot.config import Settings, get_settings
from time_bot.food_tracker.integration import FoodTrackerRuntime, setup_food_tracker


def build_dispatcher(settings: Settings) -> tuple[Dispatcher, FoodTrackerRuntime]:
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    food_runtime = setup_food_tracker(dp, settings)
    return dp, food_runtime


async def run_bot() -> None:
    settings = get_settings()
    bot = Bot(settings.telegram_bot_token.get_secret_value())
    dp, food_runtime = build_dispatcher(settings)

    @dp.startup.register
    async def _on_startup() -> None:
        await food_runtime.scheduler.start(bot)

    @dp.shutdown.register
    async def _on_shutdown() -> None:
        await food_runtime.scheduler.stop()

    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
