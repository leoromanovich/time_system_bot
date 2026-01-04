from __future__ import annotations

import socket
import asyncio
from typing import Sequence, Tuple

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import ClientTimeout, TCPConnector

from .config import Settings, load_settings
from .handlers import add_food, breath, common, condition, photo, start
from .logging_setup import setup_logging
from .services.composition_extractor import CompositionExtractor
from .services.breath_reminder_service import BreathReminderService
from .services.breath_scheduler import BreathReminderScheduler
from .services.condition_service import ConditionService
from .services.file_store import FileStore
from .services.food_event_service import FoodEventService
from .services.foods_service import FoodsService
from .services.photo_intake import (
    PhotoIntakeConfig,
    PhotoIntakeService,
    PhotoIntakeStubService,
)
from .services.time_service import TimeService


def build_dispatcher(settings: Settings) -> Tuple[Dispatcher, BreathReminderScheduler]:
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)

    file_store = FileStore(settings.data_dir)
    time_service = TimeService(settings.timezone)
    foods_service = FoodsService(file_store)
    condition_service = ConditionService(file_store)
    composition_extractor = CompositionExtractor()
    breath_reminder_service = BreathReminderService(file_store)
    if settings.photo_intake_url:
        photo_config = PhotoIntakeConfig(
            url=settings.photo_intake_url,
            token=settings.photo_intake_token,
        )
        photo_intake_service = PhotoIntakeService(photo_config)
    else:
        photo_intake_service = PhotoIntakeStubService()
    food_event_service = FoodEventService(
        file_store=file_store,
        foods_service=foods_service,
        condition_service=condition_service,
        time_service=time_service,
    )
    add_food.setup_dependencies(food_event_service, time_service, composition_extractor)
    condition.setup_dependencies(condition_service, time_service)
    breath.setup_dependencies(condition_service, time_service, breath_reminder_service)
    photo.setup_dependencies(photo_intake_service, time_service)

    breath_scheduler = BreathReminderScheduler(breath_reminder_service, time_service)

    routers: Sequence = (
        start.router,
        add_food.router,
        breath.router,
        condition.router,
        photo.router,
        common.router,
    )
    for router in routers:
        dispatcher.include_router(router)

    return dispatcher, breath_scheduler


class IPv4AiohttpSession(AiohttpSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TCPConnector будет создан с этими параметрами
        self._connector_init["family"] = socket.AF_INET
        self._should_reset_connector = True

async def run() -> None:
    setup_logging()
    settings = load_settings()
    dispatcher, breath_scheduler = build_dispatcher(settings)
    session = IPv4AiohttpSession(
        timeout=30,  # можно 30-60
    )
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )

    @dispatcher.startup.register
    async def _on_startup() -> None:
        await breath_scheduler.start(bot)

    @dispatcher.shutdown.register
    async def _on_shutdown() -> None:
        await breath_scheduler.stop()

    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run())
