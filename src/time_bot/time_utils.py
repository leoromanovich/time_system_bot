"""Helpers for dealing with timezone-aware datetimes."""
from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo


def get_timezone(tz_name: str) -> ZoneInfo:
    """Return ZoneInfo instance with graceful fallback to UTC."""

    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")


def get_today(tz: ZoneInfo) -> date:
    """Return today's date in the provided timezone."""

    return datetime.now(tz).date()


def get_now_time(tz: ZoneInfo) -> time:
    """Return the current time rounded to minutes for filenames."""

    current = datetime.now(tz)
    return current.replace(second=0, microsecond=0).time()


__all__ = ["get_timezone", "get_today", "get_now_time"]
