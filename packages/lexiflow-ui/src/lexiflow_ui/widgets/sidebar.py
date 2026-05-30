"""Primary navigation sidebar for Texts mode."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget


class SidebarWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._add_text = QPushButton("Add text", self)
        self._add_text.setObjectName("sidebar_add_text_button")
        self._add_text.setMinimumHeight(32)
        layout.addWidget(self._add_text)

        self._empty_label = QLabel("No texts yet", self)
        self._empty_label.setObjectName("sidebar_empty_label")
        self._list = QListWidget(self)
        self._list.setObjectName("sidebar_text_list")
        self._list.hide()
        layout.addWidget(self._empty_label)
        layout.addWidget(self._list, stretch=1)

    def add_text_button(self) -> QPushButton:
        return self._add_text

    def set_titles(self, titles: list[str]) -> None:
        """Show indexed text titles or the empty state."""
        self._list.clear()
        if not titles:
            self._empty_label.show()
            self._list.hide()
            return
        self._empty_label.hide()
        self._list.show()
        for title in titles:
            self._list.addItem(title)
