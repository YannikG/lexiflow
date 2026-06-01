"""UI orchestration for deleting texts to trash."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.library.text_repository import TextRepository
from PySide6.QtWidgets import QMessageBox, QWidget


def confirm_delete_text(parent: QWidget | None, *, title: str) -> bool:
    """Ask the user to confirm moving a text to trash."""
    answer = QMessageBox.question(
        parent,
        "Delete text",
        f'Move "{title}" to trash? You can restore it later from settings.',
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return answer == QMessageBox.StandardButton.Yes


def delete_text_to_trash(repo: TextRepository, text_id: UUID) -> None:
    """Move a text to trash and remove it from the library index."""
    repo.delete_to_trash(text_id)
