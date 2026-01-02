"""Helpers for constructing TimeNote objects and filenames."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, time
from pathlib import Path

from time_bot.models import TimeEntry, TimeNote
from time_bot.time_utils import get_now_time


_SAFE_TITLE_PATTERN = re.compile(r"[^0-9A-Za-zА-Яа-яЁё _-]+")


def _sanitize_title(title: str) -> str:
    normalized = re.sub(r"\s+", " ", title.strip())
    cleaned = _SAFE_TITLE_PATTERN.sub("", normalized)
    safe = cleaned.replace(" ", "_")
    return safe or "note"


def build_note(
    entry: TimeEntry,
    base_dir: Path,
    timezone,
    *,
    existing_time: time | None = None,
) -> TimeNote:
    """Create a note structure with deterministic identifiers."""

    created_at = datetime.now(timezone)
    start_or_now = entry.start_time or existing_time or get_now_time(timezone)
    safe_title = _sanitize_title(entry.title)
    file_name = f"{safe_title}_{entry.date.isoformat()}_{start_or_now.strftime('%H-%M')}.md"
    file_path = base_dir / file_name
    note_id = uuid.uuid4().hex

    return TimeNote(
        note_id=note_id,
        file_name=file_name,
        file_path=str(file_path),
        created_at=created_at,
        entry=entry,
    )


__all__ = ["build_note"]
