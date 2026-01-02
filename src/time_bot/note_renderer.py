"""Utilities for turning a TimeNote into Markdown."""
from __future__ import annotations

from time_bot.models import TimeNote


def render_markdown(note: TimeNote) -> str:
    """Render note into Obsidian-friendly Markdown."""

    entry = note.entry
    frontmatter_lines = [
        "---",
        "tags:",
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


__all__ = ["render_markdown"]
