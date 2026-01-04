from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from ..domain.models import Condition, ConditionDraft
from ..fsm.states import ConditionStandaloneStates
from ..services.condition_service import ConditionService
from ..services.time_service import TimeService
from ..ui.callbacks import ConditionBoolAction, ConditionWellBeingAction, AddFlowAction
from ..ui.keyboards import (
    condition_bool_keyboard,
    condition_well_being_keyboard,
    start_keyboard,
)

router = Router()

_condition_service: ConditionService | None = None
_time_service: TimeService | None = None


def setup_dependencies(condition_service: ConditionService, time_service: TimeService) -> None:
    global _condition_service, _time_service
    _condition_service = condition_service
    _time_service = time_service


def _get_services() -> tuple[ConditionService, TimeService]:
    if _condition_service is None or _time_service is None:  # pragma: no cover
        raise RuntimeError("Condition handler dependencies are not configured")
    return _condition_service, _time_service


@router.callback_query(AddFlowAction.filter(F.action == "condition"))
async def cb_start_condition(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ConditionStandaloneStates.ask_bloating)
    await state.update_data(condition=ConditionDraft().model_dump())
    await callback.answer()
    await callback.message.answer(
        "Отдельная запись самочувствия. Есть ли вздутие?",
        reply_markup=condition_bool_keyboard("bloating"),
    )


@router.callback_query(
    ConditionStandaloneStates.ask_bloating,
    ConditionBoolAction.filter(),
)
async def cb_condition_standalone_bloating(
    callback: CallbackQuery, callback_data: ConditionBoolAction, state: FSMContext
) -> None:
    if callback_data.value == "cancel":
        await _cancel(callback, state)
        return
    if callback_data.symptom != "bloating":
        await callback.answer("Этот вопрос про вздутие.", show_alert=True)
        return

    condition = await _get_condition(state)
    condition.bloating = callback_data.value == "yes"
    await state.update_data(condition=condition.model_dump())
    await state.set_state(ConditionStandaloneStates.ask_diarrhea)
    await callback.answer()
    await callback.message.answer(
        "Есть ли диарея?", reply_markup=condition_bool_keyboard("diarrhea")
    )


@router.callback_query(
    ConditionStandaloneStates.ask_diarrhea,
    ConditionBoolAction.filter(),
)
async def cb_condition_standalone_diarrhea(
    callback: CallbackQuery, callback_data: ConditionBoolAction, state: FSMContext
) -> None:
    if callback_data.value == "cancel":
        await _cancel(callback, state)
        return
    if callback_data.symptom != "diarrhea":
        await callback.answer("Этот вопрос про диарею.", show_alert=True)
        return

    condition = await _get_condition(state)
    condition.diarrhea = callback_data.value == "yes"
    await state.update_data(condition=condition.model_dump())
    await state.set_state(ConditionStandaloneStates.ask_well_being)
    await callback.answer()
    await callback.message.answer(
        "Оцените самочувствие от 1 (плохо) до 10 (отлично).",
        reply_markup=condition_well_being_keyboard(),
    )


@router.callback_query(
    ConditionStandaloneStates.ask_well_being,
    ConditionWellBeingAction.filter(),
)
async def cb_condition_standalone_well_being(
    callback: CallbackQuery, callback_data: ConditionWellBeingAction, state: FSMContext
) -> None:
    condition = await _get_condition(state)
    condition.well_being = callback_data.score
    if not condition.is_complete:
        await callback.answer("Пожалуйста, ответьте на все вопросы.", show_alert=True)
        return

    service, time_service = _get_services()
    model = Condition(
        bloating=bool(condition.bloating),
        diarrhea=bool(condition.diarrhea),
        well_being=condition.well_being or 1,
    )
    timestamp = time_service.now()
    short_id = time_service.short_id()
    await service.persist(timestamp=timestamp, short_id=short_id, condition=model)
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "Самочувствие сохранено в ConditionLog. Спасибо!", reply_markup=start_keyboard()
    )


async def _get_condition(state: FSMContext) -> ConditionDraft:
    data = await state.get_data()
    condition_data = data.get("condition") or ConditionDraft().model_dump()
    return ConditionDraft.model_validate(condition_data)


async def _cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "Запись самочувствия отменена.", reply_markup=start_keyboard()
    )
