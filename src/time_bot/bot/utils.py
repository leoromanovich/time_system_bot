"""Reusable utilities for bot handlers."""
from __future__ import annotations

from aiogram.types import Message

from time_bot.logging_utils import log_event
from time_bot.pipeline import process_message_text
from time_bot.sgr_client import SGRParseError


async def handle_time_entry_message(message: Message) -> None:
    text = (message.text or message.caption or "").strip()
    if not text:
        await message.answer("Сообщение пустое. Опиши активность и длительность.")
        return
    try:
        result = await process_message_text(text)
    except SGRParseError as exc:
        log_event({"status": "error", "raw_text": text, "error": str(exc)})
        await message.answer(
            "Не смог разобрать сообщение. Уточни длительность и что делал."
        )
        return
    except Exception as exc:  # unexpected failure
        log_event({"status": "error", "raw_text": text, "error": str(exc)})
        await message.answer("Произошла ошибка при обработке сообщения.")
        return
    await message.answer(
        "\n".join(
            [
                "Запись создана",
                f"{result.entry_minutes} мин, maintag={result.maintag}, subtag={result.subtag or '-'}",
                f"Файл: {result.file_name}",
            ]
        )
    )
