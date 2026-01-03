from time_bot.sgr_client import _extract_json_text


def test_extract_json_text_handles_prefix_suffix():
    data = ".\n{\n  \"a\": 1\n}\nextra"
    assert _extract_json_text(data) == '{\n  "a": 1\n}'


def test_extract_json_text_handles_nested_start():
    data = ".{\n{\"date\": \"2024-01-01\"}"
    assert _extract_json_text(data) == '{"date": "2024-01-01"}'


def test_extract_json_text_returns_original_when_no_braces():
    data = "oops"
    assert _extract_json_text(data) == "oops"
