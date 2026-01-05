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
from time_bot.models import MessageClassification, TaskEntry, TimeEntry


class SGRParseError(RuntimeError):
    """Raised when SGR cannot parse a message."""


TIME_ENTRY_SYSTEM_PROMPT = """Ты — парсер временных записей.
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
   Приёмы пищи следует относить к maintag=rt и subtag=rest (наприме, "30 минут Обед").
5. Все текстовые поля (особенно title) должны быть на языке оригинального сообщения, ничего не переводить.
6. subtag обязан быть из списка выше, если ничего не подходит — используй other.
7. Ответ формируй строго в формате JSON, соответствующем схеме.
"""

TIME_ENTRY_USER_PROMPT_TEMPLATE = """Тебе передан текст сообщения пользователя и контекстные поля.
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

CLASSIFIER_SYSTEM_PROMPT = """Ты — классификатор входящих сообщений для личного бота.
Нужно определить, к какой из трёх категорий относится текст:
- time_log — пользователь явно логирует, сколько минут потратил на активность (например «30 минут чтения книги»). Если сообщение начинается с числа минут, часов или содержит шаблон «N минут», «час», «за 25 мин» и т.д., почти всегда это time_log.
- journal — размышления, заметки в дневник, описание состояний или событий без конкретного запроса на действие.
- task — просьба добавить задачу/to-do, план на будущее или четкое намерение сделать что-то позже.
Подсказки:
1. Если сообщение начинается с количества минут или содержит тайм-коды, предпочитай time_log.
2. Если текст описывает эмоции, мысли, наблюдения о прошедшем дне без указания длительности — это journal.
3. Если есть формулировки «нужно», «надо», «планирую», «добавь задачу», то это task.
4. Когда сомневаешься между journal и task, выбирай task только если явно просится действие или задача.
Ответ формируй строго по схеме JSON.
Примеры time_log:
30 минут Обед
15 мин Путь на работу
50 минут смотрел ютуб (rest)
"""

CLASSIFIER_USER_PROMPT_TEMPLATE = """Определи назначение сообщения: task, journal или time_log.

Сообщение:
<<<
{message}
>>>

Верни JSON строго по схеме. raw_text должен совпадать с текстом выше. В explanation кратко поясни, на чём основано решение.
"""

TASK_SYSTEM_PROMPT = """Ты — парсер задач для личного бота.
Нужно извлечь структуру TaskEntry:
- title — короткое название задачи на языке пользователя.
- raw_text — оригинальный текст запроса.
- due — дата дедлайна (YYYY-MM-DD). Если срок не указан явно, верни null. Если указан относительный срок (сегодня, завтра, в пятницу и т.д.), вычисляй дату относительно значения date из контекста с учётом timezone (это московское время).
- project — массив значений coding или routine. Используй coding, если задача связана с программированием/кодингом/разработкой; иначе routine.
Соблюдай правила:
1. Не выдумывай детали — только то, что есть в тексте.
2. Если упомянута конкретная дата, используй её как due.
3. Если упомянуто «завтра», «через два дня» и т.п., вычисляй дату относительно date из контекста.
4. Даже если срок не указан, всегда формируй осмысленный title.
5. Ответ должен строго соответствовать JSON-схеме.
"""

TASK_USER_PROMPT_TEMPLATE = """Разбери задачу по схеме TaskEntry. Контекст содержит текущую дату и таймзону (Москва).

Контекст:
{context_json}

Сообщение:
<<<
{message}
>>>

Верни только JSON. raw_text обязан совпадать с текстом выше.
"""


class _Message(TypedDict):
    role: str
    content: str


def _build_context_json(message_text: str, today: date, timezone: str | None = None) -> str:
    context = {
        "raw_text": message_text,
        "date": today.isoformat(),
    }
    if timezone:
        context["timezone"] = timezone
    return json.dumps(context, ensure_ascii=False)


def _build_time_entry_messages(message_text: str, today: date, timezone: str) -> List[_Message]:
    context_json = _build_context_json(message_text, today, timezone)
    user_prompt = TIME_ENTRY_USER_PROMPT_TEMPLATE.format(context_json=context_json, message=message_text)
    return [
        {"role": "system", "content": TIME_ENTRY_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _build_task_messages(message_text: str, today: date, timezone: str) -> List[_Message]:
    context_json = _build_context_json(message_text, today, timezone)
    user_prompt = TASK_USER_PROMPT_TEMPLATE.format(context_json=context_json, message=message_text)
    return [
        {"role": "system", "content": TASK_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


@lru_cache()
def _load_schema(schema_name: str) -> Dict[str, Any]:
    root_dir = Path(__file__).resolve().parent.parent.parent
    schema_path = root_dir / "schemas" / f"{schema_name}.json"
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
    messages = _build_time_entry_messages(message_text, today, settings.timezone)
    schema = _load_schema("time_entry")
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


async def parse_task_entry_with_sgr(message_text: str, today: date, timezone: str) -> TaskEntry:
    """Call the structured parsing model for tasks."""

    client = _get_client()
    settings = get_settings()
    messages = _build_task_messages(message_text, today, timezone)
    schema = _load_schema("task_entry")
    try:
        response = await client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "task_entry", "schema": schema},
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
        content_str = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    else:
        content_str = content

    try:
        payload = json.loads(_extract_json_text(content_str))
    except json.JSONDecodeError as exc:
        raise SGRParseError(f"LLM returned invalid JSON: {exc}\nContent: {content_str}") from exc

    payload.setdefault("raw_text", message_text)
    payload.setdefault("project", ["routine"])

    try:
        entry = TaskEntry.model_validate(payload)
    except Exception as exc:
        raise SGRParseError(f"Response does not match schema: {exc}\nPayload: {payload}") from exc

    return entry


def _build_classification_messages(message_text: str) -> List[_Message]:
    user_prompt = CLASSIFIER_USER_PROMPT_TEMPLATE.format(message=message_text)
    return [
        {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


async def classify_message_intent(message_text: str) -> MessageClassification:
    """Determine whether the text is a task, journal entry, or time log."""

    client = _get_client()
    settings = get_settings()
    messages = _build_classification_messages(message_text)
    schema = _load_schema("message_classification")
    try:
        response = await client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "message_classification", "schema": schema},
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
        content_str = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    else:
        content_str = content

    try:
        payload = json.loads(_extract_json_text(content_str))
    except json.JSONDecodeError as exc:
        raise SGRParseError(f"LLM returned invalid JSON: {exc}\nContent: {content_str}") from exc

    payload.setdefault("raw_text", message_text)

    try:
        return MessageClassification.model_validate(payload)
    except Exception as exc:
        raise SGRParseError(f"Response does not match schema: {exc}\nPayload: {payload}") from exc


__all__ = ["SGRParseError", "parse_time_entry_with_sgr", "parse_task_entry_with_sgr", "classify_message_intent"]
