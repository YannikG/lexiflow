"""Post-filter new word suggestions after simplify."""

from __future__ import annotations

from lexiflow_core.simplify.structured_output import SimplifyNewWord
from lexiflow_core.vocabulary.models import NewWordSuggestion


def filter_suggestions(
    raw: tuple[SimplifyNewWord, ...],
    *,
    existing_lemmas: set[str],
) -> tuple[NewWordSuggestion, ...]:
    """Remove existing vocabulary, duplicates, and invalid entries."""
    filtered: list[NewWordSuggestion] = []
    seen: set[str] = set()
    for item in raw:
        lemma = item.lemma.strip().lower()
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
