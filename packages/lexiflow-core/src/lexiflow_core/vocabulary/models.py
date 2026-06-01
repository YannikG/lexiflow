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


@dataclass(frozen=True)
class VocabularyEntry:
    lemma: str
    translation: str
    explanation: str
    level_when_learned: CEFRLevel
    difficulty_rating: DifficultyRating
    surface_form: str | None = None
    entry_id: UUID | None = None


@dataclass(frozen=True)
class NewWordSuggestion:
    lemma: str
    gloss: str
    suggested_level: CEFRLevel
