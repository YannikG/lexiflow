"""Tests for cleanup LLM output validation."""

from __future__ import annotations

import pytest
from lexiflow_core.jobs.handlers.cleanup_output import (
    CleanupOutputError,
    validate_cleanup_output,
)
from lexiflow_core.llm.markdown_fences import strip_llm_code_fence


def test_strip_llm_code_fence_removes_markdown_wrapper() -> None:
    cleaned = "```markdown\n# Article\n\nBody text\n```"

    assert strip_llm_code_fence(cleaned) == "# Article\n\nBody text"


def test_strip_llm_code_fence_removes_plain_wrapper() -> None:
    cleaned = "```\n# Article\n\nBody text\n```"

    assert strip_llm_code_fence(cleaned) == "# Article\n\nBody text"


def test_strip_llm_code_fence_leaves_unwrapped_content() -> None:
    cleaned = "# Article\n\nBody text"

    assert strip_llm_code_fence(cleaned) == cleaned


def test_strip_llm_code_fence_leaves_partial_wrapper() -> None:
    cleaned = "```markdown\n# Article\n\nBody text"

    assert strip_llm_code_fence(cleaned) == cleaned


def test_strip_llm_code_fence_strips_empty_wrapper() -> None:
    cleaned = "```markdown\n```"

    assert strip_llm_code_fence(cleaned) == ""


def test_validate_cleanup_output_rejects_empty() -> None:
    with pytest.raises(CleanupOutputError, match="empty"):
        validate_cleanup_output(raw_paste="raw", cleaned="   ")


def test_validate_cleanup_output_rejects_unchanged() -> None:
    paste = "messy paste without structure"
    with pytest.raises(CleanupOutputError, match="unchanged"):
        validate_cleanup_output(raw_paste=paste, cleaned=paste)


def test_validate_cleanup_output_rejects_empty_fence_wrapper() -> None:
    paste = "Line one\n\nLine two"
    with pytest.raises(CleanupOutputError, match="empty"):
        validate_cleanup_output(raw_paste=paste, cleaned="```markdown\n```")


def test_validate_cleanup_output_accepts_structured_markdown() -> None:
    paste = "Line one\n\nLine two"
    cleaned = "# Article\n\nLine one\n\nLine two"

    normalized = validate_cleanup_output(raw_paste=paste, cleaned=cleaned)

    assert normalized == cleaned


def test_validate_cleanup_output_strips_markdown_fence() -> None:
    paste = "Line one\n\nLine two"
    cleaned = "```markdown\n# Article\n\nLine one\n\nLine two\n```"

    normalized = validate_cleanup_output(raw_paste=paste, cleaned=cleaned)

    assert normalized == "# Article\n\nLine one\n\nLine two"
