"""Orchestrates library storage, groups, and index synchronization."""

from __future__ import annotations

import weakref
from dataclasses import replace
from pathlib import Path
from uuid import UUID

from lexiflow_core.config.app_layout import ensure_app_layout
from lexiflow_core.config.paths import trash_dir
from lexiflow_core.library.group_registry import GroupNotFoundError
from lexiflow_core.library.group_storage import GroupStorage
from lexiflow_core.library.index import LibraryIndex, ensure_library_index
from lexiflow_core.library.models import CreateTextRequest, TextRecord
from lexiflow_core.library.text_storage import TextStorage
from lexiflow_core.library.trash import TrashItem


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
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        loaded = self._texts.load(Path(indexed.folder))
        return replace(loaded, last_viewed_tab=indexed.last_viewed_tab)

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

    def apply_simplified_variant(
        self,
        text_id: UUID,
        *,
        level: str,
        markdown: str,
    ) -> TextRecord:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        folder = Path(indexed.folder)
        record = self._texts.apply_simplified_variant(
            folder,
            level=level,
            markdown=markdown,
        )
        self._index.upsert_text(record)
        return replace(record, last_viewed_tab=indexed.last_viewed_tab)

    def read_native_variant(self, text_id: UUID) -> str:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        return self._texts.read_variant_markdown(Path(indexed.folder), "native")

    def read_variant(self, text_id: UUID, variant_name: str) -> str:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        return self._texts.read_variant_markdown(Path(indexed.folder), variant_name)

    def save_variant_edit(
        self,
        text_id: UUID,
        variant_name: str,
        markdown: str,
        *,
        library_title: str | None = None,
        source_url: str | None = None,
        update_source_url: bool = False,
    ) -> TextRecord:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            raise TextNotFoundError(f"text not found: {text_id}")
        folder = Path(indexed.folder)
        record = self._texts.save_user_variant_edit(
            folder,
            variant_name,
            markdown,
            library_title=library_title,
            source_url=source_url,
            update_source_url=update_source_url,
        )
        self._index.upsert_text(record)
        return replace(record, last_viewed_tab=indexed.last_viewed_tab)

    def delete_to_trash(self, text_id: UUID) -> None:
        indexed = self._index.get_by_id(text_id)
        if indexed is None:
            return
        folder = Path(indexed.folder)
        trash_path = trash_dir(self._data_root) / str(text_id)
        if folder.is_dir():
            self._texts.move_to_trash(folder, text_id)
        elif not trash_path.is_dir():
            raise TextNotFoundError(f"text not found: {text_id}")
        self._index.remove_from_index(text_id)

    def list_trash(self, *, language_code: str | None = None) -> list[TrashItem]:
        from lexiflow_core.library.trash import list_trash

        return list_trash(self._data_root, language_code=language_code)

    def restore_from_trash(self, text_id: UUID) -> None:
        from lexiflow_core.library.trash import restore_from_trash

        restore_from_trash(self._data_root, self._index, text_id)

    def empty_trash(self, *, language_code: str | None = None) -> int:
        from lexiflow_core.library.trash import empty_trash, list_trash

        items = list_trash(self._data_root, language_code=language_code)
        removed = empty_trash(self._data_root, language_code=language_code)
        for item in items:
            self._index.remove_from_index(item.text_id)
        return removed

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
