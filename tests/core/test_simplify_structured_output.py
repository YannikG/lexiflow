"""Tests for simplify LLM structured output parsing."""

from __future__ import annotations

import pytest
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.simplify.structured_output import (
    SimplifyOutputError,
    parse_simplify_output,
)
from lexiflow_core.vocabulary.models import WordCategory


def test_parse_simplify_output_accepts_valid_json() -> None:
    raw = """
    {
      "title": "Titulo simple",
      "body": "Texto corto.",
      "new_words": [
        {
          "lemma": "correr",
          "gloss": "to run",
          "explanation": "Movement at speed on foot.",
          "level": "A2",
          "category": "verb"
        }
      ]
    }
    """
    parsed = parse_simplify_output(raw, language_code="es")
    assert parsed.title == "Titulo simple"
    assert parsed.body == "Texto corto."
    assert len(parsed.new_words) == 1
    assert parsed.new_words[0].lemma == "correr"
    assert parsed.new_words[0].gloss == "to run"
    assert parsed.new_words[0].explanation == "Movement at speed on foot."
    assert parsed.new_words[0].level == CEFRLevel.A2
    assert parsed.new_words[0].category == WordCategory.VERB


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
        parse_simplify_output(raw, language_code="es")
