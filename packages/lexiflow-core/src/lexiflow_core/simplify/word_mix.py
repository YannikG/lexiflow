"""Level bucket word selection for simplify prompts."""

from __future__ import annotations

from dataclasses import dataclass

from lexiflow_core.languages.models import CEFRLevel, level_above, level_below
from lexiflow_core.vocabulary.models import DifficultyRating

EASY_WEIGHT = 0.25
LEVEL_QUOTA = 0.30
BELOW_QUOTA = 0.20
ABOVE_QUOTA = 0.10


@dataclass(frozen=True)
class VocabWordForMix:
    lemma: str
    level: CEFRLevel
    difficulty: DifficultyRating
    distance: float


def score_word(word: VocabWordForMix) -> float:
    """Rank vocabulary words by semantic similarity with difficulty weighting."""
    weight = EASY_WEIGHT if word.difficulty == DifficultyRating.EASY else 1.0
    similarity = 1.0 / (1.0 + word.distance)
    return similarity * weight


def rank_words(words: list[VocabWordForMix]) -> list[VocabWordForMix]:
    """Return words sorted by descending mix score."""
    return sorted(words, key=score_word, reverse=True)


def select_prompt_words(
    ranked: list[VocabWordForMix],
    target_level: CEFRLevel,
    *,
    total_target: int = 20,
) -> list[str]:
    """Fill level buckets from a ranked vocabulary list."""
    if total_target <= 0 or not ranked:
        return []
    below_level = level_below(target_level)
    above_level = level_above(target_level)
    at_level_count = max(1, int(total_target * LEVEL_QUOTA))
    below_count = max(0, int(total_target * BELOW_QUOTA))
    above_count = max(0, int(total_target * ABOVE_QUOTA))
    selected: list[str] = []
    seen: set[str] = set()

    def take_bucket(level: CEFRLevel | None, limit: int) -> None:
        if limit <= 0 or level is None:
            return
        added = 0
        for word in ranked:
            if word.lemma in seen:
                continue
            if word.level != level:
                continue
            selected.append(word.lemma)
            seen.add(word.lemma)
            added += 1
            if added >= limit:
                return

    take_bucket(target_level, at_level_count)
    take_bucket(below_level, below_count)
    take_bucket(above_level, above_count)
    for word in ranked:
        if len(selected) >= total_target:
            break
        if word.lemma in seen:
            continue
        selected.append(word.lemma)
        seen.add(word.lemma)
    return selected
