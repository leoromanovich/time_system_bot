from __future__ import annotations

from typing import Literal

from aiogram.filters.callback_data import CallbackData


class AddFlowAction(CallbackData, prefix="addflow"):
    action: Literal[
        "start",
        "continue",
        "finish",
        "cancel",
        "confirm",
        "back",
        "condition",
        "photo_start",
        "guess_start",
        "composition_accept",
        "composition_retry",
    ]


class ConditionBoolAction(CallbackData, prefix="condbool"):
    symptom: Literal["bloating", "diarrhea"]
    value: Literal["yes", "no", "cancel"]


class ConditionWellBeingAction(CallbackData, prefix="condwb"):
    score: int


class OtherAction(CallbackData, prefix="other"):
    action: Literal["menu", "breath", "reminder", "back", "devtest", "back_time"]


class BreathSeverityAction(CallbackData, prefix="breath"):
    level: Literal["strong", "medium", "weak", "none"]


class BreathReminderAction(CallbackData, prefix="breathrem"):
    time: str


class BreathSkipAction(CallbackData, prefix="breathskip"):
    pass
