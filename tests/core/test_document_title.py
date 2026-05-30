"""Tests for document title formatting."""

from __future__ import annotations

import pytest
from lexiflow_core.library.document_title import (
    DocumentTitleError,
    format_document_title,
    format_native_variant,
    normalize_document_title,
    parse_document_title,
)


def test_format_document_title() -> None:
    assert format_document_title("Hola mundo") == "# Hola mundo\n\n"


def test_format_native_variant_includes_body() -> None:
    assert format_native_variant("Hola", "Contenido.") == "# Hola\n\nContenido."


def test_format_document_title_rejects_hash() -> None:
    with pytest.raises(DocumentTitleError, match="#"):
        format_document_title("Bad # title")


def test_normalize_document_title_strips_whitespace() -> None:
    assert normalize_document_title("  Hola  ") == "Hola"


def test_normalize_document_title_rejects_empty() -> None:
    with pytest.raises(DocumentTitleError, match="empty"):
        normalize_document_title("   ")


def test_parse_document_title() -> None:
    assert parse_document_title("# Titulo\n\ncuerpo") == "Titulo"
