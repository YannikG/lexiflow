"""Tests for new word suggestion filtering."""

from __future__ import annotations

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.simplify.new_words import (
    filter_suggestions,
    learned_lemmas_from_stored,
    visible_stored_suggestions,
)
from lexiflow_core.simplify.structured_output import SimplifyNewWord
from lexiflow_core.vocabulary.models import NewWordSuggestion


def test_new_words_filtered_if_lemma_exists_in_vocabulary() -> None:
    raw = (
        SimplifyNewWord(lemma="correr", gloss="to run", level=CEFRLevel.A2),
        SimplifyNewWord(lemma="nadar", gloss="to swim", level=CEFRLevel.A2),
    )

    filtered = filter_suggestions(raw, existing_lemmas={"correr"})

    assert len(filtered) == 1
    assert filtered[0].lemma == "nadar"


def test_new_words_filter_removes_duplicates_and_junk() -> None:
    raw = (
        SimplifyNewWord(lemma="nadar", gloss="to swim", level=CEFRLevel.A2),
        SimplifyNewWord(lemma="nadar", gloss="duplicate", level=CEFRLevel.A2),
        SimplifyNewWord(lemma="  ", gloss="blank lemma", level=CEFRLevel.A2),
        SimplifyNewWord(lemma="correr", gloss="", level=CEFRLevel.A2),
        SimplifyNewWord(lemma="Correr", gloss="to run", level=CEFRLevel.B1),
    )

    filtered = filter_suggestions(raw, existing_lemmas=set())

    assert [item.lemma for item in filtered] == ["nadar", "correr"]


def test_visible_stored_suggestions_skips_existing_lemmas() -> None:
    stored = (
        NewWordSuggestion(lemma="correr", gloss="to run", suggested_level=CEFRLevel.A2),
        NewWordSuggestion(lemma="nadar", gloss="to swim", suggested_level=CEFRLevel.A2),
    )

    visible = visible_stored_suggestions(stored, existing_lemmas={"correr"})

    assert len(visible) == 1
    assert visible[0].lemma == "nadar"


def test_learned_lemmas_from_stored_returns_vocabulary_matches() -> None:
    stored = (
        NewWordSuggestion(lemma="correr", gloss="to run", suggested_level=CEFRLevel.A2),
        NewWordSuggestion(lemma="nadar", gloss="to swim", suggested_level=CEFRLevel.A2),
    )

    learned = learned_lemmas_from_stored(stored, lemmas_in_vocabulary={"correr"})

    assert learned == ("correr",)
