"""Placeholder view when a navigation mode has no content."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class EmptyStateWidget(QWidget):
    def __init__(
        self,
        *,
        title: str,
        message: str,
        action_text: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._heading = QLabel(title, self)
        self._heading.setObjectName("empty_state_title")
        heading_font = QFont(self._heading.font())
        heading_font.setPointSize(heading_font.pointSize() + 4)
        heading_font.setBold(True)
        self._heading.setFont(heading_font)
        self._heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._body = QLabel(message, self)
        self._body.setObjectName("empty_state_message")
        self._body.setWordWrap(True)
        self._body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._action: QPushButton | None = None
        layout.addWidget(self._heading)
        layout.addWidget(self._body)
        if action_text is not None:
            self._action = QPushButton(action_text, self)
            self._action.setObjectName("empty_state_action")
            layout.addWidget(self._action, alignment=Qt.AlignmentFlag.AlignCenter)

    def action_button(self) -> QPushButton | None:
        return self._action

    def set_content(
        self,
        *,
        title: str,
        message: str,
        show_action: bool,
    ) -> None:
        """Update the empty-state copy and whether the primary action is shown."""
        self._heading.setText(title)
        self._body.setText(message)
        if self._action is not None:
            self._action.setVisible(show_action)
