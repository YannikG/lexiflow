"""Canonical lemma spelling for vocabulary entries."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import WordCategory


def parse_word_category(value: object) -> WordCategory:
    """Parse a word category string from LLM or storage."""
    if isinstance(value, WordCategory):
        return value
    if not isinstance(value, str) or not value.strip():
        return WordCategory.OTHER
    normalized = value.strip().lower().replace(" ", "_")
    try:
        return WordCategory(normalized)
    except ValueError:
        return WordCategory.OTHER


def normalize_lemma(
    lemma: str,
    *,
    language_code: str,
    category: WordCategory,
) -> str:
    """Return the canonical dictionary form for storage."""
    cleaned = lemma.strip()
    if not cleaned:
        return ""
    if language_code == "de" and category == WordCategory.NOUN:
        return _capitalize_first(cleaned)
    return cleaned.lower()


def _capitalize_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]
