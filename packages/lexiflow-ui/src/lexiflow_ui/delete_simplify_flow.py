"""Confirm and remove a simplified variant from the reader."""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def confirm_delete_simplification(parent: QWidget | None, *, level_label: str) -> bool:
    """Ask the user to confirm deleting a simplified level."""
    answer = QMessageBox.question(
        parent,
        "Delete simplification",
        (
            f"Delete the {level_label} simplification for this text? "
            "Vocabulary you already added from this level is kept."
        ),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return answer == QMessageBox.StandardButton.Yes
