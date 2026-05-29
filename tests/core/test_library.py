"""Integration tests for library texts, groups, and index."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest
from lexiflow_core.config.paths import (
    groups_json_path,
    meta_path,
    text_dir,
    variant_path,
)
from lexiflow_core.library.document_title import DocumentTitleError
from lexiflow_core.library.group_repository import GroupNotEmptyError, GroupRepository
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_metadata import TextMetadataError, load_text_metadata
from lexiflow_core.library.text_repository import TextNotFoundError, TextRepository


@pytest.fixture
def library(
    tmp_path: Path,
) -> tuple[Path, TextRepository, GroupRepository, LibraryIndex]:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    text_repo = TextRepository(data_root, index)
    group_repo = GroupRepository(data_root, index)
    return data_root, text_repo, group_repo, index


def test_create_text_writes_metadata_and_group_registry(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _, _ = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Hola mundo",
            group="News/Politics",
            target_language="es",
            native_language="de",
            body="Contenido inicial.",
        )
    )

    text_folder = Path(record.folder)
    assert text_folder.is_dir()
    assert text_folder.parent.name == "news-politics"

    metadata = load_text_metadata(meta_path(text_folder))
    assert metadata.title == "Hola mundo"
    assert metadata.group == "News/Politics"
    assert isinstance(metadata.id, UUID)

    groups = json.loads(groups_json_path(data_root, "es").read_text(encoding="utf-8"))
    assert groups["news-politics"] == "News/Politics"


def test_create_text_writes_native_variant_with_document_title(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    _, text_repo, _, _ = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Hola mundo",
            group="News",
            target_language="es",
            native_language="de",
            body="Contenido.",
        )
    )

    native = variant_path(Path(record.folder), "native").read_text(encoding="utf-8")
    assert native.startswith("# Hola mundo\n\n")


def test_create_text_rejects_title_with_hash(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    _, text_repo, _, _ = library
    with pytest.raises(DocumentTitleError, match="#"):
        text_repo.create_text(
            CreateTextRequest(
                title="Bad # title",
                group="News",
                target_language="es",
                native_language="de",
            )
        )


def test_create_text_resolves_slug_collision(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _, _ = library
    from lexiflow_core.library.slug import make_text_slug

    blocked_slug = make_text_slug("Article", suffix="dead")
    blocked_folder = text_dir(data_root, "es", "news", blocked_slug)
    blocked_folder.parent.mkdir(parents=True, exist_ok=True)
    blocked_folder.mkdir()

    record = text_repo.create_text(
        CreateTextRequest(
            title="Article",
            group="News",
            target_language="es",
            native_language="de",
        )
    )

    assert Path(record.folder).name != blocked_slug
    assert blocked_folder.is_dir()
    assert Path(record.folder).is_dir()


def test_index_lists_text_after_create(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    _, text_repo, _, index = library
    created = text_repo.create_text(
        CreateTextRequest(
            title="Hola",
            group="News",
            target_language="es",
            native_language="de",
        )
    )

    listed = index.list_by_lang("es")

    assert len(listed) == 1
    assert listed[0].id == created.id
    assert listed[0].title == "Hola"
    assert listed[0].group == "News"
    assert listed[0].native_language == "de"
    assert listed[0].variants == ("native",)


def test_list_by_lang_reads_from_index_without_meta_json(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    _, text_repo, _, index = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Cached",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    meta_path(Path(record.folder)).unlink()

    listed = index.list_by_lang("es")

    assert len(listed) == 1
    assert listed[0].title == "Cached"
    assert listed[0].native_language == "de"


def test_rebuild_from_disk_syncs_manual_metadata_edit(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _, index = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Original",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    meta_file = meta_path(Path(record.folder))
    payload = json.loads(meta_file.read_text(encoding="utf-8"))
    payload["title"] = "Edited on disk"
    meta_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    count = index.rebuild_from_disk(data_root)

    assert count == 1
    assert index.list_by_lang("es")[0].title == "Edited on disk"


def test_rebuild_uses_registry_display_name_without_writing_meta(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _, index = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Sync",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    meta_file = meta_path(Path(record.folder))
    payload = json.loads(meta_file.read_text(encoding="utf-8"))
    payload["group"] = "Stale label"
    meta_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    index.rebuild_from_disk(data_root)

    assert index.list_by_lang("es")[0].group == "News"
    assert load_text_metadata(meta_file).group == "Stale label"


def test_rebuild_repairs_missing_groups_registry_entry(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _, index = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Repair",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    groups_path = groups_json_path(data_root, "es")
    groups_path.unlink()

    index.rebuild_from_disk(data_root)

    groups = json.loads(groups_path.read_text(encoding="utf-8"))
    assert groups["news"] == "News"
    assert index.list_by_lang("es")[0].id == record.id


def test_move_to_group_relocates_folder_and_updates_index(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, text_repo, group_repo, index = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Mover",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    old_folder = Path(record.folder)
    group_repo.create_group("es", "Podcasts")

    text_repo.move_to_group(record.id, "Podcasts")

    new_folder = data_root / "es" / "podcasts" / old_folder.name
    assert not old_folder.exists()
    assert new_folder.is_dir()
    assert load_text_metadata(meta_path(new_folder)).group == "Podcasts"
    assert index.list_by_lang("es")[0].group == "Podcasts"


def test_rename_group_updates_text_metadata_and_index(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, text_repo, group_repo, index = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Titulo",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    group_repo.rename_group("es", "News", "Headlines")

    text_folder = data_root / "es" / "headlines" / Path(record.folder).name
    assert text_folder.is_dir()
    assert load_text_metadata(meta_path(text_folder)).group == "Headlines"
    assert index.list_by_lang("es")[0].group == "Headlines"


def test_delete_if_empty_rejects_non_empty_group(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    _, text_repo, group_repo, _ = library
    text_repo.create_text(
        CreateTextRequest(
            title="Occupied",
            group="News",
            target_language="es",
            native_language="de",
        )
    )

    with pytest.raises(GroupNotEmptyError):
        group_repo.delete_if_empty("es", "News")


def test_delete_if_empty_removes_empty_group(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, _, group_repo, _ = library
    group_repo.create_group("es", "Empty")

    group_repo.delete_if_empty("es", "Empty")

    assert not (data_root / "es" / "empty").exists()
    assert "empty" not in json.loads(
        groups_json_path(data_root, "es").read_text(encoding="utf-8")
    )


def test_load_text_metadata_rejects_level_key_on_disk(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    _, text_repo, _, _ = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Level test",
            group="News",
            target_language="es",
            native_language="de",
        )
    )
    meta_file = meta_path(Path(record.folder))
    payload = json.loads(meta_file.read_text(encoding="utf-8"))
    payload["level"] = "A2"
    meta_file.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TextMetadataError, match="forbidden metadata keys"):
        text_repo.get_text(record.id)


def test_delete_to_trash_moves_folder_and_removes_from_index(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    data_root, text_repo, _, index = library
    record = text_repo.create_text(
        CreateTextRequest(
            title="Trash me",
            group="News",
            target_language="es",
            native_language="de",
        )
    )

    text_repo.delete_to_trash(record.id)

    assert not Path(record.folder).exists()
    assert (data_root / ".trash" / str(record.id)).is_dir()
    assert index.list_by_lang("es") == []


def test_get_text_not_found(
    library: tuple[Path, TextRepository, GroupRepository, LibraryIndex],
) -> None:
    _, text_repo, _, _ = library

    with pytest.raises(TextNotFoundError):
        text_repo.get_text(UUID("00000000-0000-0000-0000-000000000001"))
