"""Append-only logging helpers for processed messages."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from time_bot.config import get_settings

LOG_FILE_NAME = "processed_messages.jsonl"
LOGGER_NAME = "time_bot"


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


LOGGER = _setup_logger()


def _log_path() -> Path:
    settings = get_settings()
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / LOG_FILE_NAME


def log_event(data: Mapping[str, Any]) -> None:
    """Append a JSON event to the log file and emit console output."""

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

    status = payload.get("status", "info")
    raw_text = payload.get("raw_text", "")
    if status == "success":
        LOGGER.info(
            "Processed message | minutes=%s maintag=%s subtag=%s file=%s | text=%s",
            payload.get("minutes"),
            payload.get("maintag"),
            payload.get("subtag"),
            payload.get("file_name"),
            raw_text,
        )
    else:
        LOGGER.error(
            "Failed to process message | error=%s | text=%s",
            payload.get("error"),
            raw_text,
        )


__all__ = ["log_event", "LOGGER", "LOGGER_NAME"]
