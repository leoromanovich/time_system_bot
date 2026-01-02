Опишу план по шагам — от схем и SGR до тестов и внедрения в Obsidian.

⸻

0. Уточнение целевой картины

Что должно происходить в итоге:
	1.	Ты пишешь боту в Telegram фразы вида:
	•	«45 мин писал бекенд на fastapi»
	•	«1.5 часа спортзал»
	•	«30 минут болтали с коллегой»
	2.	Бот:
	•	прогоняет текст через LLM+SGR,
	•	получает строгую структуру: title, time, date, maintag, subtag, возможно комментарий,
	•	на основании структуры генерирует готовую Obsidian-заметку (Markdown + YAML-фронтматтер),
	•	сохраняет файл в директорию твоего Obsidian-vault,
	•	опционально присылает тебе результат/подтверждение.

Название файла: "<title> YYYY-MM-DD HH-MM.md" (или аналог).

⸻

1. Проектная структура и стек

1.1. Технологии
	•	Язык: Python (учитывая твой стек и SGR).
	•	Telegram: aiogram или python-telegram-bot (я бы взял aiogram 3).
	•	Pydantic v2 (под SGR-схемы).
	•	Клиент к твоему LLM/SGR (у тебя уже есть chat_sgr_parse*).
	•	Хранение заметок: файловая система (директория Obsidian vault, например ~/Obsidian/time-tracking/).

1.2. Структура репозитория (пример)

time_bot/
  src/
    __init__.py
    config.py
    models.py           # Pydantic модели для SGR
    sgr_client.py       # обёртки над chat_sgr_parse
    note_renderer.py    # генерация Markdown из моделей
    obsidian_writer.py  # запись файлов
    bot/
      __init__.py
      handlers.py       # логика Telegram-хендлеров
      main.py           # запуск бота
  tests/
    test_parsing.py
    test_note_renderer.py
    test_e2e_samples.py
  cache/
    ...
  .env
  pyproject.toml/requirements.txt
  README.md


⸻

2. Целевая схема данных (Pydantic + SGR)

2.1. Сущность для результата разбора сообщения

Вся логика SGR будет крутиться вокруг Pydantic-модели, например:

from datetime import date, time as dtime
from typing import Optional, Literal
from pydantic import BaseModel, Field

Maintag = Literal["w1", "w2", "rt", "rest"]

class TimeEntry(BaseModel):
    """
    Структура одной временной записи, извлечённой из текста пользователя.
    """
    title: str = Field(
        ...,
        description=(
            "Краткое название занятия (на русском), например: "
            "\"работа над бекендом\", \"спортзал\", \"чтение статьи\"."
        ),
        min_length=3,
    )
    raw_text: str = Field(
        ...,
        description="Оригинальный текст сообщения пользователя."
    )
    minutes: int = Field(
        ...,
        ge=1,
        le=12 * 60,
        description="Длительность занятия в минутах. Если указаны часы, перевести в минуты."
    )
    date: date = Field(
        ...,
        description="Дата занятия в формате YYYY-MM-DD. Если не указана, считать сегодняшнюю."
    )
    start_time: Optional[dtime] = Field(
        None,
        description="Время начала (локальное), если оно явно указано в тексте."
    )
    maintag: Maintag = Field(
        ...,
        description=(
            "Основной тип активности: "
            "w1 – сложная мыслительная работа, "
            "w2 – вторичная работа и соц.взаимодействия, "
            "rt – рутина (гигиена, быт, спорт и т.д.), "
            "rest – отдых от работы."
        )
    )
    subtag: Optional[str] = Field(
        None,
        description=(
            "Более конкретный тип активности: "
            "например 'coding', 'social', 'reading', 'sports', 'hygiene' и т.д."
        )
    )
    comment: Optional[str] = Field(
        None,
        description="Свободный комментарий, если в тексте есть дополнительные детали."
    )

Примечания:
	•	Maintag — Literal для жёсткой фиксации допустимых значений.
	•	date мы подставляем до запроса (если в сообщении ничего про дату нет → берём «сегодня»).
	•	raw_text тоже заполняем заранее и не просим LLM его угадывать (из принципов SGR).

2.2. Модель для внутреннего использования (ID, файл и т.д.)

Ещё один слой, уже после SGR:

class TimeNote(BaseModel):
    """
    Готовая к сохранению заметка для Obsidian.
    """
    note_id: str
    file_name: str
    file_path: str
    entry: TimeEntry
    created_at_iso: str

note_id, file_name, file_path, created_at_iso заполняются детерминированно в Python.

⸻

3. Преобразование в Obsidian-заметку

3.1. Целевой формат Markdown

На выходе хотим:

---
tags:
  - time_system
time: 60
date: 2025-11-11
maintag: w1
subtag: coding
---

Работа над бекендом для трекера времени.

Исходный текст:
> 1 час писал бэкенд на fastapi для трекера времени

