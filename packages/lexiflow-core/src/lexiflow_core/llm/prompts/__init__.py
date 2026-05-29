"""Versioned LLM prompt templates."""

from __future__ import annotations

from importlib import resources

__all__ = ["PromptNotFoundError", "load_prompt", "render_prompt"]

_PROMPTS_PACKAGE = "lexiflow_core.llm.prompts"


class PromptNotFoundError(Exception):
    """Raised when a named prompt template file does not exist."""


def load_prompt(name: str) -> str:
    """Load a prompt template by name (without .md extension)."""
    filename = f"{name}.md"
    try:
        return (
            resources.files(_PROMPTS_PACKAGE)
            .joinpath(filename)
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, TypeError, OSError) as exc:
        raise PromptNotFoundError(f"prompt not found: {name}") from exc


def render_prompt(name: str, **values: str) -> str:
    """Load and format a prompt template with the given placeholder values."""
    return load_prompt(name).format(**values)
