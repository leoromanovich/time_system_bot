from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..ui.keyboards import start_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я помогу зафиксировать приём пищи. Нажмите “Добавить еду”, чтобы начать.",
        reply_markup=start_keyboard(),
    )

