"""Shared word category labels for vocabulary UI."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import WordCategory

WORD_CATEGORY_LABELS: dict[WordCategory, str] = {
    WordCategory.NOUN: "Noun",
    WordCategory.VERB: "Verb",
    WordCategory.ADJECTIVE: "Adjective",
    WordCategory.ADVERB: "Adverb",
    WordCategory.PRONOUN: "Pronoun",
    WordCategory.PREPOSITION: "Preposition",
    WordCategory.CONJUNCTION: "Conjunction",
    WordCategory.INTERJECTION: "Interjection",
    WordCategory.OTHER: "Other",
}


def word_category_label(category: WordCategory) -> str:
    return WORD_CATEGORY_LABELS.get(category, category.value.title())
