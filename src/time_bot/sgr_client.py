"""Structured parsing client powered by an OpenAI-compatible endpoint."""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from openai import AsyncOpenAI
from openai import APIError
from openai import OpenAIError

from time_bot.config import get_settings
from time_bot.models import TimeEntry


class SGRParseError(RuntimeError):
    """Raised when SGR cannot parse a message."""


SYSTEM_PROMPT = """Ты — парсер временных записей.
На входе сообщение пользователя о том, чем он занимался и сколько времени потратил.
Нужно извлечь структуру TimeEntry:
- title — короткое описание занятия.
- minutes — длительность в минутах (часы переводи в минуты).
- date — дата события (YYYY-MM-DD); если дата не указана, используй предоставленное значение.
- start_time — время начала (HH:MM), если явно указано.
- maintag — одна из категорий: w1 (сложная мыслительная работа), w2 (вторичная работа и общение),
            rt (рутина: спорт, гигиена, быт, путь от одного места до другого, приёмы пищи),
            rest (отдых, прогулки, походы в кино, театр и т.п., встречи с друзьями).
- subtag — конкретизация занятия. Возможные значения:
  coding, wasting, social, walking, gym, writing, reading, systematization,
  watching, technical, learning, health, waiting, other.
- comment — произвольный комментарий, если есть дополнительные детали.
- raw_text — полный оригинальный текст сообщения.
Соблюдай следующие правила:
1. Не выдумывай факты — только то, что явно есть в тексте.
2. Если дата не указана, используй значение из дополнительного JSON во входе.
3. minutes должны быть > 0 и <= 720.
4. maintag и subtag выбирай по смыслу занятия, учитывая дополнительные уточнения: если человек пишет комментарий вроде
   «на самом деле это была лекция» или «видео по работе», нужно использовать соответствующие рабочие теги (например,
   w1 + learning), даже если основная активность похожа на отдых.
   Приёмы пищи следует относить к rt и subtag=rest.
5. Все текстовые поля (особенно title) должны быть на языке оригинального сообщения, ничего не переводить.
6. subtag обязан быть из списка выше, если ничего не подходит — используй other.
7. Ответ формируй строго в формате JSON, соответствующем схеме.
"""

USER_PROMPT_TEMPLATE = """Тебе передан текст сообщения пользователя и контекстные поля.
Сначала внимательно изучи JSON с подсказками, затем сам текст.

Контекст:
{context_json}

Сообщение:
<<<
{message}
>>>

Если в тексте нет даты, используй date из контекста.
raw_text обязан точно совпадать с сообщением выше.
Верни только JSON без пояснений.
"""


class _Message(TypedDict):
    role: str
    content: str


def _build_context_json(message_text: str, today: date) -> str:
    context = {
        "raw_text": message_text,
        "date": today.isoformat(),
    }
    return json.dumps(context, ensure_ascii=False)


def _build_messages(message_text: str, today: date) -> List[_Message]:
    context_json = _build_context_json(message_text, today)
    user_prompt = USER_PROMPT_TEMPLATE.format(context_json=context_json, message=message_text)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


@lru_cache()
def _load_schema() -> Dict[str, Any]:
    root_dir = Path(__file__).resolve().parent.parent.parent
    schema_path = root_dir / "schemas" / "time_entry.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


_CLIENT: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _CLIENT
    if _CLIENT is None:
        settings = get_settings()
        _CLIENT = AsyncOpenAI(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key.get_secret_value(),
        )
    return _CLIENT


def _extract_json_text(content: str) -> str:
    """Some models wrap JSON with stray characters; try to isolate the first full object."""

    text = content.strip()
    length = len(text)
    for start in range(length):
        if text[start] != "{":
            continue
        depth = 0
        for end in range(start, length):
            char = text[end]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : end + 1]
        # unmatched braces, try next start
    return text


async def parse_time_entry_with_sgr(message_text: str, today: date) -> TimeEntry:
    """Call the structured parsing model and validate the result."""

    client = _get_client()
    settings = get_settings()
    messages = _build_messages(message_text, today)
    schema = _load_schema()
    try:
        response = await client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "time_entry", "schema": schema},
            },
        )
    except (APIError, OpenAIError, ConnectionError) as exc:
        raise SGRParseError(f"Failed to call SGR endpoint: {exc}") from exc

    if not response.choices:
        raise SGRParseError("LLM returned no choices")

    content = response.choices[0].message.content
    if not content:
        raise SGRParseError("LLM response content is empty")

    if isinstance(content, list):
        # Some providers may return a list of content parts.
        content_str = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    else:
        content_str = content

    try:
        payload = json.loads(_extract_json_text(content_str))
    except json.JSONDecodeError as exc:
        raise SGRParseError(f"LLM returned invalid JSON: {exc}\nContent: {content_str}") from exc

    payload.setdefault("raw_text", message_text)
    payload.setdefault("date", today.isoformat())

    try:
        entry = TimeEntry.model_validate(payload)
    except Exception as exc:
        raise SGRParseError(f"Response does not match schema: {exc}\nPayload: {payload}") from exc

    return entry


__all__ = ["SGRParseError", "parse_time_entry_with_sgr"]
