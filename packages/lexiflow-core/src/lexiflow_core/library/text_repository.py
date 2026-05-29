"""Public facade for text library operations."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import (
    TextNotFoundError,
    coordinator_for,
)
from lexiflow_core.library.models import CreateTextRequest, TextRecord

__all__ = ["TextNotFoundError", "TextRepository"]


class TextRepository:
    def __init__(self, data_root: Path, index: LibraryIndex) -> None:
        self._coordinator = coordinator_for(data_root, index)

    def create_text(self, req: CreateTextRequest) -> TextRecord:
        return self._coordinator.create_text(req)

    def get_text(self, text_id: UUID) -> TextRecord:
        return self._coordinator.get_text(text_id)

    def move_to_group(self, text_id: UUID, group: str) -> None:
        self._coordinator.move_to_group(text_id, group)

    def delete_to_trash(self, text_id: UUID) -> None:
        self._coordinator.delete_to_trash(text_id)
