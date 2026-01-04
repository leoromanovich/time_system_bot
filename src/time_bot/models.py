"""Data models shared across the project."""
from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Maintag = Literal["w1", "w2", "rt", "rest"]
Subtag = Literal[
    "coding",
    "wasting",
    "social",
    "walking",
    "gym",
    "hobby",
    "writing",
    "reading",
    "systematization",
    "watching",
    "technical",
    "learning",
    "health",
    "rest",
    "waiting",
    "other",
]

MessageIntent = Literal["task", "journal", "time_log"]
ProjectTag = Literal["coding", "routine"]


class TimeEntry(BaseModel):
    """Structured information extracted from a natural-language message."""

    title: str = Field(..., min_length=3)
    raw_text: str
    minutes: int = Field(..., ge=1, le=12 * 60)
    date: date
    start_time: Optional[time] = None
    maintag: Maintag
    subtag: Optional[Subtag] = None
    comment: Optional[str] = None


class TimeNote(BaseModel):
    """Metadata for an Obsidian note derived from a time entry."""

    note_id: str
    file_name: str
    file_path: str
    created_at: datetime
    entry: TimeEntry


class MessageClassification(BaseModel):
    """LLM-backed classification for routing incoming messages."""

    intent: MessageIntent
    raw_text: str
    explanation: Optional[str] = None


class TaskEntry(BaseModel):
    """Structured task details for Obsidian task notes."""

    title: str = Field(..., min_length=3)
    raw_text: str
    due: Optional[date] = None
    project: List[ProjectTag] = Field(..., min_length=1)


class TaskNote(BaseModel):
    """Metadata for an Obsidian task note."""

    note_id: str
    file_name: str
    file_path: str
    created_at: datetime
    entry: TaskEntry


__all__ = [
    "Maintag",
    "Subtag",
    "TimeEntry",
    "TimeNote",
    "MessageIntent",
    "MessageClassification",
    "ProjectTag",
    "TaskEntry",
    "TaskNote",
]
