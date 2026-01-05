"""Reusable utilities for bot handlers."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List

from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from time_bot.config import get_settings
from time_bot.logging_utils import log_event
from time_bot.pipeline import PipelineResult, UnsupportedIntentError, process_message_text
from time_bot.sgr_client import SGRParseError
from time_bot.stats import get_daily_stats
from time_bot.task_reader import TaskRecord, read_tasks
from time_bot.time_utils import get_timezone, get_today

STATS_BUTTON_TEXT = "Статистика за сегодня"
TASKS_BUTTON_TEXT = "Задачи"


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=STATS_BUTTON_TEXT), KeyboardButton(text=TASKS_BUTTON_TEXT)]],
        resize_keyboard=True,
    )


def build_daily_stats_message() -> str:
    settings = get_settings()
    tz = get_timezone(settings.timezone)
    today = get_today(tz)
    stats = get_daily_stats(settings.obsidian_vault_dir, today)
    if not stats.minutes_by_maintag:
        return "Нет записей за сегодня."
    lines = [f"Статистика за {today.isoformat()}:"]
    for maintag, minutes in sorted(stats.minutes_by_maintag.items()):
        lines.append(f"- {maintag}: {minutes} мин")
    lines.append(f"Итого: {stats.total_minutes} мин")
    return "\n".join(lines)


def build_tasks_overview_message() -> str:
    settings = get_settings()
    tasks_dir = Path(settings.obsidian_tasks_path)
    if not tasks_dir.exists():
        return "Папка с задачами не найдена."
    tz = get_timezone(settings.timezone)
    today = get_today(tz)
    tasks = [task for task in read_tasks(tasks_dir) if not task.done]
    if not tasks:
        return "Нет открытых задач."

    sections = [
        ("Сегодня", sorted([t for t in tasks if t.due == today], key=_due_sort_key)),
        ("Просроченные", sorted([t for t in tasks if t.due and t.due < today], key=_due_sort_key)),
        ("Будущие", sorted([t for t in tasks if t.due and t.due > today], key=_due_sort_key)),
        ("Без даты", sorted([t for t in tasks if t.due is None], key=lambda t: t.title.lower())),
    ]

    lines: List[str] = ["Открытые задачи:"]
    for title, items in sections:
        if not items:
            continue
        lines.append(f"{title}:")
        for idx, task in enumerate(items, start=1):
            lines.append(f"{idx}. {_format_task_line(task, tasks_dir)}")
        lines.append("")
    if lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _due_sort_key(task: TaskRecord):
    return (task.due or date.max, task.title.lower())


def _format_task_line(task: TaskRecord, tasks_dir: Path) -> str:
    due_text = task.due.isoformat() if task.due else "без даты"
    try:
        rel_path = task.file_path.relative_to(tasks_dir)
    except ValueError:
        rel_path = task.file_path.name
    return f"{due_text} — {task.title} [{rel_path}]"


async def handle_time_entry_message(message: Message) -> None:
    text = (message.text or message.caption or "").strip()
    if not text:
        await message.answer(
            "Сообщение пустое. Опиши активность и длительность.",
            reply_markup=get_main_keyboard(),
        )
        return
    try:
        result = await process_message_text(text)
    except UnsupportedIntentError as exc:
        log_event({"status": "error", "raw_text": text, "error": str(exc)})
        await message.answer(
            "Эта категория сообщений пока не поддерживается.",
            reply_markup=get_main_keyboard(),
        )
        return
    except SGRParseError as exc:
        log_event({"status": "error", "raw_text": text, "error": str(exc)})
        await message.answer(
            "Не смог разобрать сообщение. Уточни длительность и что делал.",
            reply_markup=get_main_keyboard(),
        )
        return
    except Exception as exc:  # unexpected failure
        log_event({"status": "error", "raw_text": text, "error": str(exc)})
        await message.answer(
            "Произошла ошибка при обработке сообщения.",
            reply_markup=get_main_keyboard(),
        )
        return
    await message.answer(_build_success_message(result), reply_markup=get_main_keyboard())


def _build_success_message(result: PipelineResult) -> str:
    if result.note_type == "time_log" and result.time_entry:
        entry = result.time_entry
        return "\n".join(
            [
                "Запись создана",
                f"{entry.minutes} мин, maintag={entry.maintag}, subtag={entry.subtag or '-'}",
                f"Файл: {result.file_name}",
            ]
        )
    if result.note_type == "task" and result.task_entry:
        entry = result.task_entry
        due_text = entry.due.isoformat() if entry.due else "не указано"
        project_text = ", ".join(entry.project)
        return "\n".join(
            [
                "Задача создана",
                entry.title,
                f"Срок: {due_text}",
                f"Проект: {project_text}",
                f"Файл: {result.file_name}",
            ]
        )
    if result.note_type == "diary" and result.diary_entry:
        entry = result.diary_entry
        timestamp = entry.created_at.strftime("%Y-%m-%d %H-%M")
        return "\n".join(
            [
                "Запись в дневник создана",
                entry.title,
                f"Дата: {timestamp}",
                f"Файл: {result.file_name}",
            ]
        )
    return "Запись создана"


__all__ = [
    "STATS_BUTTON_TEXT",
    "TASKS_BUTTON_TEXT",
    "get_main_keyboard",
    "build_daily_stats_message",
    "build_tasks_overview_message",
    "handle_time_entry_message",
]
