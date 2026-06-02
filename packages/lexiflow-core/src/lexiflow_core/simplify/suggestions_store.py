"""Persist new word suggestions beside simplified variants."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.lemma_form import normalize_lemma, parse_word_category
from lexiflow_core.vocabulary.models import NewWordSuggestion, WordCategory


class SuggestionsStoreError(Exception):
    """Raised when suggestion sidecar files cannot be read or written."""


@dataclass(frozen=True)
class StoredSuggestion:
    lemma: str
    gloss: str
    level: str
    explanation: str = ""
    category: str = WordCategory.OTHER.value


def suggestions_path(text_folder: Path, variant_name: str) -> Path:
    """Return sidecar path for a simplified variant's suggestions."""
    return text_folder / f"{variant_name}.suggestions.json"


def load_suggestions(
    text_folder: Path,
    variant_name: str,
    *,
    language_code: str,
) -> tuple[NewWordSuggestion, ...]:
    """Load stored suggestions for a simplified variant."""
    path = suggestions_path(text_folder, variant_name)
    if not path.is_file():
        return ()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SuggestionsStoreError(f"failed to read suggestions: {path}") from exc
    if not isinstance(raw, list):
        raise SuggestionsStoreError(f"invalid suggestions format: {path}")
    return tuple(_parse_item(item, language_code=language_code) for item in raw)


def save_suggestions(
    text_folder: Path,
    variant_name: str,
    suggestions: tuple[NewWordSuggestion, ...],
) -> None:
    """Write suggestions sidecar for a simplified variant."""
    path = suggestions_path(text_folder, variant_name)
    payload = [
        StoredSuggestion(
            lemma=item.lemma,
            gloss=item.gloss,
            level=item.suggested_level.value,
            explanation=item.explanation,
            category=item.word_category.value,
        )
        for item in suggestions
    ]
    try:
        path.write_text(
            json.dumps([asdict(item) for item in payload], indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise SuggestionsStoreError(f"failed to write suggestions: {path}") from exc


def _parse_item(raw: object, *, language_code: str) -> NewWordSuggestion:
    if not isinstance(raw, dict):
        raise SuggestionsStoreError("each suggestion must be an object")
    lemma = raw.get("lemma")
    gloss = raw.get("gloss")
    level_value = raw.get("level")
    explanation = raw.get("explanation", "")
    category = parse_word_category(raw.get("category"))
    if not isinstance(lemma, str) or not isinstance(gloss, str):
        raise SuggestionsStoreError("suggestion fields must be strings")
    if not isinstance(level_value, str):
        raise SuggestionsStoreError("suggestion level must be a string")
    if not isinstance(explanation, str):
        explanation = ""
    try:
        level = CEFRLevel(level_value.upper())
    except ValueError as exc:
        raise SuggestionsStoreError(f"invalid CEFR level: {level_value!r}") from exc
    normalized = normalize_lemma(
        lemma,
        language_code=language_code,
        category=category,
    )
    if not normalized:
        raise SuggestionsStoreError("suggestion lemma must be non-empty")
    return NewWordSuggestion(
        lemma=normalized,
        gloss=gloss.strip(),
        suggested_level=level,
        explanation=explanation.strip(),
        word_category=category,
    )
