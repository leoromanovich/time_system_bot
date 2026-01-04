"""High-level pipeline utilities: message text -> note."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from aiogram.types import Message

from time_bot.config import get_settings
from time_bot.logging_utils import log_event
from time_bot.models import MessageClassification
from time_bot.note_builder import build_note
from time_bot.note_renderer import render_markdown
from time_bot.obsidian_writer import write_note_file
from time_bot.sgr_client import classify_message_intent, parse_time_entry_with_sgr
from time_bot.time_utils import get_timezone, get_today


@dataclass(slots=True)
class PipelineResult:
    note_path: Path
    markdown: str
    entry_minutes: int
    maintag: str
    subtag: Optional[str]
    file_name: str
    classification: MessageClassification


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

    classification = await classify_message_intent(text)
    entry = await parse_time_entry_with_sgr(text, today_value)
    note = build_note(entry, base_dir, tz)
    markdown = render_markdown(note)
    note_path = write_note_file(note.file_path, markdown)

    log_event(
        {
            "status": "success",
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
        entry_minutes=entry.minutes,
        maintag=entry.maintag,
        subtag=entry.subtag,
        file_name=note.file_name,
        classification=classification,
    )


async def process_message(message: Message, **kwargs) -> PipelineResult:
    text = message.text or message.caption or ""
    text = text.strip()
    if not text:
        raise ValueError("Empty message")
    return await process_message_text(text, **kwargs)


__all__ = ["process_message_text", "process_message", "PipelineResult"]
