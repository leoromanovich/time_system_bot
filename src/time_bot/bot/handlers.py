"""Telegram handlers placeholders."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from time_bot.bot.utils import (
    STATS_BUTTON_TEXT,
    ADD_FOOD_BUTTON_TEXT,
    build_daily_stats_message,
    get_main_keyboard,
    handle_time_entry_message,
)
from time_bot.food_tracker.ui.keyboards import start_keyboard

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


@router.message(lambda message: (message.text or "") == ADD_FOOD_BUTTON_TEXT)
async def handle_add_food_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Режим отслеживания питания активен. Выберите действие на клавиатуре ниже.",
        reply_markup=start_keyboard(),
    )


@router.message()
async def handle_entry(message: Message) -> None:
    await handle_time_entry_message(message)
