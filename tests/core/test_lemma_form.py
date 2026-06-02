"""Tests for canonical lemma spelling."""

from __future__ import annotations

from lexiflow_core.vocabulary.lemma_form import normalize_lemma, parse_word_category
from lexiflow_core.vocabulary.models import WordCategory


def test_normalize_lemma_capitalizes_german_nouns() -> None:
    assert (
        normalize_lemma("haus", language_code="de", category=WordCategory.NOUN)
        == "Haus"
    )


def test_normalize_lemma_lowercases_german_verbs() -> None:
    assert (
        normalize_lemma("Laufen", language_code="de", category=WordCategory.VERB)
        == "laufen"
    )


def test_normalize_lemma_lowercases_non_german_nouns() -> None:
    assert (
        normalize_lemma("Casa", language_code="es", category=WordCategory.NOUN)
        == "casa"
    )


def test_parse_word_category_accepts_known_values() -> None:
    assert parse_word_category("noun") == WordCategory.NOUN
    assert parse_word_category("unknown") == WordCategory.OTHER
