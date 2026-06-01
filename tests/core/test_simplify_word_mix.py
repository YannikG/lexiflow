"""Tests for simplify word mix selection."""

from __future__ import annotations

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.simplify.word_mix import (
    EASY_WEIGHT,
    VocabWordForMix,
    rank_words,
    score_word,
    select_prompt_words,
)
from lexiflow_core.vocabulary.models import DifficultyRating


def test_bucket_selection_prefers_hard_over_easy_at_same_similarity() -> None:
    hard = VocabWordForMix(
        lemma="duro",
        level=CEFRLevel.A2,
        difficulty=DifficultyRating.HARD,
        distance=0.1,
    )
    easy = VocabWordForMix(
        lemma="facil",
        level=CEFRLevel.A2,
        difficulty=DifficultyRating.EASY,
        distance=0.1,
    )

    ranked = rank_words([easy, hard])

    assert ranked[0].lemma == "duro"
    assert score_word(hard) > score_word(easy)
    assert score_word(easy) == EASY_WEIGHT / (1.0 + 0.1)


def test_easy_word_still_picked_if_only_fit() -> None:
    only_easy = VocabWordForMix(
        lemma="unico",
        level=CEFRLevel.A2,
        difficulty=DifficultyRating.EASY,
        distance=0.05,
    )

    selected = select_prompt_words([only_easy], CEFRLevel.A2, total_target=5)

    assert selected == ["unico"]
