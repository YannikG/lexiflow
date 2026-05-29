"""Public facade for group library operations."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import (
    GroupNotEmptyError,
    coordinator_for,
)

__all__ = ["GroupNotEmptyError", "GroupRepository"]


class GroupRepository:
    def __init__(self, data_root: Path, index: LibraryIndex) -> None:
        self._coordinator = coordinator_for(data_root, index)

    def list_groups(self, lang: str) -> list[str]:
        return self._coordinator.list_groups(lang)

    def create_group(self, lang: str, name: str) -> None:
        self._coordinator.create_group(lang, name)

    def rename_group(self, lang: str, old: str, new: str) -> None:
        self._coordinator.rename_group(lang, old, new)

    def delete_if_empty(self, lang: str, name: str) -> None:
        self._coordinator.delete_if_empty(lang, name)
