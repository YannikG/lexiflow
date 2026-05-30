"""Tests for markdown display preparation."""

from __future__ import annotations

from lexiflow_core.library.markdown_display import markdown_for_display


def test_keeps_document_title_heading_in_rendered_markdown() -> None:
    markdown = "# Hola\n\nCuerpo."

    rendered = markdown_for_display(markdown, document_title="Hola")

    assert rendered == markdown
    assert rendered.startswith("# Hola")


def test_keeps_body_when_title_heading_differs() -> None:
    markdown = "# Otro título\n\nCuerpo."

    rendered = markdown_for_display(markdown, document_title="Hola")

    assert rendered == markdown


def test_no_title_argument_returns_original_markdown() -> None:
    markdown = "# Hola\n\nCuerpo."

    assert markdown_for_display(markdown, document_title=None) == markdown
