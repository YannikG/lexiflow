"""Integration tests for library trash restore."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.paths import trash_dir
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.search import search_texts
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.library.trash import TrashItemNotFoundError


@pytest.fixture
def library_trash_setup(
    tmp_path: Path,
) -> tuple[Path, TextRepository, LibraryIndex]:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    text_repo = TextRepository(data_root, index)
    return data_root, text_repo, index


def test_delete_to_trash_removes_fts_rows(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    data_root, text_repo, index = library_trash_setup
    record = text_repo.create_text(
        CreateTextRequest(
            title="Trash me",
            group="News",
            target_language="es",
            native_language="de",
            body="palabraunica",
        )
    )
    assert search_texts(index, lang="es", query="palabraunica")

    text_repo.delete_to_trash(record.id)

    assert search_texts(index, lang="es", query="palabraunica") == []
    assert (data_root / ".trash" / str(record.id)).is_dir()


def test_restore_from_trash_reindexes_text(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_trash_setup
    record = text_repo.create_text(
        CreateTextRequest(
            title="Restore me",
            group="News",
            target_language="es",
            native_language="de",
            body="palabraunica",
        )
    )
    text_repo.delete_to_trash(record.id)
    assert index.list_by_lang("es") == []

    text_repo.restore_from_trash(record.id)

    assert len(index.list_by_lang("es")) == 1
    assert search_texts(index, lang="es", query="palabraunica")


def test_empty_trash_permanently_deletes(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _ = library_trash_setup
    record = text_repo.create_text(
        CreateTextRequest(
            title="Gone",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    text_repo.delete_to_trash(record.id)

    removed = text_repo.empty_trash()

    assert removed == 1
    assert not (trash_dir(data_root) / str(record.id)).exists()
    with pytest.raises(TrashItemNotFoundError):
        text_repo.restore_from_trash(record.id)


def test_list_trash_returns_deleted_texts(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, _ = library_trash_setup
    record = text_repo.create_text(
        CreateTextRequest(
            title="Listed",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    text_repo.delete_to_trash(record.id)

    items = text_repo.list_trash()

    assert len(items) == 1
    assert items[0].text_id == record.id
    assert items[0].title == "Listed"
