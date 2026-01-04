from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from ..domain.models import Condition, FoodEventDraft, PersistedEvent
from ..domain.normalize import deduplicate_preserve_order, normalize_food_name
from .condition_service import ConditionService
from .file_store import FileStore
from .foods_service import FoodsService
from .markdown_helpers import build_log_filename, render_frontmatter
from .time_service import TimeService


@dataclass(slots=True)
class FoodEventRecord:
    food_log_path: Path
    condition_log_path: Path


class FoodEventService:
    def __init__(
        self,
        file_store: FileStore,
        foods_service: FoodsService,
        condition_service: ConditionService,
        time_service: TimeService,
        food_log_dir: str = "FoodLog",
    ):
        self.file_store = file_store
        self.foods_service = foods_service
        self.condition_service = condition_service
        self.time_service = time_service
        self.food_log_dir = food_log_dir

    async def persist_event(
        self, draft: FoodEventDraft, condition: Condition
    ) -> PersistedEvent:
        normalized_foods = self._normalize_foods(draft.foods_raw)
        if not normalized_foods:
            raise ValueError("Cannot persist event without foods")

        await self.foods_service.ensure_notes(normalized_foods)

        timestamp = self.time_service.now()
        short_id = self.time_service.short_id()

        food_log_path = await self._write_food_log(timestamp, short_id, normalized_foods)
        condition_record = await self.condition_service.persist(
            timestamp=timestamp, short_id=short_id, condition=condition
        )

        return PersistedEvent(
            food_log_path=str(food_log_path),
            condition_log_path=str(condition_record.path),
            foods=normalized_foods,
        )

    async def _write_food_log(
        self, timestamp: datetime, short_id: str, foods: List[str]
    ):
        filename = build_log_filename(timestamp, short_id)
        payload = {
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M"),
            "foods": [f"[[{food}]]" for food in foods],
        }
        content = render_frontmatter(payload)
        return await self.file_store.write_text(Path(self.food_log_dir) / filename, content)

    def _normalize_foods(self, foods: Iterable[str]) -> List[str]:
        normalized = [normalize_food_name(food) for food in foods if food.strip()]
        return deduplicate_preserve_order(normalized)
