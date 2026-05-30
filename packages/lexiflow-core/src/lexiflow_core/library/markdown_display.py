"""Prepare markdown for reader display."""

from __future__ import annotations


def markdown_for_display(markdown: str, *, document_title: str | None) -> str:
    """Return markdown with a duplicate document-title H1 removed for rendering."""
    if document_title is None:
        return markdown
    lines = markdown.splitlines(keepends=True)
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        return markdown
    first_line = lines[index].strip()
    expected = f"# {document_title.strip()}"
    if first_line != expected:
        return markdown
    remainder_start = index + 1
    while remainder_start < len(lines) and not lines[remainder_start].strip():
        remainder_start += 1
    return "".join(lines[remainder_start:])
