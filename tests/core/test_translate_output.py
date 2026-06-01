"""Tests for translation LLM output validation."""

from __future__ import annotations

import pytest
from lexiflow_core.jobs.handlers.translate_output import (
    TranslateOutputError,
    validate_translate_output,
)


def test_validate_translate_output_rejects_unchanged_source() -> None:
    source = "# Article\n\nBody text"

    with pytest.raises(TranslateOutputError, match="unchanged"):
        validate_translate_output(source_markdown=source, translated=source)


def test_validate_translate_output_rejects_fences_only() -> None:
    source = "# Native\n\ncontent"

    with pytest.raises(TranslateOutputError, match="empty"):
        validate_translate_output(
            source_markdown=source,
            translated="```markdown\n```",
        )


def test_validate_translate_output_strips_markdown_fence() -> None:
    source = "# Native\n\ncontent"
    translated = "```markdown\n# Target\n\nbody\n```"

    normalized = validate_translate_output(
        source_markdown=source,
        translated=translated,
    )

    assert normalized == "# Target\n\nbody"


def test_validate_translate_output_accepts_single_newline_after_title() -> None:
    source = "# Native\n\ncontent"
    translated = "# Target\nbody text"

    normalized = validate_translate_output(
        source_markdown=source,
        translated=translated,
    )

    assert normalized == translated


def test_validate_translate_output_accepts_translated_markdown() -> None:
    source = "# Native\n\ncontent"
    translated = "# Target\n\nbody"

    normalized = validate_translate_output(
        source_markdown=source,
        translated=translated,
    )

    assert normalized == translated
