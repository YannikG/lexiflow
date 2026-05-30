"""Prepare markdown for reader display."""

from __future__ import annotations


def markdown_for_display(markdown: str, *, document_title: str | None = None) -> str:
    """Return markdown for reader rendering.

    The reader header shows the library title separately; variant H1 stays in the body.
    """
    _ = document_title
    return markdown