Правила:
	•	tags всегда содержит time_system.
	•	В time кладём minutes.
	•	date — поле из TimeEntry.
	•	maintag и subtag — как определит SGR.
	•	В теле файла можно:
	•	первой строкой вывести title,
	•	потом — комментарий/детали (если есть),
	•	обязательно сохранить raw_text (для отладки и будущего анализа).

3.2. Функция рендеринга

note_renderer.py:

def render_markdown(note: TimeNote) -> str:
    e = note.entry
    frontmatter_lines = [
        "---",
        "tags:",
        "  - time_system",
        f"time: {e.minutes}",
        f"date: {e.date.isoformat()}",
        f"maintag: {e.maintag}",
    ]
    if e.subtag:
        frontmatter_lines.append(f"subtag: {e.subtag}")
    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    body_lines = [""]
    body_lines.append(e.title)
    body_lines.append("")
    if e.comment:
        body_lines.append(e.comment)
        body_lines.append("")
    body_lines.append("Исходный текст:")
    body_lines.append(f"> {e.raw_text}")

    return frontmatter + "\n" + "\n".join(body_lines) + "\n"


⸻

4. Генерация имени файла и предотвращение дублей

4.1. Формат имени

Предлагаю:

<slug(title)> <YYYY-MM-DD> <HH-MM>.md

	•	slug(title) — латинизированное/очищенное название:
	•	нижний регистр,
	•	пробелы → -,
	•	убрать спецсимволы.
	•	<HH-MM>:
	•	если start_time есть — используем его;
	•	если нет — используем «время создания записи» (текущее локальное время).

Пример:
	•	title: «Работа над бекендом»
	•	date: 2025-11-11
	•	time: 14:37

→ rabota-nad-bekendom 2025-11-11 14-37.md

4.2. Проверка дублей

При записи:
	1.	Проверить, существует ли файл с таким именем.
	2.	Если да — добавить уникальный суффикс: ... 14-37 (2).md или UUID-хвост.
	3.	Поскольку у нас в имени уже время с точностью до минут, вероятность дублей небольшая, но защита лишней не будет.

⸻

5. Логика SGR: как строить запрос

5.1. Подготовка входных данных

Перед SGR:
	1.	Определяем «сегодняшнюю дату»:
	•	берём datetime.now(tz=...),
	•	храним в конфиге TIMEZONE (например, Europe/Riga у тебя).
	2.	Формируем объект с уже заданными полями, которые модель не должна угадывать:

from datetime import date

def build_sgr_input(message_text: str, today: date) -> dict:
    return {
        "raw_text": message_text,
        "date": today.isoformat(),
        # остальное пусть заполняет LLM
    }

	3.	В промпте чётко прописываем: если дата не указана → использовать эту date.

5.2. System-промпт

Идея:
	•	Описать задачу: «Ты парсер временных записей. На вход — текст про то, чем человек занимался и сколько времени потратил».
	•	Жёстко описать поля TimeEntry, значения maintag, примеры маппинга:
	•	coding → обычно w1,
	•	social → w2, иногда rest (но лучше w2 по умолчанию),
	•	reading (техническое) → w1, художественное → w2,
	•	sports, hygiene → rt,
	•	если не уверен — подбирать наиболее подходящее.
	•	Запрет на придумывание времени/активностей, которых нет.
	•	Формат ответа — строго JSON, соответствующий JSON Schema от Pydantic.

5.3. User-промпт

Пример:

Тебе даётся текст сообщения пользователя о том, чем он занимался и сколько времени потратил.
Нужно заполнить JSON-объект, строго соответствующий схеме TimeEntry.

Исходный текст:
<<<
{message_text}
>>>

Используй поле "date", которое уже дано во входном JSON, если в тексте не указано другое.

Верни только JSON, без пояснений.

И вызываем что-то вроде:

entry = chat_sgr_parse(
    messages=[system_msg, user_msg],
    model_cls=TimeEntry,
    schema_name="time_entry"
)


⸻

6. Telegram-бот: сценарии и хендлеры

6.1. Команды

Минимальный набор:
	•	/start — короткая справка, объяснение формата.
	•	/help — чуть более развёрнуто.
	•	Текст без команды — основное сообщение с описанием активности.

Опционально позже:
	•	/today — показать суммарное время за сегодня по maintag/subtag.
	•	/last — показать последнюю записанную заметку.

6.2. Основной хендлер сообщения

Псевдокод:

