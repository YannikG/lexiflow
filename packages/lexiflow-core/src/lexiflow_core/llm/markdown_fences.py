"""Normalize markdown returned by LLMs."""

from __future__ import annotations


def strip_llm_code_fence(text: str) -> str:
    """Remove optional ```markdown / ``` wrappers from LLM output."""
    normalized = text.strip()
    if not normalized.startswith("```"):
        return normalized
    first_newline = normalized.find("\n")
    if first_newline == -1:
        return normalized
    opener = normalized[3:first_newline].strip().lower()
    if opener not in ("", "markdown", "md"):
        return normalized
    body = normalized[first_newline + 1 :].rstrip()
    if not body.endswith("```"):
        return normalized
    stripped = body[:-3].rstrip()
    if not stripped:
        return ""
    return stripped
