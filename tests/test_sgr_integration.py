import json
import socket
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pytest

from time_bot.config import get_settings
from time_bot.sgr_client import parse_time_entry_with_sgr

SAMPLES_PATH = Path("tests/data/time_messages_samples.jsonl")


def _llm_available(base_url: str) -> bool:
    parsed = urlparse(base_url)
    host = parsed.hostname
    if not host:
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _load_samples():
    samples = []
    for line in SAMPLES_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        samples.append(json.loads(line))
    return samples


@pytest.mark.anyio
async def test_sgr_outputs_match_samples():
    settings = get_settings()
    if not _llm_available(settings.openai_base_url):
        pytest.skip("OpenAI-compatible endpoint is not reachable")

    today = date.today()
    samples = _load_samples()
    for sample in samples:
        entry = await parse_time_entry_with_sgr(sample["input"], today)
        expected = sample["expected"]
        for field, expected_value in expected.items():
            actual_value = getattr(entry, field)
            assert actual_value == expected_value, (
                f"Field {field} mismatch for '{sample['input']}':"
                f" expected {expected_value}, got {actual_value}"
            )
