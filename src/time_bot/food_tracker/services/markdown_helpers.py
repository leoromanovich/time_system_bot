from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import yaml


def build_log_filename(timestamp: datetime, short_id: str) -> str:
    slug = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    return f"{slug}_{short_id}.md"


def render_frontmatter(payload: Dict[str, Any]) -> str:
    yaml_body = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{yaml_body}\n---\n\n#foodtracker\n"
