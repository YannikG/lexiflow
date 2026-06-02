"""Tests for new word suggestion filtering."""

from __future__ import annotations

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.simplify.new_words import (
    filter_suggestions,
    learned_lemmas_from_stored,
    learned_vocabulary_for_variant,
    lemma_appears_in_markdown,
    visible_stored_suggestions,
)
from lexiflow_core.simplify.structured_output import SimplifyNewWord
from lexiflow_core.vocabulary.models import (
    DifficultyRating,
    NewWordSuggestion,
    VocabularyEntry,
    WordCategory,
)


def _simplify_new_word(
    *,
    lemma: str,
    gloss: str,
    level: CEFRLevel,
    explanation: str = "",
    category: WordCategory = WordCategory.OTHER,
) -> SimplifyNewWord:
    return SimplifyNewWord(
        lemma=lemma,
        gloss=gloss,
        explanation=explanation,
        level=level,
        category=category,
    )


def test_new_words_filtered_if_lemma_exists_in_vocabulary() -> None:
    raw = (
        _simplify_new_word(lemma="correr", gloss="to run", level=CEFRLevel.A2),
        _simplify_new_word(lemma="nadar", gloss="to swim", level=CEFRLevel.A2),
    )

    filtered = filter_suggestions(raw, existing_lemmas={"correr"}, language_code="es")

    assert len(filtered) == 1
    assert filtered[0].lemma == "nadar"


def test_new_words_filter_removes_duplicates_and_junk() -> None:
    raw = (
        _simplify_new_word(lemma="nadar", gloss="to swim", level=CEFRLevel.A2),
        _simplify_new_word(lemma="nadar", gloss="duplicate", level=CEFRLevel.A2),
        _simplify_new_word(lemma="  ", gloss="blank lemma", level=CEFRLevel.A2),
        _simplify_new_word(lemma="correr", gloss="", level=CEFRLevel.A2),
        _simplify_new_word(lemma="Correr", gloss="to run", level=CEFRLevel.B1),
    )

    filtered = filter_suggestions(raw, existing_lemmas=set(), language_code="es")

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


def test_lemma_appears_in_markdown_matches_whole_words_case_insensitive() -> None:
    markdown = "# Simple\n\nTexto simple."

    assert lemma_appears_in_markdown("simple", markdown)
    assert lemma_appears_in_markdown("Simple", markdown)
    assert not lemma_appears_in_markdown("simp", markdown)


def test_learned_vocabulary_for_variant_includes_manual_adds_in_markdown() -> None:
    stored = (
        NewWordSuggestion(lemma="nadar", gloss="to swim", suggested_level=CEFRLevel.A2),
    )
    entries = (
        VocabularyEntry(
            lemma="nadar",
            translation="to swim",
            explanation="",
            level_when_learned=CEFRLevel.A2,
            difficulty_rating=DifficultyRating.HARD,
            word_category=WordCategory.VERB,
        ),
        VocabularyEntry(
            lemma="simple",
            translation="simple",
            explanation="",
            level_when_learned=CEFRLevel.A2,
            difficulty_rating=DifficultyRating.HARD,
            word_category=WordCategory.ADJECTIVE,
        ),
    )

    learned = learned_vocabulary_for_variant(
        stored,
        entries,
        variant_markdown="# Simple\n\nTexto simple.",
    )

    assert [entry.lemma for entry in learned] == ["nadar", "simple"]
