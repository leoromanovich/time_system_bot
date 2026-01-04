from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from .file_store import FileStore


@dataclass
class BreathReminder:
    user_id: int
    chat_id: int
    time: str
    last_sent_date: str | None = None
    one_shot: bool = False


class BreathReminderService:
    def __init__(self, file_store: FileStore, filename: str = "breath_reminders.json"):
        self._path = file_store.resolve(filename)
        self._lock = asyncio.Lock()
        self._reminders: List[BreathReminder] = self._load()

    def _load(self) -> List[BreathReminder]:
        if not self._path.exists():
            return []
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return [BreathReminder(**item) for item in data]

    def _save(self) -> None:
        payload = [asdict(item) for item in self._reminders]
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    async def add_or_update(self, user_id: int, chat_id: int, time_str: str, *, one_shot: bool = False) -> None:
        async with self._lock:
            for reminder in self._reminders:
                if reminder.user_id == user_id:
                    reminder.chat_id = chat_id
                    reminder.time = time_str
                    reminder.one_shot = one_shot
                    self._save()
                    return
            self._reminders.append(
                BreathReminder(user_id=user_id, chat_id=chat_id, time=time_str, one_shot=one_shot)
            )
            self._save()

    async def get_due(self, time_str: str, date_str: str) -> List[BreathReminder]:
        async with self._lock:
            return [
                reminder
                for reminder in self._reminders
                if reminder.time == time_str
                and (reminder.one_shot or reminder.last_sent_date != date_str)
            ]

    async def get_due_one_shot(self, timestamp: str) -> List[BreathReminder]:
        async with self._lock:
            return [
                reminder
                for reminder in self._reminders
                if reminder.one_shot and reminder.time <= timestamp
            ]

    async def mark_sent(self, reminder: BreathReminder, date_str: str) -> None:
        async with self._lock:
            for stored in self._reminders:
                if stored.user_id == reminder.user_id:
                    if stored.one_shot:
                        self._reminders.remove(stored)
                    else:
                        stored.last_sent_date = date_str
                    break
            self._save()
