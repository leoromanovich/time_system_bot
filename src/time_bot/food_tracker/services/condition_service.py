from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..domain.models import Condition
from .file_store import FileStore
from .markdown_helpers import build_log_filename, render_frontmatter


@dataclass(slots=True)
class ConditionRecord:
    path: Path
    content: str


class ConditionService:
    def __init__(self, file_store: FileStore, log_dir: str = "ConditionLog"):
        self.file_store = file_store
        self.log_dir = log_dir

    async def persist(
        self, timestamp: datetime, short_id: str, condition: Condition
    ) -> ConditionRecord:
        filename = build_log_filename(timestamp, short_id)
        content = self._render_markdown(timestamp, condition)
        path = await self.file_store.write_text(Path(self.log_dir) / filename, content)
        return ConditionRecord(path=path, content=content)

    def _render_markdown(self, timestamp: datetime, condition: Condition) -> str:
        payload = {
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M"),
            "bloating": bool(condition.bloating),
            "diarrhea": bool(condition.diarrhea),
            "well_being": condition.well_being,
        }
        return render_frontmatter(payload)

    async def persist_breath(self, timestamp: datetime, severity: str) -> ConditionRecord:
        filename = f"{timestamp.strftime('%Y-%m-%d')}_breath.md"
        payload = {
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M"),
            "breath_smell": severity,
        }
        content = render_frontmatter(payload)
        path = await self.file_store.write_text(Path(self.log_dir) / filename, content)
        return ConditionRecord(path=path, content=content)
