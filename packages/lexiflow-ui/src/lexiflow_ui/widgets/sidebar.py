"""Primary navigation sidebar for Texts mode."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SidebarWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        label = QLabel("No texts yet", self)
        label.setObjectName("sidebar_empty_label")
        layout.addWidget(label)
        layout.addStretch()
