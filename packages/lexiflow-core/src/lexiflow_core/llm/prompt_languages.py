"""Human-readable language labels for LLM prompts."""

from __future__ import annotations

from lexiflow_core.languages.catalog import get_language


def prompt_language_label(iso: str) -> str:
    """Return a prompt-friendly language label for an ISO 639-1 code."""
    try:
        info = get_language(iso)
    except KeyError:
        return iso
    return f"{info.name} ({iso})"
