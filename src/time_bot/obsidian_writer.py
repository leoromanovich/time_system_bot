"""File writer utilities for Obsidian notes."""
from __future__ import annotations

from pathlib import Path


def write_note_file(path: str | Path, content: str) -> Path:
    """Persist note content to disk, creating parents when necessary."""

    note_path = Path(path)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(content, encoding="utf-8")
    return note_path


__all__ = ["write_note_file"]
