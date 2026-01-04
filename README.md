# time_system_bot

## Project structure

```
src/
  time_bot/
    bot/               # aiogram routers and startup code
    cli.py             # manual pipeline runner
    config.py          # pydantic-settings configuration
    models.py          # TimeEntry/TimeNote schemas
    note_builder.py    # helpers for filenames/metadata
    note_renderer.py   # Markdown rendering
    obsidian_writer.py # filesystem writer
    sgr_client.py      # wrapper for chat_sgr_parse
    time_utils.py      # timezone helpers
tests/
  data/
cache/
scripts/
```

Use `.env.example` as a template for configuring local secrets (Telegram token, OpenAI key, Obsidian vault path, timezone, cache dir).

## Food tracker

The Telegram bot now includes the food tracking flow from `tmp_sources/food_calendar`. Use the “Добавить еду” button next to “Статистика за сегодня” to open the inline menu. Environment variables prefixed with `FOOD_TRACK_` control the model that recognizes compositions and where Markdown files (FoodLog, ConditionLog, etc.) are stored.
