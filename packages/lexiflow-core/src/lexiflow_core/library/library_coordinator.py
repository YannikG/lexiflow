"""Orchestrates library storage, groups, and index synchronization."""

from __future__ import annotations

import weakref
from pathlib import Path
from uuid import UUID

from lexiflow_core.config.app_layout import ensure_app_layout
from lexiflow_core.library.group_registry import GroupNotFoundError
from lexiflow_core.library.group_storage import GroupStorage
from lexiflow_core.library.index import LibraryIndex, ensure_library_index
from lexiflow_core.library.models import CreateTextRequest, TextRecord
from lexiflow_core.library.text_storage import TextStorage


class GroupNotEmptyError(Exception):
    """Raised when deleting a group that still contains texts."""


class TextNotFoundError(Exception):
    """Raised when a text id does not exist."""


class LibraryCoordinator:
    def __init__(self, data_root: Path, index: LibraryIndex) -> None:
        self._data_root = data_root
        self._index = index
        self._texts = TextStorage(data_root)
        self._groups = GroupStorage(data_root)

    @classmethod
    def open(cls, data_root: Path) -> tuple[LibraryCoordinator, LibraryIndex]:
        """Prepare layout, migrate the index, and return a coordinator."""
        ensure_app_layout(data_root)
        ensure_library_index(data_root)
        index = LibraryIndex(data_root)
        return cls(data_root, index), index

    def create_text(self, req: CreateTextRequest) -> TextRecord:
        group_folder_slug = self._groups.register(req.target_language, req.group)
        record = self._texts.create(req, group_folder_slug=group_folder_slug)
        self._index.upsert_text(record)
        return record

    def get_text(self, text_id: UUID) -> TextRecord:
        record = self._index.get_by_id(text_id)
        if record is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        return self._texts.load(Path(record.folder))

    def move_to_group(self, text_id: UUID, group: str) -> None:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        if indexed.group == group:
            return
        lang = indexed.target_language
        group_folder_slug = self._groups.register(lang, group)
        record = self._texts.move_folder(
            Path(indexed.folder),
            target_language=lang,
            group_folder_slug=group_folder_slug,
            group_display=group,
        )
        self._index.upsert_text(record)

    def write_native_variant(self, text_id: UUID, markdown: str) -> None:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        folder = Path(indexed.folder)
        self._texts.write_variant_markdown(folder, "native", markdown)
        record = self._texts.load(folder)
        self._index.upsert_text(record)

    def apply_translated_variant(
        self, text_id: UUID, translated_markdown: str
    ) -> TextRecord:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        folder = Path(indexed.folder)
        record = self._texts.apply_translated_variant(folder, translated_markdown)
        self._index.upsert_text(record)
        return record

    def read_native_variant(self, text_id: UUID) -> str:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        return self._texts.read_variant_markdown(Path(indexed.folder), "native")

    def delete_to_trash(self, text_id: UUID) -> None:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        self._texts.move_to_trash(Path(indexed.folder), text_id)
        self._index.remove_from_index(text_id)

    def list_groups(self, lang: str) -> list[str]:
        return self._groups.list_display_names(lang)

    def create_group(self, lang: str, name: str) -> None:
        self._groups.register(lang, name)

    def rename_group(self, lang: str, old: str, new: str) -> None:
        old_slug, new_slug = self._groups.rename_registry(lang, old, new)
        self._groups.rename_folder(lang, old_slug, new_slug)
        for text_folder in self._groups.text_folders(lang, new_slug):
            record = self._texts.update_group_label_in_folder(
                text_folder,
                group_display=new,
                group_folder_slug=new_slug,
            )
            self._index.upsert_text(record)

    def delete_if_empty(self, lang: str, name: str) -> None:
        registry = self._groups.registry(lang)
        try:
            folder_slug = registry.folder_slug_for_display(name)
        except GroupNotFoundError:
            return
        if self._groups.text_folders(lang, folder_slug):
            raise GroupNotEmptyError(f"group is not empty: {name!r}")
        self._groups.remove_folder(lang, folder_slug)
        self._groups.remove_registry_entry(lang, folder_slug)


_coordinators: weakref.WeakValueDictionary[int, LibraryCoordinator] = (
    weakref.WeakValueDictionary()
)


def coordinator_for(data_root: Path, index: LibraryIndex) -> LibraryCoordinator:
    """Return a shared coordinator for a data root and index pair."""
    key = id(index)
    existing = _coordinators.get(key)
    if existing is not None:
        return existing
    created = LibraryCoordinator(data_root, index)
    _coordinators[key] = created
    return created
