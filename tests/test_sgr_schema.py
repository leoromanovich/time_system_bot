from pathlib import Path
import json

from time_bot.models import TimeEntry

SCHEMA_PATH = Path("schemas/time_entry.json")


def test_schema_file_matches_model_schema() -> None:
    assert SCHEMA_PATH.exists(), "Schema file missing"
    file_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    model_schema = TimeEntry.model_json_schema()
    assert file_schema == model_schema


def test_maintag_enum_values() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    maintag_schema = schema["properties"]["maintag"]
    assert sorted(maintag_schema["enum"]) == ["rest", "rt", "w1", "w2"]


def test_subtag_enum_values() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    subtag_schema = schema["properties"]["subtag"]
    enum_values = None
    if "enum" in subtag_schema:
        enum_values = subtag_schema["enum"]
    else:
        for option in subtag_schema.get("anyOf", []):
            if "enum" in option:
                enum_values = option["enum"]
                break
    assert enum_values is not None, "Subtag enum not found in schema"
    assert sorted(enum_values) == [
        "coding",
        "gym",
        "health",
        "learning",
        "other",
        "reading",
        "social",
        "systematization",
        "technical",
        "waiting",
        "walking",
        "wasting",
        "watching",
        "writing",
    ]
