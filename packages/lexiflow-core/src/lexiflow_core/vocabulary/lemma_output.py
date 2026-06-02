"""Parse lemma inference LLM JSON output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


class LemmaOutputError(Exception):
    """Raised when lemma LLM output is invalid."""


@dataclass(frozen=True)
class LemmaInferenceResult:
    lemma: str
    translation: str
    explanation: str


def lemma_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "lemma": {"type": "string"},
            "translation": {"type": "string"},
            "explanation": {"type": "string"},
        },
        "required": ["lemma", "translation", "explanation"],
    }


def parse_lemma_output(raw: str) -> LemmaInferenceResult:
    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LemmaOutputError("lemma output is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise LemmaOutputError("lemma output must be an object")
    lemma = parsed.get("lemma")
    translation = parsed.get("translation")
    explanation = parsed.get("explanation")
    if not isinstance(lemma, str) or not lemma.strip():
        raise LemmaOutputError("lemma must be a non-empty string")
    if not isinstance(translation, str) or not translation.strip():
        raise LemmaOutputError("translation must be a non-empty string")
    if not isinstance(explanation, str):
        raise LemmaOutputError("explanation must be a string")
    return LemmaInferenceResult(
        lemma=lemma.strip().lower(),
        translation=translation.strip(),
        explanation=explanation.strip(),
    )
