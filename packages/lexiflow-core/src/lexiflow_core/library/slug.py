"""Text slug generation for on-disk folders."""

from __future__ import annotations

import secrets

from lexiflow_core.library.slugify import slugify_segment


class TextSlugError(Exception):
    """Raised when a unique text folder slug cannot be allocated."""


def make_text_slug(title: str, *, suffix: str | None = None) -> str:
    """Derive a text folder slug from a title plus a short random suffix."""
    base = slugify_segment(title, fallback="text")
    token = suffix if suffix is not None else secrets.token_hex(2)
    return f"{base}-{token}"
