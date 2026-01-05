"""Utilities for turning note models into Markdown."""
from __future__ import annotations

from time_bot.models import TaskNote, TimeNote


def render_markdown(note: TimeNote | TaskNote) -> str:
    """Render note into Obsidian-friendly Markdown."""

    if isinstance(note, TimeNote):
        return _render_time_entry(note)
    if isinstance(note, TaskNote):
        return _render_task(note)
    raise TypeError(f"Unsupported note type: {type(note)!r}")


def _render_time_entry(note: TimeNote) -> str:
    entry = note.entry
    frontmatter_lines = [
        "---",
        "tags: task",
        "  - time_system",
        f"time: {entry.minutes}",
        f"date: {entry.date.isoformat()}",
        f"maintag: {entry.maintag}",
    ]
    if entry.subtag:
        frontmatter_lines.append(f"subtag: {entry.subtag}")
    frontmatter_lines.append("---")

    body_lines = [entry.title, ""]
    if entry.comment:
        body_lines.append(entry.comment)
        body_lines.append("")
    body_lines.append("Исходный текст:")
    body_lines.append(f"> {entry.raw_text}")
    body = "\n".join(body_lines)

    return "\n".join(frontmatter_lines) + "\n\n" + body + "\n"


def _render_task(note: TaskNote) -> str:
    entry = note.entry
    due_value = entry.due.isoformat() if entry.due else ""
    projects = entry.project or ["routine"]
    frontmatter_lines = [
        "---",
        "tags:",
        "  - task",
        "done: false",
        "status: not started",
        "priority: 1",
        f"due: {due_value}",
        "project:",
    ]
    for project in projects:
        frontmatter_lines.append(f"  - {project}")
    frontmatter_lines.append("---")

    body_lines = [
        entry.title,
        "",
        "Описание задачи:",
        f"> {entry.raw_text}",
    ]

    return "\n".join(frontmatter_lines) + "\n\n" + "\n".join(body_lines) + "\n"


__all__ = ["render_markdown"]
