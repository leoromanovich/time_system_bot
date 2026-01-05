"""Telegram handlers placeholders."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from time_bot.bot.utils import (
    STATS_BUTTON_TEXT,
    TASKS_BUTTON_TEXT,
    build_daily_stats_message,
    build_tasks_overview_message,
    get_main_keyboard,
    handle_time_entry_message,
)

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет! Отправь описание активности, например '30 минут спортзал'.",
        reply_markup=get_main_keyboard(),
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(
        "Напиши, чем занимался и сколько времени ушло. Я превращу сообщение в заметку Obsidian.",
        reply_markup=get_main_keyboard(),
    )


@router.message(lambda message: (message.text or "") == STATS_BUTTON_TEXT)
async def handle_daily_stats(message: Message) -> None:
    await message.answer(build_daily_stats_message(), reply_markup=get_main_keyboard())


@router.message(lambda message: (message.text or "") == TASKS_BUTTON_TEXT)
async def handle_tasks_list(message: Message) -> None:
    await message.answer(build_tasks_overview_message(), reply_markup=get_main_keyboard())


@router.message()
async def handle_entry(message: Message) -> None:
    await handle_time_entry_message(message)
