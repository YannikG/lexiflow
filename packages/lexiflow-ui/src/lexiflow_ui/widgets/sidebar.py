"""Primary navigation sidebar for Texts mode."""

from __future__ import annotations

from uuid import UUID

from lexiflow_core.library.models import TextRecord
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SidebarWidget(QWidget):
    text_selected = Signal(UUID)

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
        self._list.itemClicked.connect(self._emit_selected_text)
        self._list.hide()
        layout.addWidget(self._empty_label)
        layout.addWidget(self._list, stretch=1)

    def add_text_button(self) -> QPushButton:
        return self._add_text

    def set_texts(self, records: list[TextRecord]) -> None:
        """Show indexed texts or the empty state."""
        self._list.clear()
        if not records:
            self._empty_label.show()
            self._list.hide()
            return
        self._empty_label.hide()
        self._list.show()
        for record in records:
            item = QListWidgetItem(record.title)
            item.setData(Qt.ItemDataRole.UserRole, str(record.id))
            self._list.addItem(item)

    def select_text(self, text_id: UUID) -> None:
        """Highlight a text in the sidebar list."""
        for row in range(self._list.count()):
            item = self._list.item(row)
            stored_id = item.data(Qt.ItemDataRole.UserRole)
            if stored_id == text_id or stored_id == str(text_id):
                self._list.setCurrentItem(item)
                return

    def _emit_selected_text(self, item: QListWidgetItem) -> None:
        text_id = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(text_id, str):
            try:
                self.text_selected.emit(UUID(text_id))
            except ValueError:
                pass
        elif isinstance(text_id, UUID):
            self.text_selected.emit(text_id)
