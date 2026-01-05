from datetime import date
from pathlib import Path

import pytest

from time_bot.bot import utils as bot_utils
from time_bot.task_reader import TaskRecord, read_tasks


def _write_task_file(path: Path, due: str, done: str = "false") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "tags:",
                "  - task",
                f"done: {done}",
                "status: not started",
                "priority: 1",
                f"due: {due}",
                "project:",
                "  - routine",
                "---",
                "Тестовая задача",
                "",
                "Описание задачи:",
                "> Задача для теста",
            ]
        ),
        encoding="utf-8",
    )


def test_read_tasks_parses_frontmatter(tmp_path):
    file_path = tmp_path / "task1.md"
    _write_task_file(file_path, "2025-07-30")

    records = read_tasks(tmp_path)
    assert len(records) == 1
    record = records[0]
    assert record.title == "Тестовая задача"
    assert record.due == date(2025, 7, 30)
    assert record.done is False
    assert record.file_path == file_path


@pytest.mark.anyio
async def test_build_tasks_overview_message_orders_sections(monkeypatch, tmp_path):
    records = [
        TaskRecord("Сегодня", date(2025, 7, 30), False, tmp_path / "today.md"),
        TaskRecord("Просроченная", date(2025, 7, 29), False, tmp_path / "over.md"),
        TaskRecord("Будущая", date(2025, 8, 2), False, tmp_path / "future.md"),
        TaskRecord("Без даты", None, False, tmp_path / "none.md"),
        TaskRecord("Сделана", date(2025, 7, 30), True, tmp_path / "done.md"),
    ]

    class DummySettings:
        obsidian_tasks_path = tmp_path
        timezone = "Europe/Moscow"
        obsidian_vault_dir = tmp_path

    monkeypatch.setattr(bot_utils, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(bot_utils, "read_tasks", lambda _: records)
    monkeypatch.setattr(bot_utils, "get_today", lambda tz: date(2025, 7, 30))

    message = bot_utils.build_tasks_overview_message()
    today_idx = message.index("Сегодня:")
    overdue_idx = message.index("Просроченные:")
    future_idx = message.index("Будущие:")
    undated_idx = message.index("Без даты:")
    assert today_idx < overdue_idx < future_idx < undated_idx
    assert "Сделана" not in message
