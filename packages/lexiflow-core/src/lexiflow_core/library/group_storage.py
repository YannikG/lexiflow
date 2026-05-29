"""Disk-only group folder and registry operations."""

from __future__ import annotations

import shutil
from pathlib import Path

from lexiflow_core.config.paths import group_dir
from lexiflow_core.library.group_registry import GroupRegistry


class GroupFolderExistsError(Exception):
    """Raised when a group folder path already exists on disk."""


class GroupStorage:
    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root

    def registry(self, lang: str) -> GroupRegistry:
        return GroupRegistry(self._data_root, lang)

    def list_display_names(self, lang: str) -> list[str]:
        return self.registry(lang).list_display_names()

    def register(self, lang: str, display_name: str) -> str:
        """Register a group and return its folder slug."""
        folder_slug = self.registry(lang).register(display_name)
        group_dir(self._data_root, lang, folder_slug).mkdir(parents=True, exist_ok=True)
        return folder_slug

    def rename_registry(
        self, lang: str, old_display: str, new_display: str
    ) -> tuple[str, str]:
        return self.registry(lang).rename(old_display, new_display)

    def rename_folder(self, lang: str, old_slug: str, new_slug: str) -> Path:
        """Rename a group folder on disk and return the new path."""
        old_path = group_dir(self._data_root, lang, old_slug)
        new_path = group_dir(self._data_root, lang, new_slug)
        if old_path.exists() and old_path != new_path:
            if new_path.exists():
                raise GroupFolderExistsError(
                    f"target group folder already exists: {new_path}"
                )
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_path), str(new_path))
        if not new_path.exists():
            new_path.mkdir(parents=True, exist_ok=True)
        return new_path

    def text_folders(self, lang: str, folder_slug: str) -> list[Path]:
        folder = group_dir(self._data_root, lang, folder_slug)
        if not folder.is_dir():
            return []
        return [entry for entry in folder.iterdir() if entry.is_dir()]

    def remove_registry_entry(self, lang: str, folder_slug: str) -> None:
        self.registry(lang).remove(folder_slug)

    def remove_folder(self, lang: str, folder_slug: str) -> None:
        folder = group_dir(self._data_root, lang, folder_slug)
        if folder.exists():
            shutil.rmtree(folder)
