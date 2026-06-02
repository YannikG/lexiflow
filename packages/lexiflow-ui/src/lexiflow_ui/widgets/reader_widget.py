"""Markdown reader with tabs, read mode, and edit mode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.jobs.embed_queue import (
    enqueue_translated_text_embed,
    enqueue_vocabulary_word_embed,
)
from lexiflow_core.jobs.service import JobService
from lexiflow_core.jobs.text_job_status import pending_simplified_variants
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.document_title import (
    DocumentTitleError,
    normalize_document_title,
)
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.models import TextRecord
from lexiflow_core.library.reader_tabs import (
    NATIVE_TAB,
    SIMPLIFIED_PREFIX,
    TRANSLATED_TAB,
    discover_simplified_variants,
    level_from_simplified_variant,
    simplified_tab_label,
    simplified_variant_name,
)
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.simplify.new_words import (
    learned_vocabulary_for_variant,
    visible_stored_suggestions,
)
from lexiflow_core.simplify.suggestions_store import load_suggestions
from lexiflow_core.vocabulary.models import NewWordSuggestion, VocabularyEntry
from lexiflow_core.vocabulary.store import VocabularyStore, VocabularyStoreError
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.add_word_flow import prompt_edit_word
from lexiflow_ui.delete_text_flow import confirm_delete_text, delete_text_to_trash
from lexiflow_ui.generation_status import generation_indicator
from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.reader_add_word import can_add_word_from_tab, open_highlight_add_dialog
from lexiflow_ui.reader_flow import markdown_for_reader_pane, variant_reader_state
from lexiflow_ui.simplify_flow import (
    confirm_simplify_without_translated,
    default_simplify_level,
    submit_simplify,
)
from lexiflow_ui.unsaved_changes import (
    confirm_leave_dirty_editor,
    fields_differ_from_snapshot,
)
from lexiflow_ui.widgets.vocabulary_delete_undo_banner import VocabularyDeleteUndoBanner
from lexiflow_ui.widgets.word_panel import WordPanel
from lexiflow_ui.worker_supervisor import WorkerSupervisor


@dataclass(frozen=True)
class _EditSnapshot:
    title: str
    source_url: str
    markdown: str


class ReaderWidget(QWidget):
    tab_changed = Signal(str)
    text_saved = Signal()
    text_deleted = Signal()
    simplify_submitted = Signal()
    vocabulary_changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        data_root: Path | None = None,
        supervisor: WorkerSupervisor | None = None,
        llama_supervisor: LlamaServerSupervisor | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("reader_widget")
        self._data_root = data_root
        self._supervisor = supervisor
        self._llama_supervisor = llama_supervisor
        self._record: TextRecord | None = None
        self._repo: TextRepository | None = None
        self._index: LibraryIndex | None = None
        self._settings: Settings | None = None
        self._active_tab = TRANSLATED_TAB
        self._simplified_variants: tuple[str, ...] = ()
        self._loaded_markdown: str | None = None
        self._tab_buttons: dict[str, QPushButton | QToolButton] = {}
        self._single_simplified_variant: str | None = None
        self._edit_snapshot: _EditSnapshot | None = None
        self._tab_button_group = QButtonGroup(self)
        self._tab_button_group.setExclusive(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        header = QVBoxLayout()
        title_row = QHBoxLayout()
        self._library_title = QLabel(self)
        self._library_title.setObjectName("reader_library_title")
        self._title_edit = QLineEdit(self)
        self._title_edit.setObjectName("reader_title_edit")
        self._title_edit.setPlaceholderText("Title")
        self._title_edit.hide()
        title_row.addWidget(self._library_title, stretch=1)
        title_row.addWidget(self._title_edit, stretch=1)
        self._source_button = QPushButton("Open source", self)
        self._source_button.setObjectName("reader_source_button")
        self._source_button.clicked.connect(self._open_source_url)
        self._source_button.hide()
        title_row.addWidget(self._source_button)
        header.addLayout(title_row)
        self._source_url_edit = QLineEdit(self)
        self._source_url_edit.setObjectName("reader_source_url_edit")
        self._source_url_edit.setPlaceholderText("Source URL (optional)")
        self._source_url_edit.hide()
        header.addWidget(self._source_url_edit)
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
        self._register_tab_button(self._simplified_menu)
        self._simplified_menu.hide()
        tab_row.addWidget(self._simplified_menu)
        self._simplify_level = QComboBox(self)
        self._simplify_level.setObjectName("reader_simplify_level")
        for level in CEFRLevel:
            self._simplify_level.addItem(level.value, level)
        self._simplify_button = QPushButton("Simplify", self)
        self._simplify_button.setObjectName("reader_simplify_button")
        self._simplify_button.clicked.connect(self._run_simplify)
        tab_row.addWidget(self._simplify_level)
        tab_row.addWidget(self._simplify_button)
        tab_row.addStretch(1)
        root.addLayout(tab_row)

        self._mode_stack = QStackedWidget(self)
        self._mode_stack.setObjectName("reader_mode_stack")
        self._read_pane = QTextBrowser(self)
        self._read_pane.setObjectName("reader_read_pane")
        self._read_pane.setOpenExternalLinks(True)
        self._read_pane.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._read_pane.customContextMenuRequested.connect(self._show_read_context_menu)
        self._edit_pane = QPlainTextEdit(self)
        self._edit_pane.setObjectName("reader_edit_pane")
        self._preview_pane = QTextBrowser(self)
        self._preview_pane.setObjectName("reader_edit_preview_pane")
        self._preview_pane.setOpenExternalLinks(True)
        self._edit_pane.textChanged.connect(self._update_edit_preview)

        read_page = QWidget(self)
        read_layout = QVBoxLayout(read_page)
        read_layout.setContentsMargins(0, 0, 0, 0)
        self._generation_banner = QWidget(read_page)
        self._generation_banner.setObjectName("reader_generation_banner")
        banner_layout = QVBoxLayout(self._generation_banner)
        banner_layout.setContentsMargins(0, 0, 0, 8)
        self._generation_headline = QLabel(self._generation_banner)
        self._generation_headline.setObjectName("reader_generation_headline")
        self._generation_headline.setWordWrap(True)
        self._generation_progress = QProgressBar(self._generation_banner)
        self._generation_progress.setObjectName("reader_generation_progress")
        self._generation_progress.setTextVisible(False)
        self._generation_progress.setRange(0, 0)
        banner_layout.addWidget(self._generation_headline)
        banner_layout.addWidget(self._generation_progress)
        self._generation_banner.hide()
        read_layout.addWidget(self._generation_banner)
        read_layout.addWidget(self._read_pane, stretch=1)
        self._delete_undo_banner = VocabularyDeleteUndoBanner(
            data_root=self._data_root,
            language_code=self._reader_language_code,
            supervisor=self._supervisor,
            parent=read_page,
        )
        self._delete_undo_banner.restored.connect(self._on_vocabulary_delete_restored)
        read_layout.addWidget(self._delete_undo_banner)
        self._word_panel = WordPanel(read_page)
        self._word_panel.add_requested.connect(self._add_new_word)
        self._word_panel.edit_requested.connect(self._edit_learned_word)
        self._word_panel.delete_requested.connect(self._delete_learned_word)
        read_layout.addWidget(self._word_panel, stretch=0)

        edit_page = QWidget(self)
        edit_layout = QVBoxLayout(edit_page)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_splitter = QSplitter(Qt.Orientation.Horizontal, edit_page)
        edit_splitter.setObjectName("reader_edit_splitter")
        edit_splitter.addWidget(self._edit_pane)
        edit_splitter.addWidget(self._preview_pane)
        edit_splitter.setStretchFactor(0, 1)
        edit_splitter.setStretchFactor(1, 1)
        edit_layout.addWidget(edit_splitter)

        self._mode_stack.addWidget(read_page)
        self._mode_stack.addWidget(edit_page)
        root.addWidget(self._mode_stack, stretch=1)

        controls = QHBoxLayout()
        controls.setObjectName("reader_controls")
        controls.addStretch(1)
        self._edit_button = QPushButton("Edit", self)
        self._edit_button.setObjectName("reader_edit_button")
        self._edit_button.clicked.connect(self._enter_edit_mode)
        self._delete_button = QPushButton("Delete", self)
        self._delete_button.setObjectName("reader_delete_button")
        self._delete_button.clicked.connect(self._delete_text)
        self._save_button = QPushButton("Save", self)
        self._save_button.setObjectName("reader_save_button")
        self._save_button.clicked.connect(self._save_edit)
        self._save_button.hide()
        self._cancel_button = QPushButton("Cancel", self)
        self._cancel_button.setObjectName("reader_cancel_button")
        self._cancel_button.clicked.connect(self._cancel_edit)
        self._cancel_button.hide()
        controls.addWidget(self._edit_button)
        controls.addWidget(self._delete_button)
        controls.addWidget(self._save_button)
        controls.addWidget(self._cancel_button)
        root.addLayout(controls)

        self._native_tab.clicked.connect(lambda: self.request_select_tab(NATIVE_TAB))
        self._translated_tab.clicked.connect(
            lambda: self.request_select_tab(TRANSLATED_TAB)
        )
        self._simplified_tab.clicked.connect(self._select_single_simplified_tab)

    @property
    def active_tab_id(self) -> str:
        return self._active_tab

    def is_editing(self) -> bool:
        return self._mode_stack.currentIndex() == 1

    def has_unsaved_edits(self) -> bool:
        if not self.is_editing() or self._edit_snapshot is None:
            return False
        return fields_differ_from_snapshot(
            title=(self._title_edit.text(), self._edit_snapshot.title),
            source_url=(self._source_url_edit.text(), self._edit_snapshot.source_url),
            markdown=(self._edit_pane.toPlainText(), self._edit_snapshot.markdown),
        )

    def leave_edit_mode_without_save(self) -> None:
        self._show_read_mode()

    def confirm_leave_edit_mode(self, parent: QWidget | None = None) -> bool:
        """Return True when navigation may proceed away from edit mode."""
        return confirm_leave_dirty_editor(parent, self)

    def open_text(
        self,
        *,
        record: TextRecord,
        repo: TextRepository,
        index: LibraryIndex,
        settings: Settings,
        initial_tab: str,
    ) -> bool:
        """Load a text and show the requested tab."""
        if not self.confirm_leave_edit_mode(self):
            return False
        self._record = record
        self._repo = repo
        self._index = index
        self._settings = settings
        self._refresh_simplified_variants()
        self._configure_simplified_tabs()
        self._library_title.setText(record.title)
        self._configure_simplify_level(record.target_language)
        self._update_source_url_controls()
        self._apply_reader_font()
        self._show_read_mode()
        self.select_tab(initial_tab)
        return True

    def request_select_tab(self, tab_id: str) -> None:
        """Switch tabs from user input; prompts when edits are unsaved."""
        if tab_id == self._active_tab and self.is_editing():
            return
        if not self.confirm_leave_edit_mode(self):
            self._update_tab_buttons()
            return
        self.select_tab(tab_id)

    def select_tab(self, tab_id: str) -> None:
        """Switch reader tab and refresh content."""
        if self._record is None or self._repo is None:
            return
        self._active_tab = tab_id
        self._update_tab_buttons()
        self._show_read_mode()
        markdown, status_message, edit_enabled = variant_reader_state(
            self._repo,
            self._record,
            tab_id,
            data_root=self._data_root,
        )
        if markdown is None:
            self._loaded_markdown = None
            message = status_message or "This variant is not available yet."
            self._show_status_overlay(message)
            self._edit_button.setEnabled(False)
            self._refresh_word_panel()
            self.tab_changed.emit(tab_id)
            return
        self._hide_generation_banner()
        self._loaded_markdown = markdown
        self._edit_button.setEnabled(edit_enabled)
        rendered = markdown_for_reader_pane(markdown, document_title=None)
        self._read_pane.setMarkdown(rendered)
        self._sync_simplify_level_picker()
        self._refresh_word_panel()
        self.tab_changed.emit(tab_id)

    def scroll_to_match(self, query: str) -> None:
        """Scroll the read pane to the first occurrence of *query* when possible."""
        trimmed = query.strip()
        if not trimmed:
            return
        self._read_pane.find(trimmed)

    def reload_from_disk(
        self, *, focus_simplified_level: CEFRLevel | None = None
    ) -> None:
        """Refresh simplified tabs and active content after background jobs."""
        if self._record is None or self._repo is None or self._index is None:
            return
        self._record = self._repo.get_text(self._record.id)
        self._refresh_simplified_variants()
        self._configure_simplified_tabs()
        self._library_title.setText(self._record.title)
        if focus_simplified_level is not None:
            variant = simplified_variant_name(focus_simplified_level)
            if variant in self._simplified_variants:
                self.select_tab(variant)
                return
        self.select_tab(self._active_tab)

    def refresh_word_panel(self) -> None:
        """Refresh new/learned word tables for the active simplified tab."""
        self._refresh_word_panel()

    def refresh_infrastructure_status(self) -> None:
        """Refresh pending overlays when llama-server or worker state changes."""
        if self._record is None or self._loaded_markdown is not None:
            self._hide_generation_banner()
            return
        self.select_tab(self._active_tab)

    def _show_status_overlay(self, message: str) -> None:
        indicator = generation_indicator(
            llama_supervisor=self._llama_supervisor,
            worker_supervisor=self._supervisor,
            pending_message=message,
            variant_name=self._active_tab,
        )
        if indicator is not None:
            self._generation_headline.setText(indicator.headline)
            if indicator.show_progress:
                self._generation_progress.setRange(0, 0)
                self._generation_progress.show()
            else:
                self._generation_progress.hide()
            self._generation_banner.show()
            self._read_pane.setPlainText(indicator.detail)
            return
        self._hide_generation_banner()
        self._read_pane.setPlainText(message)

    def _hide_generation_banner(self) -> None:
        self._generation_banner.hide()
        self._generation_progress.hide()

    def simplified_menu(self) -> QToolButton:
        return self._simplified_menu

    def _register_tab_button(self, button: QAbstractButton) -> None:
        button.setCheckable(True)
        if button not in self._tab_button_group.buttons():
            self._tab_button_group.addButton(button)

    def _make_tab_button(
        self, label: str, tab_id: str, object_name: str
    ) -> QPushButton:
        button = QPushButton(label, self)
        button.setObjectName(object_name)
        self._register_tab_button(button)
        if tab_id:
            self._tab_buttons[tab_id] = button
        return button

    def _select_single_simplified_tab(self) -> None:
        if self._single_simplified_variant is not None:
            self.request_select_tab(self._single_simplified_variant)

    def _refresh_simplified_variants(self) -> None:
        if self._record is None:
            self._simplified_variants = ()
            return
        on_disk = discover_simplified_variants(Path(self._record.folder))
        pending: tuple[str, ...] = ()
        if self._data_root is not None:
            jobs = JobService(self._data_root).list_jobs()
            pending = pending_simplified_variants(jobs, text_id=self._record.id)
        merged = tuple(on_disk) + tuple(pending)
        self._simplified_variants = tuple(dict.fromkeys(merged))

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
                lambda _checked=False, tab=variant: self.request_select_tab(tab)
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
        self._preview_pane.setFont(font)

    def _update_source_url_controls(self) -> None:
        if self._record is None:
            self._source_button.hide()
            return
        if self._record.source_url:
            self._source_button.show()
        else:
            self._source_button.hide()

    def _show_read_mode(self) -> None:
        self._mode_stack.setCurrentIndex(0)
        self._edit_snapshot = None
        if self._record is not None:
            self._library_title.setText(self._record.title)
        self._library_title.show()
        self._title_edit.hide()
        self._source_url_edit.hide()
        self._update_source_url_controls()
        self._edit_button.show()
        self._delete_button.show()
        self._save_button.hide()
        self._cancel_button.hide()

    def _enter_edit_mode(self) -> None:
        if self._loaded_markdown is None or self._record is None:
            return
        title = self._record.title
        source_url = self._record.source_url or ""
        self._title_edit.setText(title)
        self._source_url_edit.setText(source_url)
        self._edit_snapshot = _EditSnapshot(
            title=title,
            source_url=source_url,
            markdown=self._loaded_markdown,
        )
        self._library_title.hide()
        self._title_edit.show()
        self._source_button.hide()
        self._source_url_edit.show()
        self._edit_pane.setPlainText(self._loaded_markdown)
        self._update_edit_preview()
        self._mode_stack.setCurrentIndex(1)
        self._edit_button.hide()
        self._delete_button.hide()
        self._save_button.show()
        self._cancel_button.show()

    def _update_edit_preview(self) -> None:
        if self._record is None:
            return
        markdown = self._edit_pane.toPlainText()
        rendered = markdown_for_reader_pane(markdown, document_title=None)
        self._preview_pane.setMarkdown(rendered)

    def _cancel_edit(self) -> None:
        self._show_read_mode()
        self.select_tab(self._active_tab)

    def _save_edit(self) -> None:
        if self._record is None or self._repo is None:
            return
        try:
            library_title = normalize_document_title(self._title_edit.text())
        except DocumentTitleError as error:
            QMessageBox.warning(self, "Invalid title", str(error))
            return
        markdown = self._edit_pane.toPlainText()
        source_url = self._source_url_edit.text().strip() or None
        updated = self._repo.save_variant_edit(
            self._record.id,
            self._active_tab,
            markdown,
            library_title=library_title,
            source_url=source_url,
            update_source_url=True,
        )
        if self._active_tab == TRANSLATED_TAB and self._data_root is not None:
            enqueue_translated_text_embed(
                JobService(self._data_root),
                self._record.id,
            )
            if self._supervisor is not None:
                self._supervisor.ensure_running()
        self._record = updated
        self._library_title.setText(updated.title)
        self._show_read_mode()
        self.select_tab(self._active_tab)
        self.text_saved.emit()

    def _open_source_url(self) -> None:
        if self._record is None or not self._record.source_url:
            return
        QDesktopServices.openUrl(QUrl(self._record.source_url))

    def _configure_simplify_level(self, target_language: str) -> None:
        if self._data_root is None:
            return
        if level_from_simplified_variant(self._active_tab) is not None:
            self._sync_simplify_level_picker()
            return
        level = default_simplify_level(self._data_root, target_language)
        index = self._simplify_level.findData(level)
        if index >= 0:
            self._simplify_level.setCurrentIndex(index)

    def _sync_simplify_level_picker(self) -> None:
        level = level_from_simplified_variant(self._active_tab)
        if level is None:
            return
        index = self._simplify_level.findData(level)
        if index >= 0:
            self._simplify_level.setCurrentIndex(index)

    def _selected_simplify_level(self) -> CEFRLevel:
        tab_level = level_from_simplified_variant(self._active_tab)
        if tab_level is not None:
            return tab_level
        level_value = self._simplify_level.currentData()
        if isinstance(level_value, CEFRLevel):
            return level_value
        return CEFRLevel(self._simplify_level.currentText())

    def _run_simplify(self) -> None:
        if (
            self._record is None
            or self._repo is None
            or self._data_root is None
            or self._supervisor is None
        ):
            return
        if not self.confirm_leave_edit_mode(self):
            return
        try:
            self._repo.read_variant(self._record.id, TRANSLATED_TAB)
        except FileNotFoundError:
            confirm_simplify_without_translated(self)
            return
        level = self._selected_simplify_level()
        submit_simplify(
            data_root=self._data_root,
            text_id=self._record.id,
            level=level,
        )
        variant = simplified_variant_name(level)
        self._refresh_simplified_variants()
        self._configure_simplified_tabs()
        self.select_tab(variant)
        self.simplify_submitted.emit()

    def _delete_text(self) -> None:
        if self._record is None or self._repo is None:
            return
        if not self.confirm_leave_edit_mode(self):
            return
        if not confirm_delete_text(self, title=self._record.title):
            return
        text_id = self._record.id
        delete_text_to_trash(self._repo, text_id)
        self._record = None
        self._repo = None
        self._index = None
        self._loaded_markdown = None
        self._show_read_mode()
        self.text_deleted.emit()

    def _refresh_word_panel(self) -> None:
        if self._record is None or not self._active_tab.startswith(SIMPLIFIED_PREFIX):
            self._word_panel.clear()
            return
        if self._data_root is None:
            self._word_panel.clear()
            return
        folder = Path(self._record.folder)
        stored = load_suggestions(
            folder,
            self._active_tab,
            language_code=self._record.target_language,
        )
        markdown = self._loaded_markdown or ""
        if not stored and not markdown.strip():
            self._word_panel.clear()
            return
        store = VocabularyStore(self._data_root, self._record.target_language)
        entries = store.list_for_simplify()
        existing = {entry.lemma for entry in entries}
        new_words = visible_stored_suggestions(stored, existing_lemmas=existing)
        learned_words = learned_vocabulary_for_variant(
            stored,
            entries,
            variant_markdown=markdown,
        )
        if not new_words and not learned_words:
            self._word_panel.clear()
            return
        self._word_panel.set_content(
            new_words=new_words,
            learned_words=learned_words,
        )

    def _show_read_context_menu(self, position: object) -> None:
        if self._record is None or not can_add_word_from_tab(self._active_tab):
            return
        from PySide6.QtCore import QPoint

        if not isinstance(position, QPoint):
            return
        menu = QMenu(self)
        add_action = menu.addAction("Add word")
        chosen = menu.exec(self._read_pane.mapToGlobal(position))
        if chosen is not add_action:
            return
        self.request_add_word_from_selection()

    def request_add_word_from_selection(self) -> bool:
        """Add the current reader selection to vocabulary."""
        return self._highlight_add_word()

    def _highlight_add_word(self) -> bool:
        if (
            self._record is None
            or self._data_root is None
            or self._settings is None
            or self._settings.native_language is None
        ):
            return False
        surface_form = (
            self._read_pane.textCursor().selectedText().replace("\u2029", " ").strip()
        )
        saved = open_highlight_add_dialog(
            self,
            data_root=self._data_root,
            record=self._record,
            tab_id=self._active_tab,
            surface_form=surface_form,
            native_language=self._settings.native_language,
            supervisor=self._supervisor,
        )
        if saved:
            self.vocabulary_changed.emit()
        return saved

    def _add_new_word(self, suggestion: NewWordSuggestion) -> None:
        if self._record is None or self._data_root is None or self._supervisor is None:
            return
        store = VocabularyStore(self._data_root, self._record.target_language)
        try:
            store.add_from_suggestion(suggestion)
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Add word", str(error))
            return
        enqueue_vocabulary_word_embed(
            JobService(self._data_root),
            language_code=self._record.target_language,
            lemma=suggestion.lemma,
        )
        self._supervisor.ensure_running()
        self._refresh_word_panel()
        self.vocabulary_changed.emit()

    def _edit_learned_word(self, entry: VocabularyEntry) -> None:
        if self._record is None or self._data_root is None:
            return
        form = prompt_edit_word(self, entry=entry)
        if form is None:
            return
        store = VocabularyStore(self._data_root, self._record.target_language)
        try:
            updated = store.update_entry(
                entry.lemma,
                new_lemma=form.lemma,
                translation=form.translation,
                explanation=form.explanation,
                level_when_learned=form.level_when_learned,
                word_category=form.word_category,
                difficulty_rating=form.difficulty_rating,
            )
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Edit word", str(error))
            return
        if updated.lemma != entry.lemma or updated.translation != entry.translation:
            enqueue_vocabulary_word_embed(
                JobService(self._data_root),
                language_code=self._record.target_language,
                lemma=updated.lemma,
            )
            if self._supervisor is not None:
                self._supervisor.ensure_running()
        self._refresh_word_panel()
        self.vocabulary_changed.emit()

    def _delete_learned_word(self, entry: VocabularyEntry) -> None:
        if self._record is None or self._data_root is None:
            return
        confirm = QMessageBox.question(
            self,
            "Delete word",
            f'Delete "{entry.lemma}" from vocabulary?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        store = VocabularyStore(self._data_root, self._record.target_language)
        try:
            snapshot = store.delete_entry(entry.lemma)
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Delete word", str(error))
            return
        self._delete_undo_banner.offer(snapshot)
        self._refresh_word_panel()
        self.vocabulary_changed.emit()

    def _reader_language_code(self) -> str | None:
        if self._record is None:
            return None
        return self._record.target_language

    def _on_vocabulary_delete_restored(self) -> None:
        self._refresh_word_panel()
        self.vocabulary_changed.emit()
