from __future__ import annotations

from datetime import datetime
from typing import List, Sequence

from pydantic import BaseModel, Field, validator


class FoodEventDraft(BaseModel):
    started_at: datetime
    foods_raw: List[str] = Field(default_factory=list)
    foods_normalized: List[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    def append_foods(self, foods: Sequence[str]) -> None:
        self.foods_raw.extend(foods)


class Condition(BaseModel):
    bloating: bool
    diarrhea: bool
    well_being: int = Field(ge=1, le=10)


class PersistedEvent(BaseModel):
    food_log_path: str
    condition_log_path: str
    foods: List[str]


class ConditionDraft(BaseModel):
    bloating: bool | None = None
    diarrhea: bool | None = None
    well_being: int | None = None

    @property
    def is_complete(self) -> bool:
        return (
            self.bloating is not None
            and self.diarrhea is not None
            and self.well_being is not None
        )
