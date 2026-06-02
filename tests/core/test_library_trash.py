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
from lexiflow_core.library.trash import TrashItemNotFoundError, trashed_text_ids


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


def test_list_trash_filters_by_language(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, _ = library_trash_setup
    es = text_repo.create_text(
        CreateTextRequest(
            title="Spanish",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    de = text_repo.create_text(
        CreateTextRequest(
            title="German",
            group="News",
            target_language="de",
            native_language="en",
        )
    )
    text_repo.delete_to_trash(es.id)
    text_repo.delete_to_trash(de.id)

    assert len(text_repo.list_trash(language_code="es")) == 1
    assert text_repo.list_trash(language_code="es")[0].title == "Spanish"


def test_trashed_text_ids_filters_by_language(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _ = library_trash_setup
    es = text_repo.create_text(
        CreateTextRequest(
            title="Spanish",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    de = text_repo.create_text(
        CreateTextRequest(
            title="German",
            group="News",
            target_language="de",
            native_language="en",
        )
    )
    text_repo.delete_to_trash(es.id)
    text_repo.delete_to_trash(de.id)

    assert trashed_text_ids(data_root, language_code="es") == frozenset({es.id})
    assert trashed_text_ids(data_root, language_code="de") == frozenset({de.id})


def test_empty_trash_filters_by_language(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _ = library_trash_setup
    es = text_repo.create_text(
        CreateTextRequest(
            title="Spanish",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    de = text_repo.create_text(
        CreateTextRequest(
            title="German",
            group="News",
            target_language="de",
            native_language="en",
        )
    )
    text_repo.delete_to_trash(es.id)
    text_repo.delete_to_trash(de.id)

    removed = text_repo.empty_trash(language_code="es")

    assert removed == 1
    assert len(text_repo.list_trash(language_code="es")) == 0
    assert len(text_repo.list_trash(language_code="de")) == 1
    assert (data_root / ".trash" / str(de.id)).is_dir()


def test_list_by_lang_excludes_trashed_text_with_stale_index_row(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    data_root, text_repo, index = library_trash_setup
    from lexiflow_core.library.text_storage import TextStorage

    record = text_repo.create_text(
        CreateTextRequest(
            title="Stale index",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    TextStorage(data_root).move_to_trash(Path(record.folder), record.id)

    assert index.get_by_id(record.id) is None
    assert index.list_by_lang("es") == []


def test_search_excludes_trashed_text_with_stale_fts_row(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_trash_setup

    record = text_repo.create_text(
        CreateTextRequest(
            title="Hidden from search",
            group="News",
            target_language="es",
            native_language="de",
            body="palabraunica",
        )
    )
    text_repo.delete_to_trash(record.id)
    connection = index._connect()  # noqa: SLF001
    try:
        connection.execute(
            """
            INSERT INTO text_search (text_id, lang, variant, title, body)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(record.id), "es", "native", record.title, "palabraunica"),
        )
        connection.commit()
    finally:
        connection.close()

    assert search_texts(index, lang="es", query="palabraunica") == []


def test_purge_trashed_texts_removes_stale_index_rows(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    data_root, text_repo, index = library_trash_setup
    from lexiflow_core.library.text_storage import TextStorage

    record = text_repo.create_text(
        CreateTextRequest(
            title="Purge me",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    TextStorage(data_root).move_to_trash(Path(record.folder), record.id)
    connection = index._connect()  # noqa: SLF001
    try:
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM texts WHERE id = ?",
                (str(record.id),),
            ).fetchone()[0]
            == 1
        )
    finally:
        connection.close()

    removed = index.purge_trashed_texts()

    assert removed == 1
    assert index.get_by_id(record.id) is None


def test_rebuild_from_disk_counts_only_active_texts_after_partial_trash(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_trash_setup
    active = text_repo.create_text(
        CreateTextRequest(
            title="Still here A",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    still_b = text_repo.create_text(
        CreateTextRequest(
            title="Still here B",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    trashed_a = text_repo.create_text(
        CreateTextRequest(
            title="The Metamorphosis",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    trashed_b = text_repo.create_text(
        CreateTextRequest(
            title="The Little Prince",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    text_repo.delete_to_trash(trashed_a.id)
    text_repo.delete_to_trash(trashed_b.id)

    count = index.rebuild_from_disk()

    assert count == 2
    listed = index.list_by_lang("es")
    assert len(listed) == 2
    assert {record.id for record in listed} == {active.id, still_b.id}


def test_rebuild_from_disk_excludes_trashed_texts(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    _, text_repo, index = library_trash_setup
    record = text_repo.create_text(
        CreateTextRequest(
            title="Rebuild skip",
            group="News",
            target_language="es",
            native_language="de",
            body="palabraunica",
        )
    )
    text_repo.delete_to_trash(record.id)

    count = index.rebuild_from_disk()

    assert count == 0
    assert index.list_by_lang("es") == []
    assert search_texts(index, lang="es", query="palabraunica") == []


def test_rebuild_from_disk_excludes_trashed_text_with_stale_library_copy(
    library_trash_setup: tuple[Path, TextRepository, LibraryIndex],
) -> None:
    data_root, text_repo, index = library_trash_setup
    from lexiflow_core.library.text_storage import TextStorage

    record = text_repo.create_text(
        CreateTextRequest(
            title="Duplicate on disk",
            group="News",
            target_language="es",
            native_language="de",
            body="palabraunica",
        )
    )
    TextStorage(data_root).move_to_trash(Path(record.folder), record.id)
    stale_library_copy = data_root / "es" / record.group_folder_slug / record.text_slug
    stale_library_copy.mkdir(parents=True, exist_ok=True)
    trash_meta = trash_dir(data_root) / str(record.id) / "meta.json"
    (stale_library_copy / "meta.json").write_text(
        trash_meta.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    count = index.rebuild_from_disk(data_root)

    assert count == 0
    assert index.list_by_lang("es") == []
    assert search_texts(index, lang="es", query="palabraunica") == []
