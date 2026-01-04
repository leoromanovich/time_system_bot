from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .callbacks import (
    AddFlowAction,
    BreathReminderAction,
    BreathSeverityAction,
    BreathSkipAction,
    ConditionBoolAction,
    ConditionWellBeingAction,
    OtherAction,
)


def start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить еду", callback_data=AddFlowAction(action="start"))
    builder.button(text="Самочувствие", callback_data=AddFlowAction(action="condition"))
    builder.button(text="Другое", callback_data=OtherAction(action="menu"))
    builder.button(text="Вернуться к трекингу времени", callback_data=OtherAction(action="back_time"))
    builder.adjust(1)
    return builder.as_markup()


def adding_foods_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Продолжить ввод", callback_data=AddFlowAction(action="continue"))
    builder.button(text="Завершить", callback_data=AddFlowAction(action="finish"))
    builder.button(text="Отменить", callback_data=AddFlowAction(action="cancel"))
    builder.button(
        text="Распознать состав по фото",
        callback_data=AddFlowAction(action="photo_start"),
    )
    builder.button(
        text="Предположить состав",
        callback_data=AddFlowAction(action="guess_start"),
    )
    builder.adjust(1)
    return builder.as_markup()


def confirm_finish_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Сохранить и продолжить", callback_data=AddFlowAction(action="confirm"))
    builder.button(text="Вернуться к вводу", callback_data=AddFlowAction(action="back"))
    builder.button(text="Отменить", callback_data=AddFlowAction(action="cancel"))
    builder.adjust(1)
    return builder.as_markup()


def condition_bool_keyboard(symptom: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Да",
        callback_data=ConditionBoolAction(symptom=symptom, value="yes"),
    )
    builder.button(
        text="Нет",
        callback_data=ConditionBoolAction(symptom=symptom, value="no"),
    )
    builder.button(
        text="Отменить",
        callback_data=ConditionBoolAction(symptom=symptom, value="cancel"),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def condition_well_being_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for score in range(1, 11):
        builder.button(
            text=str(score),
            callback_data=ConditionWellBeingAction(score=score),
        )
    builder.adjust(5)
    return builder.as_markup()


def other_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Запах изо рта",
        callback_data=OtherAction(action="breath"),
    )
    builder.button(
        text="Напоминание о запахе",
        callback_data=OtherAction(action="reminder"),
    )
    builder.button(
        text="Тест напоминания (20 секунд)",
        callback_data=OtherAction(action="devtest"),
    )
    builder.button(text="Назад", callback_data=OtherAction(action="back"))
    builder.adjust(1)
    return builder.as_markup()


def breath_severity_keyboard(include_skip: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Сильный", callback_data=BreathSeverityAction(level="strong"))
    builder.button(text="Средний", callback_data=BreathSeverityAction(level="medium"))
    builder.button(text="Слабый", callback_data=BreathSeverityAction(level="weak"))
    builder.button(text="Нет", callback_data=BreathSeverityAction(level="none"))
    if include_skip:
        builder.button(text="Пропустить", callback_data=BreathSkipAction())
    builder.adjust(2)
    return builder.as_markup()


def breath_reminder_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = ["06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00"]
    for option in options:
        builder.button(
            text=option,
            callback_data=BreathReminderAction(time=option.replace(":", "")),
        )
    builder.button(text="Отмена", callback_data=OtherAction(action="back"))
    builder.adjust(3)
    return builder.as_markup()


def composition_result_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Добавить как есть",
        callback_data=AddFlowAction(action="composition_accept"),
    )
    builder.button(
        text="Распознать заново",
        callback_data=AddFlowAction(action="composition_retry"),
    )
    builder.button(
        text="Отменить",
        callback_data=AddFlowAction(action="cancel"),
    )
    builder.adjust(1)
    return builder.as_markup()
