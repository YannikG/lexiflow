"""Integration tests for library full-text search."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.search import search_texts
from lexiflow_core.library.text_repository import TextRepository


@pytest.fixture
def library_search_setup(
    tmp_path: Path,
) -> tuple[Path, TextRepository, LibraryIndex]:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    text_repo = TextRepository(data_root, index)
    return data_root, text_repo, index


def test_search_finds_keyword_in_native_variant_body(
    library_search_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_search_setup
    text_repo.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="de",
            body="Contenido con palabraunica aqui.",
        )
    )

    hits = search_texts(index, lang="es", query="palabraunica")

    assert len(hits) == 1
    assert hits[0].variant == "native"


def test_search_scoped_to_target_language(
    library_search_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_search_setup
    text_repo.create_text(
        CreateTextRequest(
            title="Spanish",
            group="News",
            target_language="es",
            native_language="de",
            body="palabra espanola",
        )
    )
    text_repo.create_text(
        CreateTextRequest(
            title="German",
            group="News",
            target_language="de",
            native_language="en",
            body="palabra espanola",
        )
    )

    hits = search_texts(index, lang="es", query="palabra")

    assert len(hits) == 1
    assert hits[0].title == "Spanish"


def test_search_fuzzy_fallback_matches_typo(
    library_search_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_search_setup
    text_repo.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="de",
            body="Contenido con palabraunica aqui.",
        )
    )

    hits = search_texts(index, lang="es", query="palabreunica")

    assert len(hits) == 1


def test_search_snippet_contains_mark(
    library_search_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_search_setup
    text_repo.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="de",
            body="Contenido con palabraunica aqui.",
        )
    )

    hits = search_texts(index, lang="es", query="palabraunica")

    assert len(hits) == 1
    assert "<mark>" in hits[0].snippet or hits[0].match_offset is not None


def test_search_reflects_edits_without_cache(
    library_search_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_search_setup
    record = text_repo.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="de",
            body="Contenido inicial.",
        )
    )
    assert search_texts(index, lang="es", query="nuevotermino") == []

    text_repo.save_variant_edit(
        record.id,
        "native",
        "# Article\n\nContenido con nuevotermino aqui.",
    )

    hits = search_texts(index, lang="es", query="nuevotermino")

    assert len(hits) == 1
