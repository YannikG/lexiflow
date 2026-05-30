"""Markdown reader with tabs, read mode, and edit mode."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.models import TextRecord
from lexiflow_core.library.reader_tabs import (
    NATIVE_TAB,
    TRANSLATED_TAB,
    discover_simplified_variants,
    simplified_tab_label,
)
from lexiflow_core.library.text_repository import TextRepository
from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.reader_flow import load_variant_markdown, markdown_for_reader_pane


class ReaderWidget(QWidget):
    tab_changed = Signal(str)
    text_saved = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reader_widget")
        self._record: TextRecord | None = None
        self._repo: TextRepository | None = None
        self._index: LibraryIndex | None = None
        self._settings: Settings | None = None
        self._active_tab = TRANSLATED_TAB
        self._simplified_variants: tuple[str, ...] = ()
        self._loaded_markdown: str | None = None
        self._tab_buttons: dict[str, QPushButton | QToolButton] = {}
        self._single_simplified_variant: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        header = QHBoxLayout()
        self._title = QLabel(self)
        self._title.setObjectName("reader_document_title")
        header.addWidget(self._title, stretch=1)
        self._source_button = QPushButton("Open source", self)
        self._source_button.setObjectName("reader_source_button")
        self._source_button.clicked.connect(self._open_source_url)
        self._source_button.hide()
        header.addWidget(self._source_button)
        root.addLayout(header)

        tab_row = QHBoxLayout()
        tab_row.setSpacing(4)
        self._native_tab = self._make_tab_button(
            "Native", NATIVE_TAB, "reader_tab_native"
        )
        self._translated_tab = self._make_tab_button(
            "Translated", TRANSLATED_TAB, "reader_tab_translated"
        )
        tab_row.addWidget(self._native_tab)
        tab_row.addWidget(self._translated_tab)
        self._simplified_tab = self._make_tab_button(
            "Simplified", "", "reader_tab_simplified"
        )
        self._simplified_tab.hide()
        tab_row.addWidget(self._simplified_tab)
        self._simplified_menu = QToolButton(self)
        self._simplified_menu.setObjectName("reader_simplified_menu")
        self._simplified_menu.setText("Simplified")
        self._simplified_menu.setCheckable(True)
        self._simplified_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._simplified_menu.hide()
        tab_row.addWidget(self._simplified_menu)
        tab_row.addStretch(1)
        root.addLayout(tab_row)

        controls = QHBoxLayout()
        self._edit_button = QPushButton("Edit", self)
        self._edit_button.setObjectName("reader_edit_button")
        self._edit_button.clicked.connect(self._enter_edit_mode)
        self._save_button = QPushButton("Save", self)
        self._save_button.setObjectName("reader_save_button")
        self._save_button.clicked.connect(self._save_edit)
        self._save_button.hide()
        self._cancel_button = QPushButton("Cancel", self)
        self._cancel_button.setObjectName("reader_cancel_button")
        self._cancel_button.clicked.connect(self._cancel_edit)
        self._cancel_button.hide()
        controls.addWidget(self._edit_button)
        controls.addWidget(self._save_button)
        controls.addWidget(self._cancel_button)
        controls.addStretch(1)
        root.addLayout(controls)

        self._mode_stack = QStackedWidget(self)
        self._mode_stack.setObjectName("reader_mode_stack")
        self._read_pane = QTextBrowser(self)
        self._read_pane.setObjectName("reader_read_pane")
        self._read_pane.setOpenExternalLinks(True)
        self._edit_pane = QPlainTextEdit(self)
        self._edit_pane.setObjectName("reader_edit_pane")
        self._mode_stack.addWidget(self._read_pane)
        self._mode_stack.addWidget(self._edit_pane)
        root.addWidget(self._mode_stack, stretch=1)

        self._native_tab.clicked.connect(lambda: self.select_tab(NATIVE_TAB))
        self._translated_tab.clicked.connect(lambda: self.select_tab(TRANSLATED_TAB))
        self._simplified_tab.clicked.connect(self._select_single_simplified_tab)

    @property
    def active_tab_id(self) -> str:
        return self._active_tab

    def open_text(
        self,
        *,
        record: TextRecord,
        repo: TextRepository,
        index: LibraryIndex,
        settings: Settings,
        initial_tab: str,
    ) -> None:
        """Load a text and show the requested tab."""
        self._record = record
        self._repo = repo
        self._index = index
        self._settings = settings
        self._simplified_variants = discover_simplified_variants(Path(record.folder))
        self._configure_simplified_tabs()
        self._title.setText(record.title)
        if record.source_url:
            self._source_button.show()
        else:
            self._source_button.hide()
        self._apply_reader_font()
        self._show_read_mode()
        self.select_tab(initial_tab)

    def select_tab(self, tab_id: str) -> None:
        """Switch reader tab and refresh content."""
        if self._record is None or self._repo is None:
            return
        self._active_tab = tab_id
        self._update_tab_buttons()
        self._show_read_mode()
        markdown, title = load_variant_markdown(self._repo, self._record, tab_id)
        if markdown is None:
            self._loaded_markdown = None
            self._read_pane.setPlainText(
                "This variant is not available yet. "
                "Background jobs may still be running."
            )
            self._edit_button.setEnabled(False)
            self.tab_changed.emit(tab_id)
            return
        self._loaded_markdown = markdown
        self._edit_button.setEnabled(True)
        display_title = title if title is not None else self._record.title
        rendered = markdown_for_reader_pane(
            markdown,
            document_title=display_title,
        )
        self._read_pane.setMarkdown(rendered)
        self.tab_changed.emit(tab_id)

    def simplified_menu(self) -> QToolButton:
        return self._simplified_menu

    def _make_tab_button(
        self, label: str, tab_id: str, object_name: str
    ) -> QPushButton:
        button = QPushButton(label, self)
        button.setObjectName(object_name)
        button.setCheckable(True)
        if tab_id:
            self._tab_buttons[tab_id] = button
        return button

    def _select_single_simplified_tab(self) -> None:
        if self._single_simplified_variant is not None:
            self.select_tab(self._single_simplified_variant)

    def _configure_simplified_tabs(self) -> None:
        self._simplified_tab.hide()
        self._simplified_menu.hide()
        self._simplified_menu.setMenu(None)
        self._single_simplified_variant = None
        for variant in self._simplified_variants:
            self._tab_buttons.pop(variant, None)

        if not self._simplified_variants:
            return

        if len(self._simplified_variants) == 1:
            variant = self._simplified_variants[0]
            label = simplified_tab_label(variant)
            self._single_simplified_variant = variant
            self._simplified_tab.setText(f"Simplified ({label})")
            self._simplified_tab.show()
            self._tab_buttons[variant] = self._simplified_tab
            return

        menu = QMenu(self)
        for variant in self._simplified_variants:
            label = simplified_tab_label(variant)
            action = menu.addAction(label)
            action.triggered.connect(
                lambda _checked=False, tab=variant: self.select_tab(tab)
            )
            self._tab_buttons[variant] = self._simplified_menu
        self._simplified_menu.setMenu(menu)
        self._simplified_menu.show()

    def _update_tab_buttons(self) -> None:
        for tab_id, button in self._tab_buttons.items():
            if button is self._simplified_menu:
                continue
            button.setChecked(tab_id == self._active_tab)
        if self._simplified_menu.isVisible():
            self._simplified_menu.setChecked(
                self._active_tab in self._simplified_variants
            )

    def _apply_reader_font(self) -> None:
        if self._settings is None:
            return
        font = QFont(self._read_pane.font())
        font.setPointSize(self._settings.reader_font_size)
        self._read_pane.setFont(font)
        self._edit_pane.setFont(font)

    def _show_read_mode(self) -> None:
        self._mode_stack.setCurrentWidget(self._read_pane)
        self._edit_button.show()
        self._save_button.hide()
        self._cancel_button.hide()

    def _enter_edit_mode(self) -> None:
        if self._loaded_markdown is None:
            return
        self._edit_pane.setPlainText(self._loaded_markdown)
        self._mode_stack.setCurrentWidget(self._edit_pane)
        self._edit_button.hide()
        self._save_button.show()
        self._cancel_button.show()

    def _cancel_edit(self) -> None:
        self._show_read_mode()
        self.select_tab(self._active_tab)

    def _save_edit(self) -> None:
        if self._record is None or self._repo is None:
            return
        markdown = self._edit_pane.toPlainText()
        updated = self._repo.save_variant_edit(
            self._record.id,
            self._active_tab,
            markdown,
        )
        self._record = updated
        self._title.setText(updated.title)
        self._show_read_mode()
        self.select_tab(self._active_tab)
        self.text_saved.emit()

    def _open_source_url(self) -> None:
        if self._record is None or not self._record.source_url:
            return
        QDesktopServices.openUrl(QUrl(self._record.source_url))
