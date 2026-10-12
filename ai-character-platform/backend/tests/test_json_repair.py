import pytest
from app.services.gemini_service import _extract_json, _repair_json, _try_parse


def test_extract_json_clean():
    raw = '{"name": "Elena", "age": 28}'
    extracted = _extract_json(raw)
    assert extracted == raw


def test_extract_json_with_markdown_fences():
    raw = '```json\n{"name": "Elena", "age": 28}\n```'
    extracted = _extract_json(raw)
    assert '{"name": "Elena", "age": 28}' in extracted


def test_extract_json_nested_bracket_depth():
    raw = 'Here is the response: {"name": "Elena", "details": {"hobby": "reading"}} extra text'
    extracted = _extract_json(raw)
    assert extracted == '{"name": "Elena", "details": {"hobby": "reading"}}'


def test_repair_smart_quotes():
    raw = '{\u201cname\u201d: \u2018Elena\u2019}'
    repaired = _repair_json(raw)
    assert repaired == '{"name": \'Elena\'}'


def test_repair_trailing_commas():
    raw = '{"name": "Elena", "hobbies": ["reading", "coding",],}'
    repaired = _repair_json(raw)
    assert repaired == '{"name": "Elena", "hobbies": ["reading", "coding"]}'


def test_repair_control_characters():
    raw = '{"name": "Elena\x00\x05\x1f"}'
    repaired = _repair_json(raw)
    assert repaired == '{"name": "Elena"}'


def test_try_parse_recovers_malformed():
    raw = '```json\n{"name": \u201cElena\u201d, "age": 28,}\n```'
    parsed = _try_parse(raw)
    assert parsed["name"] == "Elena"
    assert parsed["age"] == 28
