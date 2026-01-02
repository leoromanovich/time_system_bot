"""Utilities for aggregating time entries from Obsidian notes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class DailyStats:
    date: date
    minutes_by_maintag: dict[str, int]

    @property
    def total_minutes(self) -> int:
        return sum(self.minutes_by_maintag.values())


def _iter_markdown_files(base_dir: Path) -> Iterable[Path]:
    if not base_dir.exists():
        return []
    return base_dir.glob("*.md")


def _parse_frontmatter(path: Path) -> dict[str, str]:
    frontmatter: dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            first_line = handle.readline().strip()
            if first_line != "---":
                return frontmatter
            for line in handle:
                stripped = line.strip()
                if stripped == "---":
                    break
                if ":" not in stripped:
                    continue
                key, value = stripped.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                if key in {"time", "date", "maintag"}:
                    frontmatter[key] = value
    except OSError:
        return {}
    return frontmatter


def get_daily_stats(base_dir: Path, target_date: date) -> DailyStats:
    minutes_by_maintag: dict[str, int] = {}
    for note_path in _iter_markdown_files(base_dir):
        frontmatter = _parse_frontmatter(note_path)
        if not frontmatter:
            continue
        entry_date = frontmatter.get("date")
        if entry_date != target_date.isoformat():
            continue
        maintag = frontmatter.get("maintag")
        if not maintag:
            continue
        try:
            minutes = int(frontmatter.get("time", "0"))
        except ValueError:
            continue
        minutes_by_maintag[maintag] = minutes_by_maintag.get(maintag, 0) + minutes
    return DailyStats(date=target_date, minutes_by_maintag=minutes_by_maintag)


__all__ = ["DailyStats", "get_daily_stats"]
