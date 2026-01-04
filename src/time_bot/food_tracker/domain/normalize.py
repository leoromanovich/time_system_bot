from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List

SAFE_FILENAME_PATTERN = re.compile(r"[^\w\s\-\(\)%]+", re.UNICODE)
MULTISPACE = re.compile(r"\s+")


def normalize_food_name(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = MULTISPACE.sub(" ", cleaned)
    return cleaned


def deduplicate_preserve_order(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def sanitize_filename(value: str, max_length: int = 120) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    normalized = SAFE_FILENAME_PATTERN.sub("", normalized)
    normalized = MULTISPACE.sub(" ", normalized)
    normalized = normalized.strip().strip(".")
    if not normalized:
        normalized = "food"
    if len(normalized) > max_length:
        normalized = normalized[:max_length].rstrip()
    return normalized
