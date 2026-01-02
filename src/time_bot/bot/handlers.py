"""Telegram handlers placeholders."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from time_bot.bot.utils import handle_time_entry_message

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer("Привет! Отправь описание активности, например '30 минут спортзал'.")


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(
        "Напиши, чем занимался и сколько времени ушло. Я превращу сообщение в заметку Obsidian."
    )


@router.message()
async def handle_entry(message: Message) -> None:
    await handle_time_entry_message(message)
