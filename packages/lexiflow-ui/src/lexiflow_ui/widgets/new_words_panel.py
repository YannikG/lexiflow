"""New word suggestions panel below the simplified reader."""

from __future__ import annotations

from lexiflow_core.vocabulary.models import NewWordSuggestion
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

NEW_WORDS_PANEL_MAX_HEIGHT = 140


class NewWordsPanel(QWidget):
    """List filtered new word suggestions with one-click add actions."""

    add_requested = Signal(NewWordSuggestion)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("new_words_panel")
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )
        self.setMaximumHeight(NEW_WORDS_PANEL_MAX_HEIGHT)

        self._rows_container = QWidget(self)
        self._rows_container.setObjectName("new_words_rows")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(4)
        self._rows_layout.addStretch(1)

        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("new_words_scroll")
        self._scroll.setWidget(self._rows_container)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(4)
        self._heading = QLabel("New words", self)
        self._heading.setObjectName("new_words_heading")
        root.addWidget(self._heading)
        root.addWidget(self._scroll, stretch=1)
        self.hide()

    def set_suggestions(self, suggestions: tuple[NewWordSuggestion, ...]) -> None:
        """Replace displayed suggestions."""
        self._clear_rows()
        if not suggestions:
            self.hide()
            return
        for suggestion in suggestions:
            row = QWidget(self._rows_container)
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
            label.setWordWrap(True)
            add_button = QPushButton("Add", row)
            add_button.setObjectName("new_words_add_button")
            add_button.clicked.connect(
                lambda _checked=False, item=suggestion: self.add_requested.emit(item)
            )
            layout.addWidget(label, stretch=1)
            layout.addWidget(add_button)
            self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)
        self.show()

    def _clear_rows(self) -> None:
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
