from __future__ import annotations

from datetime import timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery

from ..services.condition_service import ConditionService
from ..services.breath_reminder_service import BreathReminderService
from ..services.time_service import TimeService
from ..ui.callbacks import (
    BreathReminderAction,
    BreathSeverityAction,
    BreathSkipAction,
    OtherAction,
)
from ..ui.keyboards import (
    breath_reminder_keyboard,
    breath_severity_keyboard,
    other_menu_keyboard,
    start_keyboard,
)

router = Router()

_condition_service: ConditionService | None = None
_time_service: TimeService | None = None
_reminder_service: BreathReminderService | None = None


def setup_dependencies(
    condition_service: ConditionService,
    time_service: TimeService,
    reminder_service: BreathReminderService,
) -> None:
    global _condition_service, _time_service, _reminder_service
    _condition_service = condition_service
    _time_service = time_service
    _reminder_service = reminder_service


def _get_condition_service() -> ConditionService:
    if _condition_service is None:  # pragma: no cover - wiring issue
        raise RuntimeError("ConditionService is not configured")
    return _condition_service


def _get_time_service() -> TimeService:
    if _time_service is None:  # pragma: no cover - wiring issue
        raise RuntimeError("TimeService is not configured")
    return _time_service


def _get_reminder_service() -> BreathReminderService:
    if _reminder_service is None:  # pragma: no cover - wiring issue
        raise RuntimeError("ReminderService is not configured")
    return _reminder_service


@router.callback_query(OtherAction.filter(F.action == "menu"))
async def cb_other_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Выберите дополнительную опцию:", reply_markup=other_menu_keyboard()
    )


@router.callback_query(OtherAction.filter(F.action == "back"))
async def cb_other_back(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("Главное меню:", reply_markup=start_keyboard())


@router.callback_query(OtherAction.filter(F.action == "breath"))
async def cb_breath_start(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Какой запах изо рта утром?", reply_markup=breath_severity_keyboard()
    )


@router.callback_query(BreathSeverityAction.filter())
async def cb_breath_severity(
    callback: CallbackQuery, callback_data: BreathSeverityAction
) -> None:
    service = _get_condition_service()
    timestamp = _get_time_service().now()
    await service.persist_breath(timestamp, callback_data.level)
    await callback.answer()
    await callback.message.answer(
        "Записал запах изо рта.", reply_markup=start_keyboard()
    )


@router.callback_query(OtherAction.filter(F.action == "reminder"))
async def cb_breath_reminder(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Выберите время напоминания:", reply_markup=breath_reminder_keyboard()
    )


@router.callback_query(BreathReminderAction.filter())
async def cb_breath_reminder_time(
    callback: CallbackQuery, callback_data: BreathReminderAction
) -> None:
    if not callback.from_user:
        await callback.answer("Не удалось определить пользователя.", show_alert=True)
        return
    reminder_service = _get_reminder_service()
    time_value = _restore_time(callback_data.time)
    await reminder_service.add_or_update(
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id if callback.message else callback.from_user.id,
        time_str=time_value,
    )
    await callback.answer()
    await callback.message.answer(
        f"Напоминание установлено на {time_value}.", reply_markup=start_keyboard()
    )


@router.callback_query(BreathSkipAction.filter())
async def cb_breath_skip(callback: CallbackQuery) -> None:
    await callback.answer("Напоминание пропущено.")
    await callback.message.answer(
        "Напоминание пропущено. Запись не изменена.", reply_markup=start_keyboard()
    )


@router.callback_query(OtherAction.filter(F.action == "devtest"))
async def cb_breath_reminder_devtest(callback: CallbackQuery) -> None:
    if not callback.from_user:
        await callback.answer("Не удалось определить пользователя.", show_alert=True)
        return
    reminder_service = _get_reminder_service()
    now = _get_time_service().now()
    special_time = (now + timedelta(seconds=20)).strftime("%Y-%m-%d_%H:%M:%S")
    await reminder_service.add_or_update(
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id if callback.message else callback.from_user.id,
        time_str=special_time,
        one_shot=True,
    )
    await callback.answer()
    await callback.message.answer(
        "Тестовое напоминание придёт через 20 секунд.", reply_markup=start_keyboard()
    )


def _restore_time(raw: str) -> str:
    if ":" in raw:
        return raw
    if len(raw) == 4:
        return f"{raw[:2]}:{raw[2:]}"
    return raw
