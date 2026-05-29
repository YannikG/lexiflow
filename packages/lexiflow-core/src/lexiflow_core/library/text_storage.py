"""Disk-only text folder operations."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from lexiflow_core.config.paths import (
    group_dir,
    meta_path,
    text_dir,
    trash_dir,
    variant_path,
)
from lexiflow_core.library.document_title import format_native_variant
from lexiflow_core.library.models import CreateTextRequest, TextRecord
from lexiflow_core.library.slug import TextSlugError, make_text_slug
from lexiflow_core.library.text_metadata import (
    TextMetadata,
    load_text_metadata,
    metadata_to_record,
    save_text_metadata,
)


class TextStorage:
    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root

    def create(self, req: CreateTextRequest, *, group_folder_slug: str) -> TextRecord:
        """Write a new text folder, metadata, and native variant."""
        text_slug = self._allocate_text_slug(
            req.target_language, group_folder_slug, req.title
        )
        folder = text_dir(
            self._data_root, req.target_language, group_folder_slug, text_slug
        )
        now = datetime.now(UTC)
        metadata = TextMetadata(
            id=uuid4(),
            title=req.title,
            group=req.group,
            native_language=req.native_language,
            target_language=req.target_language,
            variants=("native",),
            source_url=req.source_url,
            created_at=now,
            updated_at=now,
        )
        save_text_metadata(meta_path(folder), metadata)
        native_content = format_native_variant(req.title, req.body)
        variant_path(folder, "native").write_text(native_content, encoding="utf-8")
        return metadata_to_record(
            metadata,
            group_folder_slug=group_folder_slug,
            text_slug=text_slug,
            folder=str(folder),
        )

    def load(self, folder: Path) -> TextRecord:
        """Load a text record from its on-disk folder."""
        metadata = load_text_metadata(meta_path(folder))
        return metadata_to_record(
            metadata,
            group_folder_slug=folder.parent.name,
            text_slug=folder.name,
            folder=str(folder),
        )

    def move_folder(
        self,
        folder: Path,
        *,
        target_language: str,
        group_folder_slug: str,
        group_display: str,
    ) -> TextRecord:
        """Relocate a text folder to another group and update metadata."""
        new_folder = text_dir(
            self._data_root, target_language, group_folder_slug, folder.name
        )
        group_dir(self._data_root, target_language, group_folder_slug).mkdir(
            parents=True, exist_ok=True
        )
        shutil.move(str(folder), str(new_folder))
        metadata = load_text_metadata(meta_path(new_folder))
        updated = TextMetadata(
            id=metadata.id,
            title=metadata.title,
            group=group_display,
            native_language=metadata.native_language,
            target_language=metadata.target_language,
            variants=metadata.variants,
            source_url=metadata.source_url,
            created_at=metadata.created_at,
            updated_at=datetime.now(UTC),
        )
        save_text_metadata(meta_path(new_folder), updated)
        return metadata_to_record(
            updated,
            group_folder_slug=group_folder_slug,
            text_slug=new_folder.name,
            folder=str(new_folder),
        )

    def move_to_trash(self, folder: Path, text_id: UUID) -> None:
        """Move a text folder into the trash area."""
        destination_root = trash_dir(self._data_root)
        destination_root.mkdir(parents=True, exist_ok=True)
        destination = destination_root / str(text_id)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(folder), str(destination))

    def update_group_label_in_folder(
        self, text_folder: Path, *, group_display: str, group_folder_slug: str
    ) -> TextRecord:
        """Patch group display name in text metadata after a group rename."""
        metadata = load_text_metadata(meta_path(text_folder))
        updated = TextMetadata(
            id=metadata.id,
            title=metadata.title,
            group=group_display,
            native_language=metadata.native_language,
            target_language=metadata.target_language,
            variants=metadata.variants,
            source_url=metadata.source_url,
            created_at=metadata.created_at,
            updated_at=datetime.now(UTC),
        )
        save_text_metadata(meta_path(text_folder), updated)
        return metadata_to_record(
            updated,
            group_folder_slug=group_folder_slug,
            text_slug=text_folder.name,
            folder=str(text_folder),
        )

    def _allocate_text_slug(
        self, language_code: str, group_folder_slug: str, title: str
    ) -> str:
        for _ in range(20):
            candidate = make_text_slug(title)
            folder = text_dir(
                self._data_root, language_code, group_folder_slug, candidate
            )
            if not folder.exists():
                return candidate
        raise TextSlugError("could not allocate unique text slug")
