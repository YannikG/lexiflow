"""Shared slugification for on-disk folder names."""

from __future__ import annotations

import re

_UNSAFE_CHARS = re.compile(r"[/\\:\0]+")
_WHITESPACE = re.compile(r"\s+")
_NON_SLUG = re.compile(r"[^a-z0-9-]+")
_EDGE_DOTS = re.compile(r"^\.+|\.+$")


def slugify_segment(value: str, *, fallback: str = "item") -> str:
    """Normalize a label into a lowercase kebab-case filesystem segment."""
    normalized = value.strip()
    if not normalized:
        return fallback
    normalized = _UNSAFE_CHARS.sub("-", normalized)
    normalized = _WHITESPACE.sub("-", normalized)
    normalized = normalized.lower()
    normalized = _NON_SLUG.sub("-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    normalized = _EDGE_DOTS.sub("", normalized)
    return normalized or fallback
