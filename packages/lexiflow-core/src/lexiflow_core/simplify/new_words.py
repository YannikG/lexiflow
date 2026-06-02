"""Post-filter new word suggestions after simplify."""

from __future__ import annotations

import re

from lexiflow_core.simplify.structured_output import SimplifyNewWord
from lexiflow_core.vocabulary.lemma_form import normalize_lemma
from lexiflow_core.vocabulary.models import NewWordSuggestion, VocabularyEntry


def filter_suggestions(
    raw: tuple[SimplifyNewWord, ...],
    *,
    existing_lemmas: set[str],
    language_code: str,
) -> tuple[NewWordSuggestion, ...]:
    """Remove existing vocabulary, duplicates, and invalid entries."""
    filtered: list[NewWordSuggestion] = []
    seen: set[str] = set()
    for item in raw:
        lemma = normalize_lemma(
            item.lemma,
            language_code=language_code,
            category=item.category,
        )
        gloss = item.gloss.strip()
        if not lemma or not gloss:
            continue
        if lemma in existing_lemmas or lemma in seen:
            continue
        seen.add(lemma)
        filtered.append(
            NewWordSuggestion(
                lemma=lemma,
                gloss=gloss,
                suggested_level=item.level,
                explanation=item.explanation.strip(),
                word_category=item.category,
            )
        )
    return tuple(filtered)


def visible_stored_suggestions(
    stored: tuple[NewWordSuggestion, ...],
    *,
    existing_lemmas: set[str],
) -> tuple[NewWordSuggestion, ...]:
    """Return sidecar suggestions that are not already in vocabulary."""
    return tuple(item for item in stored if item.lemma not in existing_lemmas)


def learned_lemmas_from_stored(
    stored: tuple[NewWordSuggestion, ...],
    *,
    lemmas_in_vocabulary: set[str],
) -> tuple[str, ...]:
    """Return lemmas from stored suggestions that are already in vocabulary."""
    return tuple(item.lemma for item in stored if item.lemma in lemmas_in_vocabulary)


def lemma_appears_in_markdown(lemma: str, markdown: str) -> bool:
    """Return whether *lemma* occurs as a whole word in *markdown*."""
    if not lemma.strip():
        return False
    pattern = re.compile(
        rf"(?<![\w]){re.escape(lemma)}(?![\w])",
        re.IGNORECASE,
    )
    return pattern.search(markdown) is not None


def learned_vocabulary_for_variant(
    stored: tuple[NewWordSuggestion, ...],
    vocabulary_entries: tuple[VocabularyEntry, ...],
    *,
    variant_markdown: str,
) -> tuple[VocabularyEntry, ...]:
    """Return vocabulary entries learned for a simplified variant.

    Includes entries from stored suggestions already in vocabulary, plus any
    other vocabulary lemmas that appear in the variant markdown (e.g. manual adds).
    """
    by_lemma = {entry.lemma: entry for entry in vocabulary_entries}
    existing = set(by_lemma)
    ordered_lemmas: list[str] = list(
        learned_lemmas_from_stored(stored, lemmas_in_vocabulary=existing)
    )
    seen = set(ordered_lemmas)
    for lemma in sorted(existing - seen):
        if lemma_appears_in_markdown(lemma, variant_markdown):
            ordered_lemmas.append(lemma)
    return tuple(by_lemma[lemma] for lemma in ordered_lemmas if lemma in by_lemma)
