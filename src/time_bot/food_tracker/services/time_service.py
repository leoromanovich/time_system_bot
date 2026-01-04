from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import secrets


class TimeService:
    def __init__(self, tz: ZoneInfo):
        self.tz = tz

    def now(self) -> datetime:
        return datetime.now(tz=self.tz)

    def short_id(self, length: int = 8) -> str:
        return secrets.token_hex(length // 2)
