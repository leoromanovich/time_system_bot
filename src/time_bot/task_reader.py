"""Utilities for reading task notes from the Obsidian vault."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Tuple


@dataclass(slots=True)
class TaskRecord:
    title: str
    due: date | None
    done: bool
    file_path: Path


def read_tasks(tasks_dir: Path) -> List[TaskRecord]:
    """Scan the tasks directory and return parsed task metadata."""

    records: List[TaskRecord] = []
    if not tasks_dir.exists():
        return records
    for path in sorted(tasks_dir.rglob("*.md")):
        record = _parse_task_file(path)
        if record is not None:
            records.append(record)
    return records


def _parse_task_file(path: Path) -> TaskRecord | None:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None

    frontmatter, body_lines = _extract_frontmatter(content.splitlines())
    title = _extract_title(body_lines) or path.stem

    done_value = str(frontmatter.get("done", "")).strip().lower()
    done = done_value in {"true", "yes", "1"}

    due_value = str(frontmatter.get("due", "")).strip()
    due_date = None
    if due_value:
        try:
            due_date = date.fromisoformat(due_value)
        except ValueError:
            due_date = None

    return TaskRecord(title=title, due=due_date, done=done, file_path=path)


def _extract_frontmatter(lines: List[str]) -> Tuple[dict, List[str]]:
    if not lines or lines[0].strip() != "---":
        return {}, lines

    front_lines: List[str] = []
    end_index = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = idx
            break
        front_lines.append(line.rstrip("\n"))
    if end_index is None:
        return {}, lines
    data = _parse_frontmatter_lines(front_lines)
    return data, lines[end_index + 1 :]


def _parse_frontmatter_lines(lines: Iterable[str]) -> dict:
    data: dict = {}
    current_list_key: str | None = None

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            if current_list_key is not None:
                data.setdefault(current_list_key, []).append(stripped[2:].strip())
            continue
        if stripped.startswith("* "):
            if current_list_key is not None:
                data.setdefault(current_list_key, []).append(stripped[2:].strip())
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value == "":
            current_list_key = key
            data[key] = []
        else:
            data[key] = value
            current_list_key = None
    return data


def _extract_title(body_lines: List[str]) -> str | None:
    for line in body_lines:
        if line.strip():
            return line.strip()
    return None


__all__ = ["TaskRecord", "read_tasks"]
