"""Integration helpers to wire the food tracker into the main bot."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from aiogram import Dispatcher

from time_bot.config import Settings
from time_bot.food_tracker.handlers import add_food, breath, condition, common, photo
from time_bot.food_tracker.services.breath_reminder_service import (
    BreathReminderService,
)
from time_bot.food_tracker.services.breath_scheduler import BreathReminderScheduler
from time_bot.food_tracker.services.composition_extractor import CompositionExtractor
from time_bot.food_tracker.services.condition_service import ConditionService
from time_bot.food_tracker.services.file_store import FileStore
from time_bot.food_tracker.services.food_event_service import FoodEventService
from time_bot.food_tracker.services.foods_service import FoodsService
from time_bot.food_tracker.services.photo_intake import (
    PhotoIntakeConfig,
    PhotoIntakeService,
    PhotoIntakeStubService,
)
from time_bot.food_tracker.services.time_service import TimeService


@dataclass(slots=True)
class FoodTrackerConfig:
    storage_dir: Path
    timezone: ZoneInfo
    model_name: str
    model_endpoint: str
    model_api_key: str
    photo_intake_url: str | None
    photo_intake_token: str | None


@dataclass(slots=True)
class FoodTrackerRuntime:
    scheduler: BreathReminderScheduler


def _build_config(settings: Settings) -> FoodTrackerConfig:
    storage_dir = (
        settings.food_track_obsidian_vault_dir
        if settings.food_track_obsidian_vault_dir is not None
        else settings.obsidian_vault_dir / "FoodTracker"
    )
    storage_dir = storage_dir.expanduser()

    timezone = ZoneInfo(settings.timezone)

    model_name = settings.food_track_model_name or settings.model_name
    base_endpoint = settings.food_track_model_endpoint or settings.openai_base_url
    endpoint = base_endpoint.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint = f"{endpoint}/chat/completions"

    api_key = (
        settings.food_track_openai_api_key.get_secret_value()
        if settings.food_track_openai_api_key is not None
        else settings.openai_api_key.get_secret_value()
    )

    return FoodTrackerConfig(
        storage_dir=storage_dir,
        timezone=timezone,
        model_name=model_name,
        model_endpoint=endpoint,
        model_api_key=api_key,
        photo_intake_url=settings.food_track_photo_intake_url,
        photo_intake_token=settings.food_track_photo_intake_token,
    )


def _include_routers(dp: Dispatcher, routers: Iterable) -> None:
    for router in routers:
        dp.include_router(router)


def setup_food_tracker(dp: Dispatcher, settings: Settings) -> FoodTrackerRuntime:
    """
    Configure dependencies, register routers, and return runtime hooks for the
    food tracker module.
    """

    config = _build_config(settings)
    file_store = FileStore(config.storage_dir)
    time_service = TimeService(config.timezone)
    foods_service = FoodsService(file_store)
    condition_service = ConditionService(file_store)
    breath_service = BreathReminderService(file_store)
    food_event_service = FoodEventService(
        file_store=file_store,
        foods_service=foods_service,
        condition_service=condition_service,
        time_service=time_service,
    )
    composition_extractor = CompositionExtractor(
        model=config.model_name,
        endpoint=config.model_endpoint,
        api_key=config.model_api_key,
    )

    if config.photo_intake_url:
        photo_service: PhotoIntakeService = PhotoIntakeService(
            PhotoIntakeConfig(
                url=config.photo_intake_url,
                token=config.photo_intake_token,
            )
        )
    else:
        photo_service = PhotoIntakeStubService()

    add_food.setup_dependencies(food_event_service, time_service, composition_extractor)
    condition.setup_dependencies(condition_service, time_service)
    breath.setup_dependencies(condition_service, time_service, breath_service)
    photo.setup_dependencies(photo_service, time_service)

    _include_routers(
        dp,
        (
            add_food.router,
            condition.router,
            breath.router,
            photo.router,
            common.router,
        ),
    )

    scheduler = BreathReminderScheduler(breath_service, time_service)
    return FoodTrackerRuntime(scheduler=scheduler)


__all__ = ["setup_food_tracker", "FoodTrackerRuntime"]