@router.message(F.text)
async def handle_time_entry(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    today = get_today_for_user(user_id)  # пока можно просто TIMEZONE из конфига
    sgr_input = build_sgr_input(text, today)

    try:
        entry = await parse_time_entry_with_sgr(sgr_input)
    except SGRParseError as e:
        await message.reply("Не смог разобрать сообщение. Уточни, пожалуйста, длительность и суть занятия.")
        return

    note = build_time_note(entry, base_dir=config.OBSIDIAN_DIR)
    markdown = render_markdown(note)
    write_note_file(note.file_path, markdown)

    await message.reply(
        f"Записал {entry.minutes} мин, maintag={entry.maintag}, subtag={entry.subtag or '-'}.\n"
        f"Файл: {note.file_name}"
    )


⸻

7. Работа с датой и временем

7.1. «Функция получения сегодняшней даты»

Вынести в отдельный слой:

from datetime import datetime
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("Europe/Riga")

def get_today() -> date:
    return datetime.now(TIMEZONE).date()

def get_now_time() -> dtime:
    return datetime.now(TIMEZONE).time().replace(second=0, microsecond=0)

Потом можно будет расширить до «персональных таймзон по user_id».

7.2. Интерпретация времени в тексте

Логика выбора:
	•	Если в тексте есть диапазон (10:00–11:30) → SGR:
	•	вытаскивает start_time,
	•	считает minutes.
	•	Если указаны только часы/минуты (1.5 часа, 40 мин) → SGR:
	•	парсит в minutes,
	•	start_time = None, а мы используем текущее время для имени файла.

⸻

8. Тестирование (особенно для LLM+SGR)

8.1. Набор тестовых сообщений

Сделать файл tests/data/time_messages_samples.jsonl, где каждая строка:

{
  "input": "1 час писал бекенд на fastapi",
  "expected": {
    "minutes": 60,
    "maintag": "w1",
    "subtag": "coding",
    "title": "Работа над бекендом на fastapi"
  }
}

Примеры, которые обязательно покрыть:
	1.	«45 мин писал код, делал фичу для бэкенда»
	2.	«1.5 часа болтали с коллегами про работу» → w2, social
	3.	«30 минут спортзал» → rt, sports
	4.	«20 мин умывался, душ» → rt, hygiene
	5.	«2 часа читал книгу по C++» → w1, reading
	6.	«1 час читал роман» → w2, reading
	7.	Со смешанными формулировками и без явного указания единиц («полтора часа», «минут 40» и т.п.).

8.2. Типы тестов
	1.	Юнит-тесты рендеринга:
	•	TimeEntry → Markdown
	•	Проверить YAML-секцию, поля, экранирование.
	2.	Юнит-тесты генерации имени файла:
	•	Разные title, наличие/отсутствие start_time.
	•	Корректность slug.
	3.	Интеграционные тесты SGR с моками:
	•	Обернуть chat_sgr_parse в интерфейс, который можно замокать.
	•	На вход текст, на выход — заранее определённый TimeEntry.
	4.	E2E-тесты пайплайна (без Telegram):
	•	Функция process_text_to_note(text):
	•	вызывает парсер (замоканный),
	•	создаёт TimeNote,
	•	рендерит Markdown.
	•	Проверить, что Markdown совпадает с ожидаемым.

⸻

9. Конфигурация и безопасность

9.1. Конфиг

config.py:
	•	TELEGRAM_BOT_TOKEN
	•	OBSIDIAN_DIR — путь к папке с заметками.
	•	TIMEZONE
	•	Параметры клиента LLM (endpoint, ключи, timeout).

Читать из .env (через python-dotenv или pydantic-settings).

9.2. Прав доступа
	•	Убедиться, что у процесса бота есть права записи в директорию Obsidian.
	•	По возможности, vault лежит у тебя локально; если бот в Docker — смонтировать папку.

⸻

10. Пошаговый план реализации

Сводим всё в линейный план:
	1.	Скелет проекта
	•	Создать репозиторий.
	•	Настроить pyproject/requirements.
	•	Добавить базовый config.py.
	2.	Модели и SGR-схемы
	•	Определить TimeEntry, TimeNote.
	•	Сгенерировать JSON Schema для TimeEntry.
	•	Написать system+user промпты для time_entry.
	3.	Клиент SGR
	•	Написать parse_time_entry_with_sgr(message_text: str, today: date) -> TimeEntry.
	•	Подключить кэширование ответов в cache/time_entries.jsonl.
	4.	Рендеринг Obsidian-заметки
	•	Реализовать build_time_note(entry, base_dir) (генерация ID, имени файла, пути, timestamps).
	•	Реализовать render_markdown(note).
	•	Реализовать write_note_file(path, content).
	5.	Локальный CLI для отладки
	•	Команда python -m time_bot.cli "1 час писал бекенд".
	•	Печатает Markdown в stdout и/или пишет файл.
	6.	Тесты
	•	Написать юнит-тесты рендеринга и имени файла.
	•	Добавить фикстуры сообщений и ожидаемых полей (без реальной LLM — через моки).
	7.	Интеграция с Telegram
	•	Настроить aiogram.
	•	Хендлеры /start, /help, основной текст.
	•	Подключить пайплайн: сообщение → SGR → заметка → запись файла → ответ пользователю.
	8.	Доп. фичи (по желанию)
	•	Команды /today и /stats.
	•	Отправка предпросмотра заметки перед записью (с подтверждением).
	•	Обработка правок (например, командой /edit_last).
	9.	Деплой
	•	Локально, как systemd-служба или Docker-контейнер.
	•	Логи в файл + минимальный мониторинг.

⸻

Если хочешь, дальше можем:
	•	сначала детализировать именно TimeEntry (вплоть до текстов Field(description=...) под SGR),
	•	либо сразу написать пример system-промпта для твоего chat_sgr_parse и пару примеров input→output.