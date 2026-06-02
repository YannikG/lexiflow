"""Tests for usage explanation normalization."""

from __future__ import annotations

from lexiflow_core.vocabulary.explanation_text import normalize_usage_explanation
from lexiflow_core.vocabulary.lemma_output import parse_lemma_output


def test_normalize_usage_explanation_strips_this_word_refers_to() -> None:
    assert (
        normalize_usage_explanation("This word refers to movement at speed.")
        == "Movement at speed."
    )


def test_normalize_usage_explanation_leaves_direct_style_unchanged() -> None:
    text = "Used when describing fast movement on foot."
    assert normalize_usage_explanation(text) == text


def test_parse_lemma_output_normalizes_explanation() -> None:
    parsed = parse_lemma_output(
        """
        {
          "lemma": "correr",
          "translation": "to run",
          "explanation": "This word refers to moving quickly on foot.",
          "category": "verb"
        }
        """,
        language_code="es",
    )
    assert parsed.explanation == "Moving quickly on foot."
