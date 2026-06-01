"""Tests for prompt language labels."""

from __future__ import annotations

from lexiflow_core.llm.prompt_languages import prompt_language_label


def test_prompt_language_label_uses_catalog_name() -> None:
    assert prompt_language_label("de") == "German (de)"
    assert prompt_language_label("uk") == "Ukrainian (uk)"


def test_prompt_language_label_falls_back_to_iso() -> None:
    assert prompt_language_label("xx") == "xx"
