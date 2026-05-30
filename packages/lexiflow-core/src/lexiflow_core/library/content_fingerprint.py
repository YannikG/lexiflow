"""Content fingerprint for duplicate detection."""

from __future__ import annotations

import hashlib
import re


def normalize_for_fingerprint(text: str) -> str:
    """Normalize pasted or variant body text for stable comparison."""
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].strip().startswith("# "):
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines.pop()
    body = "\n".join(lines)
    return re.sub(r"\s+", " ", body.strip().lower())


def content_fingerprint(text: str) -> str:
    """Return a stable hash of normalized content."""
    normalized = normalize_for_fingerprint(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
