"""Parse and validate simplify LLM structured JSON output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.vocabulary.explanation_text import normalize_usage_explanation
from lexiflow_core.vocabulary.lemma_form import normalize_lemma, parse_word_category
from lexiflow_core.vocabulary.models import WordCategory


class SimplifyOutputError(Exception):
    """Raised when simplify LLM output is invalid."""


@dataclass(frozen=True)
class SimplifyNewWord:
    lemma: str
    gloss: str
    explanation: str
    level: CEFRLevel
    category: WordCategory


@dataclass(frozen=True)
class SimplifyLLMOutput:
    title: str
    body: str
    new_words: tuple[SimplifyNewWord, ...]


def simplify_json_schema() -> dict[str, object]:
    """Return JSON schema passed to LLM providers for simplify jobs."""
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "body": {"type": "string"},
            "new_words": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "lemma": {"type": "string"},
                        "gloss": {"type": "string"},
                        "explanation": {"type": "string"},
                        "level": {"type": "string"},
                        "category": {"type": "string"},
                    },
                    "required": ["lemma", "gloss", "explanation", "level", "category"],
                },
            },
        },
        "required": ["title", "body", "new_words"],
    }


def parse_simplify_output(raw: str, *, language_code: str) -> SimplifyLLMOutput:
    """Parse and validate simplify LLM JSON before persistence."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SimplifyOutputError("invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SimplifyOutputError("output must be a JSON object")
    return _parse_payload(payload, language_code=language_code)


def _parse_payload(payload: dict[str, Any], *, language_code: str) -> SimplifyLLMOutput:
    title = payload.get("title")
    body = payload.get("body")
    new_words_raw = payload.get("new_words")
    if not isinstance(title, str) or not title.strip():
        raise SimplifyOutputError("title must be a non-empty string")
    if not isinstance(body, str) or not body.strip():
        raise SimplifyOutputError("body must be a non-empty string")
    if not isinstance(new_words_raw, list):
        raise SimplifyOutputError("new_words must be an array")
    new_words = tuple(
        _parse_new_word(item, language_code=language_code) for item in new_words_raw
    )
    return SimplifyLLMOutput(
        title=title.strip(),
        body=body.strip(),
        new_words=new_words,
    )


def _parse_new_word(raw: object, *, language_code: str) -> SimplifyNewWord:
    if not isinstance(raw, dict):
        raise SimplifyOutputError("each new word must be an object")
    lemma = raw.get("lemma")
    gloss = raw.get("gloss")
    explanation = raw.get("explanation")
    level_value = raw.get("level")
    category = parse_word_category(raw.get("category"))
    if not isinstance(lemma, str) or not lemma.strip():
        raise SimplifyOutputError("new word lemma must be a non-empty string")
    if not isinstance(gloss, str) or not gloss.strip():
        raise SimplifyOutputError("new word gloss must be a non-empty string")
    if not isinstance(explanation, str):
        raise SimplifyOutputError("new word explanation must be a string")
    if not isinstance(level_value, str):
        raise SimplifyOutputError("new word level must be a string")
    try:
        level = CEFRLevel(level_value.strip().upper())
    except ValueError as exc:
        raise SimplifyOutputError(f"invalid CEFR level: {level_value!r}") from exc
    normalized = normalize_lemma(
        lemma,
        language_code=language_code,
        category=category,
    )
    if not normalized:
        raise SimplifyOutputError("new word lemma must be a non-empty string")
    return SimplifyNewWord(
        lemma=normalized,
        gloss=gloss.strip(),
        explanation=normalize_usage_explanation(explanation),
        level=level,
        category=category,
    )
