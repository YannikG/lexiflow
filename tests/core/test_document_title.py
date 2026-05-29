"""Tests for document title formatting."""

from __future__ import annotations

import pytest
from lexiflow_core.library.document_title import (
    DocumentTitleError,
    format_document_title,
    format_native_variant,
)


def test_format_document_title() -> None:
    assert format_document_title("Hola mundo") == "# Hola mundo\n\n"


def test_format_native_variant_includes_body() -> None:
    assert format_native_variant("Hola", "Contenido.") == "# Hola\n\nContenido."


def test_format_document_title_rejects_hash() -> None:
    with pytest.raises(DocumentTitleError, match="#"):
        format_document_title("Bad # title")
