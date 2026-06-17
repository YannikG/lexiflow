"""Tests for LLM prompt template loading."""

from __future__ import annotations

import pytest
from lexiflow_core.llm.prompts import PromptNotFoundError, load_prompt


def test_load_cleanup_prompt_is_non_empty() -> None:
    content = load_prompt("cleanup")
    assert content.strip()


def test_cleanup_prompt_forbids_translation_out_of_source_language() -> None:
    content = load_prompt("cleanup").lower()
    assert "source language" in content
    assert "do not translate" in content
    assert "{source_language}" in content


def test_load_missing_prompt_raises() -> None:
    with pytest.raises(PromptNotFoundError, match="nonexistent"):
        load_prompt("nonexistent")


def test_simplify_prompt_requires_prose_not_bullet_summary() -> None:
    content = load_prompt("simplify").lower()
    assert "not a summary" in content
    assert "bullet" in content
    assert "paragraph" in content
