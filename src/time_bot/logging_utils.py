"""Append-only logging helpers for processed messages."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from time_bot.config import get_settings

LOG_FILE_NAME = "processed_messages.jsonl"


def _log_path() -> Path:
    settings = get_settings()
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / LOG_FILE_NAME


def log_event(data: Mapping[str, Any]) -> None:
    """Append a JSON event to the log file."""

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    }
    try:
        path = _log_path()
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False))
            handle.write("\n")
    except OSError:
        # Logging is best-effort; avoid breaking the pipeline.
        pass


__all__ = ["log_event"]
