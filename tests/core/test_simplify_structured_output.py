"""Tests for simplify LLM structured output parsing."""

from __future__ import annotations

import pytest
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.simplify.structured_output import (
    SimplifyOutputError,
    parse_simplify_output,
)


def test_parse_simplify_output_accepts_valid_json() -> None:
    raw = """
    {
      "title": "Titulo simple",
      "body": "Texto corto.",
      "new_words": [
        {"lemma": "correr", "gloss": "to run", "level": "A2"}
      ]
    }
    """
    parsed = parse_simplify_output(raw)
    assert parsed.title == "Titulo simple"
    assert parsed.body == "Texto corto."
    assert len(parsed.new_words) == 1
    assert parsed.new_words[0].lemma == "correr"
    assert parsed.new_words[0].gloss == "to run"
    assert parsed.new_words[0].level == CEFRLevel.A2


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        '{"title": "", "body": "x", "new_words": []}',
        '{"title": "T", "body": "x", "new_words": "bad"}',
    ],
)
def test_parse_simplify_output_rejects_invalid_json(raw: str) -> None:
    with pytest.raises(SimplifyOutputError):
        parse_simplify_output(raw)
