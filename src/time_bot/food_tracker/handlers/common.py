from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from time_bot.bot.utils import get_main_keyboard

from ..ui.callbacks import OtherAction

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Сейчас ничего не записывается.")
        return

    await state.clear()
    await message.answer("Диалог отменён. Введите /add, чтобы начать заново.")


@router.callback_query(OtherAction.filter(F.action == "back_time"))
async def cb_back_to_time_tracking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "Вернулся к отслеживанию времени. Просто напишите, чем занимались.",
        reply_markup=get_main_keyboard(),
    )
