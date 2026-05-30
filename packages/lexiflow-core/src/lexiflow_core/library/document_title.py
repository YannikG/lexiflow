"""Document title formatting for variant markdown files."""

from __future__ import annotations


class DocumentTitleError(Exception):
    """Raised when a title cannot be used as a markdown heading."""


def normalize_document_title(title: str) -> str:
    """Return a validated library title string."""
    normalized = title.strip()
    if not normalized:
        raise DocumentTitleError("title must not be empty")
    if "\n" in normalized:
        raise DocumentTitleError("title must be a single line")
    if "#" in normalized:
        raise DocumentTitleError("title must not contain '#'")
    return normalized


def format_document_title(title: str) -> str:
    """Return markdown with the document title as the top-level heading."""
    return f"# {normalize_document_title(title)}\n\n"


def format_native_variant(title: str, body: str) -> str:
    """Format native variant content with document title heading."""
    return format_document_title(title) + body


def parse_document_title(markdown: str) -> str:
    """Extract the document title from the first top-level markdown heading."""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title:
                return title
    raise DocumentTitleError("no document title heading found")
