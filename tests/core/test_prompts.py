"""Tests for LLM prompt template loading."""

from __future__ import annotations

import pytest
from lexiflow_core.llm.prompts import PromptNotFoundError, load_prompt


def test_load_cleanup_prompt_is_non_empty() -> None:
    content = load_prompt("cleanup")
    assert content.strip()


def test_load_missing_prompt_raises() -> None:
    with pytest.raises(PromptNotFoundError, match="nonexistent"):
        load_prompt("nonexistent")
