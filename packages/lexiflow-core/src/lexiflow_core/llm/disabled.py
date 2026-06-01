"""LLM provider that fails when the LLM toggle is off."""

from __future__ import annotations

LLM_DISABLED_MESSAGE = (
    "LLM is disabled in settings. Enable the LLM toggle to run translate, "
    "cleanup, and simplify jobs."
)


class LLMDisabledError(Exception):
    """Raised when completion is requested while LLM is disabled."""


class DisabledLLM:
    def complete(
        self, prompt: str, *, json_schema: dict[str, object] | None = None
    ) -> str:
        del prompt, json_schema
        raise LLMDisabledError(LLM_DISABLED_MESSAGE)
