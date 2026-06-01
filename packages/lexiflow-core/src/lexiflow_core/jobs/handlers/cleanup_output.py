"""Validate markdown cleanup LLM output before persistence."""

from __future__ import annotations

from lexiflow_core.library.document_title import (
    DocumentTitleError,
    parse_document_title,
)
from lexiflow_core.llm.markdown_fences import strip_llm_code_fence


class CleanupOutputError(Exception):
    """Raised when cleanup LLM output is not usable markdown."""


def validate_cleanup_output(*, raw_paste: str, cleaned: str) -> str:
    """Ensure cleaned output is structured markdown that differs from the paste."""
    normalized = strip_llm_code_fence(cleaned)
    if not normalized:
        raise CleanupOutputError("cleanup output is empty")
    if normalized == raw_paste.strip():
        raise CleanupOutputError("cleanup output is unchanged from the pasted content")
    try:
        title = parse_document_title(normalized)
    except DocumentTitleError as exc:
        raise CleanupOutputError(str(exc)) from exc
    body = normalized.split("\n\n", 1)
    if len(body) < 2 or not body[1].strip():
        raise CleanupOutputError("cleanup output body is empty")
    if title.strip() == body[1].strip():
        raise CleanupOutputError("cleanup output body is empty")
    return normalized
