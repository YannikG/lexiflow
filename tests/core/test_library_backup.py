"""Integration tests for library backup export and restore."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.library.backup import export_library_zip, restore_library_zip
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository


def test_export_and_restore_library_roundtrip(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    coordinator, index = LibraryCoordinator.open(source_root)
    del coordinator
    text_repo = TextRepository(source_root, index)
    text_repo.create_text(
        CreateTextRequest(
            title="Backed up",
            group="News",
            target_language="es",
            native_language="de",
            body="Contenido respaldado.",
        )
    )
    archive = tmp_path / "library-backup.zip"
    export_library_zip(archive, data_root=source_root)

    restored_root = tmp_path / "restored"
    restore_library_zip(archive, destination_root=restored_root)

    restored_index = LibraryIndex(restored_root)
    count = restored_index.rebuild_from_disk(restored_root)

    assert count == 1
    listed = restored_index.list_by_lang("es")
    assert len(listed) == 1
    assert listed[0].title == "Backed up"
