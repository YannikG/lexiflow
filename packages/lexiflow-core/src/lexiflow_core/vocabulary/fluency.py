"""Difficulty promotion helpers for vocabulary study."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import DifficultyRating

_PROMOTION: dict[DifficultyRating, DifficultyRating] = {
    DifficultyRating.HARD: DifficultyRating.WELL,
    DifficultyRating.WELL: DifficultyRating.FLUENT,
    DifficultyRating.FLUENT: DifficultyRating.EASY,
}


def next_difficulty(current: DifficultyRating) -> DifficultyRating | None:
    """Return the next difficulty after promote fluency, or None when mastered."""
    return _PROMOTION.get(current)
