"""High-level pipeline utilities: message text -> note."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from aiogram.types import Message

from time_bot.config import get_settings
from time_bot.logging_utils import log_event
from time_bot.models import MessageClassification, TaskEntry, TimeEntry
from time_bot.note_builder import build_note, build_task_note
from time_bot.note_renderer import render_markdown
from time_bot.obsidian_writer import write_note_file
from time_bot.sgr_client import (
    classify_message_intent,
    parse_task_entry_with_sgr,
    parse_time_entry_with_sgr,
)
from time_bot.time_utils import get_timezone, get_today

TASK_TIMEZONE = "Europe/Moscow"


class UnsupportedIntentError(RuntimeError):
    """Raised when an intent is classified but not supported yet."""

    def __init__(self, intent: str):
        super().__init__(f"Intent '{intent}' is not supported yet.")
        self.intent = intent

@dataclass(slots=True)
class PipelineResult:
    note_path: Path
    markdown: str
    file_name: str
    classification: MessageClassification
    note_type: str
    time_entry: TimeEntry | None = None
    task_entry: TaskEntry | None = None


async def process_message_text(
    text: str,
    *,
    today: date | None = None,
    output_dir: Path | None = None,
) -> PipelineResult:
    settings = get_settings()
    tz = get_timezone(settings.timezone)
    today_value = today or get_today(tz)
    base_dir = output_dir or Path(settings.obsidian_vault_dir)
    if output_dir is not None:
        tasks_dir = Path(output_dir) / "tasks"
    else:
        tasks_dir = Path(settings.obsidian_tasks_path)

    classification = await classify_message_intent(text)
    if classification.intent == "time_log":
        return await _process_time_log(
            text,
            today_value=today_value,
            base_dir=base_dir,
            tz=tz,
            classification=classification,
        )
    if classification.intent == "task":
        return await _process_task(
            text,
            today_value=today_value,
            tasks_dir=tasks_dir,
            timezone=tz,
            classification=classification,
        )

    raise UnsupportedIntentError(classification.intent)


async def process_message(message: Message, **kwargs) -> PipelineResult:
    text = message.text or message.caption or ""
    text = text.strip()
    if not text:
        raise ValueError("Empty message")
    return await process_message_text(text, **kwargs)


async def _process_time_log(
    text: str,
    *,
    today_value: date,
    base_dir: Path,
    tz,
    classification: MessageClassification,
) -> PipelineResult:
    entry = await parse_time_entry_with_sgr(text, today_value)
    note = build_note(entry, base_dir, tz)
    markdown = render_markdown(note)
    note_path = write_note_file(note.file_path, markdown)

    log_event(
        {
            "status": "success",
            "kind": "time_log",
            "raw_text": text,
            "intent": classification.intent,
            "minutes": entry.minutes,
            "maintag": entry.maintag,
            "subtag": entry.subtag,
            "date": entry.date.isoformat(),
            "file_name": note.file_name,
            "file_path": str(note_path),
        }
    )

    return PipelineResult(
        note_path=note_path,
        markdown=markdown,
        file_name=note.file_name,
        classification=classification,
        note_type="time_log",
        time_entry=entry,
    )


async def _process_task(
    text: str,
    *,
    today_value: date,
    tasks_dir: Path,
    timezone,
    classification: MessageClassification,
) -> PipelineResult:
    task_entry = await parse_task_entry_with_sgr(text, today_value, TASK_TIMEZONE)
    note = build_task_note(task_entry, tasks_dir, timezone)
    markdown = render_markdown(note)
    note_path = write_note_file(note.file_path, markdown)

    log_event(
        {
            "status": "success",
            "kind": "task",
            "raw_text": text,
            "intent": classification.intent,
            "title": task_entry.title,
            "project": task_entry.project,
            "due": task_entry.due.isoformat() if task_entry.due else None,
            "file_name": note.file_name,
            "file_path": str(note_path),
        }
    )

    return PipelineResult(
        note_path=note_path,
        markdown=markdown,
        file_name=note.file_name,
        classification=classification,
        note_type="task",
        task_entry=task_entry,
    )


__all__ = ["process_message_text", "process_message", "PipelineResult", "UnsupportedIntentError"]
