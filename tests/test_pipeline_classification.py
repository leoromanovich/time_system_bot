from datetime import date

import pytest

from time_bot.models import MessageClassification, TimeEntry
from time_bot.pipeline import process_message_text


@pytest.mark.anyio
async def test_process_message_returns_classification(tmp_path, monkeypatch):
    sample_text = "30 минут чтения"
    fake_classification = MessageClassification(
        intent="time_log",
        raw_text=sample_text,
        explanation="Starts with minutes.",
    )

    async def _fake_classify(message_text: str):
        assert message_text == sample_text
        return fake_classification

    async def _fake_parse(message_text: str, today: date):
        assert message_text == sample_text
        return TimeEntry(
            title="Чтение",
            raw_text=message_text,
            minutes=30,
            date=today,
            start_time=None,
            maintag="w1",
            subtag="reading",
            comment=None,
        )

    monkeypatch.setattr("time_bot.pipeline.classify_message_intent", _fake_classify)
    monkeypatch.setattr("time_bot.pipeline.parse_time_entry_with_sgr", _fake_parse)

    result = await process_message_text(sample_text, today=date(2024, 1, 1), output_dir=tmp_path)
    assert result.classification.intent == "time_log"
    assert result.classification.raw_text == sample_text
    assert result.entry_minutes == 30
