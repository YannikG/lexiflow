"""Tests for reader tab memory in the library index."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.reader_tabs import NATIVE_TAB, resolve_open_tab
from lexiflow_core.library.text_repository import TextRepository


def test_set_and_get_last_viewed_tab(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Hola",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )

    assert index.get_last_viewed_tab(record.id) is None
    index.set_last_viewed_tab(record.id, NATIVE_TAB)
    assert index.get_last_viewed_tab(record.id) == NATIVE_TAB


def test_resolve_open_tab_uses_last_viewed_when_available(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Hola",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    index.set_last_viewed_tab(record.id, NATIVE_TAB)

    tab = resolve_open_tab(
        index.get_last_viewed_tab(record.id),
        available_variants=("native", "translated"),
        simplified_variants=(),
    )
    assert tab == NATIVE_TAB


def test_resolve_open_tab_defaults_to_translated_on_first_open() -> None:
    tab = resolve_open_tab(
        None,
        available_variants=("native", "translated"),
        simplified_variants=(),
    )
    assert tab == "translated"


def test_upsert_text_preserves_last_viewed_tab(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Hola",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    index.set_last_viewed_tab(record.id, NATIVE_TAB)

    updated = repo.save_variant_edit(
        record.id,
        "native",
        "# Hola\n\nUpdated body.",
    )
    assert updated.title == "Hola"
    assert index.get_last_viewed_tab(record.id) == NATIVE_TAB


def test_get_text_includes_last_viewed_tab_from_index(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Hola",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    index.set_last_viewed_tab(record.id, NATIVE_TAB)

    loaded = repo.get_text(record.id)

    assert loaded.last_viewed_tab == NATIVE_TAB
