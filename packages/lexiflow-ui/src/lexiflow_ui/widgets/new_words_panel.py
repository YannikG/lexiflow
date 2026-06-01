"""New word suggestions panel below the simplified reader."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import NewWordSuggestion
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NewWordsPanel(QWidget):
    """List filtered new word suggestions with one-click add actions."""

    add_requested = Signal(NewWordSuggestion)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("new_words_panel")
        self._rows_layout = QVBoxLayout()
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(4)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        self._heading = QLabel("New words", self)
        self._heading.setObjectName("new_words_heading")
        root.addWidget(self._heading)
        root.addLayout(self._rows_layout)
        self.hide()

    def set_suggestions(self, suggestions: tuple[NewWordSuggestion, ...]) -> None:
        """Replace displayed suggestions."""
        self._clear_rows()
        if not suggestions:
            self.hide()
            return
        for suggestion in suggestions:
            row = QWidget(self)
            row.setObjectName("new_words_row")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            label = QLabel(
                (
                    f"{suggestion.lemma} — {suggestion.gloss} "
                    f"({suggestion.suggested_level.value})"
                ),
                row,
            )
            label.setObjectName("new_words_label")
            add_button = QPushButton("Add", row)
            add_button.setObjectName("new_words_add_button")
            add_button.clicked.connect(
                lambda _checked=False, item=suggestion: self.add_requested.emit(item)
            )
            layout.addWidget(label, stretch=1)
            layout.addWidget(add_button)
            self._rows_layout.addWidget(row)
        self.show()

    def _clear_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
