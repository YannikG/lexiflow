"""Sanitize user group labels into filesystem-safe folder slugs."""

from __future__ import annotations

from lexiflow_core.library.slugify import slugify_segment


def slugify_group_name(display_name: str) -> str:
    """Convert a user-facing group label into a folder slug."""
    normalized = display_name.strip()
    if not normalized:
        raise ValueError("group name must not be empty")
    slug = slugify_segment(normalized, fallback="")
    if not slug:
        raise ValueError("group name must contain at least one alphanumeric character")
    return slug
