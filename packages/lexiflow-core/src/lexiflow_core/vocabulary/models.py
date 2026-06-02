"""Vocabulary domain types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from lexiflow_core.languages.models import CEFRLevel


class DifficultyRating(StrEnum):
    HARD = "hard"
    WELL = "well"
    FLUENT = "fluent"
    EASY = "easy"


class VocabularySort(StrEnum):
    RECENT = "recent"
    ALPHABETICAL = "alphabetical"
    LEVEL = "level"
    DIFFICULTY = "difficulty"


class WordCategory(StrEnum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    OTHER = "other"


@dataclass(frozen=True)
class VocabularyEntry:
    lemma: str
    translation: str
    explanation: str
    level_when_learned: CEFRLevel
    difficulty_rating: DifficultyRating
    word_category: WordCategory = WordCategory.OTHER
    surface_form: str | None = None
    entry_id: UUID | None = None


@dataclass(frozen=True)
class NewWordSuggestion:
    lemma: str
    gloss: str
    suggested_level: CEFRLevel
    explanation: str = ""
    word_category: WordCategory = WordCategory.OTHER
