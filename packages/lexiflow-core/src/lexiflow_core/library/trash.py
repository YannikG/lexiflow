"""Trash storage for deleted texts."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from lexiflow_core.config.paths import group_dir, meta_path, text_dir, trash_dir
from lexiflow_core.library.group_storage import GroupStorage
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.slug import TextSlugError, make_text_slug
from lexiflow_core.library.text_metadata import TextMetadataError, load_text_metadata
from lexiflow_core.library.text_storage import TextStorage


class TrashItemNotFoundError(Exception):
    """Raised when a trashed text id does not exist."""


class TrashRestoreError(Exception):
    """Raised when a trashed text cannot be restored to its library location."""


@dataclass(frozen=True)
class TrashItem:
    text_id: UUID
    title: str
    group: str
    target_language: str
    deleted_at: datetime | None = None


def list_trash(data_root: Path, *, language_code: str | None = None) -> list[TrashItem]:
    """Return metadata for texts currently in trash."""
    root = trash_dir(data_root)
    if not root.is_dir():
        return []
    items: list[TrashItem] = []
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        try:
            text_id = UUID(folder.name)
        except ValueError:
            continue
        meta_file = meta_path(folder)
        if not meta_file.is_file():
            continue
        try:
            metadata = load_text_metadata(meta_file)
        except TextMetadataError:
            continue
        if language_code is not None and metadata.target_language != language_code:
            continue
        deleted_at = datetime.fromtimestamp(folder.stat().st_mtime)
        items.append(
            TrashItem(
                text_id=text_id,
                title=metadata.title,
                group=metadata.group,
                target_language=metadata.target_language,
                deleted_at=deleted_at,
            )
        )
    items.sort(key=lambda item: (item.target_language, item.title.casefold()))
    return items


def trashed_text_ids(
    data_root: Path, *, language_code: str | None = None
) -> frozenset[UUID]:
    """Return ids for texts currently stored under the trash area."""
    root = trash_dir(data_root)
    if not root.is_dir():
        return frozenset()
    ids: set[UUID] = set()
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        meta_file = meta_path(folder)
        if meta_file.is_file():
            try:
                metadata = load_text_metadata(meta_file)
            except TextMetadataError:
                continue
            if language_code is not None and metadata.target_language != language_code:
                continue
            ids.add(metadata.id)
            try:
                ids.add(UUID(folder.name))
            except ValueError:
                pass
            continue
        if language_code is not None:
            continue
        try:
            ids.add(UUID(folder.name))
        except ValueError:
            pass
    return frozenset(ids)


def text_is_in_trash(data_root: Path, text_id: UUID) -> bool:
    """Return whether a text id currently has an entry under trash."""
    return text_id in trashed_text_ids(data_root)


def is_path_in_trash(path: Path, data_root: Path) -> bool:
    """Return whether a path is inside the library trash area."""
    try:
        path.resolve().relative_to(trash_dir(data_root).resolve())
    except ValueError:
        return False
    return True


def restore_from_trash(
    data_root: Path,
    index: LibraryIndex,
    text_id: UUID,
) -> None:
    """Move a trashed text back into the library and re-index it."""
    source = trash_dir(data_root) / str(text_id)
    if not source.is_dir():
        raise TrashItemNotFoundError(f"trashed text not found: {text_id}")
    metadata = load_text_metadata(meta_path(source))
    groups = GroupStorage(data_root)
    group_folder_slug = groups.register(metadata.target_language, metadata.group)
    text_slug = _allocate_restore_slug(
        data_root,
        metadata.target_language,
        group_folder_slug,
        metadata.title,
    )
    destination = text_dir(
        data_root,
        metadata.target_language,
        group_folder_slug,
        text_slug,
    )
    if destination.exists():
        raise TrashRestoreError(f"restore target already exists: {destination}")
    group_dir(data_root, metadata.target_language, group_folder_slug).mkdir(
        parents=True, exist_ok=True
    )
    shutil.move(str(source), str(destination))
    record = TextStorage(data_root).load(destination)
    index.upsert_text(record)


def empty_trash(data_root: Path, *, language_code: str | None = None) -> int:
    """Permanently delete trashed texts. Returns count removed."""
    root = trash_dir(data_root)
    if not root.is_dir():
        return 0
    count = 0
    for folder in list(root.iterdir()):
        if not folder.is_dir():
            continue
        try:
            UUID(folder.name)
        except ValueError:
            continue
        if language_code is not None:
            meta_file = meta_path(folder)
            if not meta_file.is_file():
                continue
            try:
                metadata = load_text_metadata(meta_file)
            except TextMetadataError:
                continue
            if metadata.target_language != language_code:
                continue
        shutil.rmtree(folder)
        count += 1
    return count


def _allocate_restore_slug(
    data_root: Path,
    language_code: str,
    group_folder_slug: str,
    title: str,
) -> str:
    for _ in range(20):
        candidate = make_text_slug(title)
        folder = text_dir(data_root, language_code, group_folder_slug, candidate)
        if not folder.exists():
            return candidate
    raise TextSlugError("could not allocate unique text slug for restore")
