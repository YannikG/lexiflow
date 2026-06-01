"""Validate plain-translation LLM output before persistence."""

from __future__ import annotations

from lexiflow_core.library.document_title import (
    DocumentTitleError,
    parse_document_title,
)
from lexiflow_core.llm.markdown_fences import strip_llm_code_fence


class TranslateOutputError(Exception):
    """Raised when translation LLM output is not usable markdown."""


def validate_translate_output(*, source_markdown: str, translated: str) -> str:
    """Ensure translation differs from the source and has a document title."""
    normalized = strip_llm_code_fence(translated)
    if not normalized:
        raise TranslateOutputError("translation output is empty")
    if normalized == source_markdown.strip():
        raise TranslateOutputError("translation output is unchanged from the source")
    try:
        title = parse_document_title(normalized)
    except DocumentTitleError as exc:
        raise TranslateOutputError(str(exc)) from exc
    body = normalized.split("\n\n", 1)
    if len(body) < 2 or not body[1].strip():
        raise TranslateOutputError("translation output body is empty")
    if title.strip() == body[1].strip():
        raise TranslateOutputError("translation output body is empty")
    return normalized
