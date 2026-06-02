"""Parse lemma inference LLM JSON output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from lexiflow_core.vocabulary.explanation_text import normalize_usage_explanation
from lexiflow_core.vocabulary.lemma_form import normalize_lemma, parse_word_category
from lexiflow_core.vocabulary.models import WordCategory


class LemmaOutputError(Exception):
    """Raised when lemma LLM output is invalid."""


@dataclass(frozen=True)
class LemmaInferenceResult:
    lemma: str
    translation: str
    explanation: str
    word_category: WordCategory


def lemma_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "lemma": {"type": "string"},
            "translation": {"type": "string"},
            "explanation": {"type": "string"},
            "category": {"type": "string"},
        },
        "required": ["lemma", "translation", "explanation", "category"],
    }


def parse_lemma_output(raw: str, *, language_code: str) -> LemmaInferenceResult:
    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LemmaOutputError("lemma output is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise LemmaOutputError("lemma output must be an object")
    lemma = parsed.get("lemma")
    translation = parsed.get("translation")
    explanation = parsed.get("explanation")
    category = parse_word_category(parsed.get("category"))
    if not isinstance(lemma, str) or not lemma.strip():
        raise LemmaOutputError("lemma must be a non-empty string")
    if not isinstance(translation, str) or not translation.strip():
        raise LemmaOutputError("translation must be a non-empty string")
    if not isinstance(explanation, str):
        raise LemmaOutputError("explanation must be a string")
    normalized = normalize_lemma(
        lemma,
        language_code=language_code,
        category=category,
    )
    if not normalized:
        raise LemmaOutputError("lemma must be a non-empty string")
    return LemmaInferenceResult(
        lemma=normalized,
        translation=translation.strip(),
        explanation=normalize_usage_explanation(explanation),
        word_category=category,
    )
