"""Tests for vocabulary difficulty promotion."""

from __future__ import annotations

from lexiflow_core.vocabulary.fluency import next_difficulty
from lexiflow_core.vocabulary.models import DifficultyRating


def test_next_difficulty_steps_hard_to_well() -> None:
    assert next_difficulty(DifficultyRating.HARD) == DifficultyRating.WELL


def test_next_difficulty_steps_fluent_to_easy() -> None:
    assert next_difficulty(DifficultyRating.FLUENT) == DifficultyRating.EASY


def test_next_difficulty_returns_none_for_easy() -> None:
    assert next_difficulty(DifficultyRating.EASY) is None
