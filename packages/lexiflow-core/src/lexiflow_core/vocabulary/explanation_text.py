"""Normalize usage explanations from LLM output."""

from __future__ import annotations

import re

_EXPLANATION_PREFIXES = (
    re.compile(r"^this word refers to\s+", re.IGNORECASE),
    re.compile(r"^this word means\s+", re.IGNORECASE),
    re.compile(r"^this refers to\s+", re.IGNORECASE),
    re.compile(r"^the word refers to\s+", re.IGNORECASE),
    re.compile(r"^this term refers to\s+", re.IGNORECASE),
    re.compile(r"^this means\s+", re.IGNORECASE),
    re.compile(r"^dieses wort bezeichnet\s+", re.IGNORECASE),
    re.compile(r"^das wort bezeichnet\s+", re.IGNORECASE),
    re.compile(r"^dieses wort bedeutet\s+", re.IGNORECASE),
    re.compile(r"^das wort bedeutet\s+", re.IGNORECASE),
    re.compile(r"^dieses wort bezieht sich auf\s+", re.IGNORECASE),
    re.compile(r"^das wort bezieht sich auf\s+", re.IGNORECASE),
)


def normalize_usage_explanation(explanation: str) -> str:
    """Strip common meta phrasing from a one-line usage explanation."""
    text = explanation.strip()
    if not text:
        return text
    for pattern in _EXPLANATION_PREFIXES:
        stripped = pattern.sub("", text, count=1)
        if stripped != text:
            text = stripped.strip()
            break
    if not text:
        return text
    return text[0].upper() + text[1:]
