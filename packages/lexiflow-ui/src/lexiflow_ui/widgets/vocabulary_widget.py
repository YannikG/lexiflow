"""Vocabulary browse mode for the active target language."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.jobs.embed_queue import enqueue_vocabulary_word_embed
from lexiflow_core.jobs.service import JobService
from lexiflow_core.vocabulary.export import export_vocabulary_zip
from lexiflow_core.vocabulary.import_bundle import (
    VocabularyImportError,
    import_vocabulary_zip,
)
from lexiflow_core.vocabulary.models import DifficultyRating, VocabularySort
from lexiflow_core.vocabulary.store import (
    DeletedVocabularyEntry,
    VocabularyStore,
    VocabularyStoreError,
)
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.add_word_flow import (
    default_level_for_language,
    prompt_add_word,
    prompt_edit_word,
)
from lexiflow_ui.dialogs.add_word_dialog import AddWordForm
from lexiflow_ui.widgets.empty_state import EmptyStateWidget
from lexiflow_ui.widgets.vocabulary_browse_table import VocabularyBrowseTable
from lexiflow_ui.worker_supervisor import WorkerSupervisor

DELETE_UNDO_WINDOW_MS = 8_000


class VocabularyWidget(QWidget):
    vocabulary_changed = Signal()

    def __init__(
        self,
        *,
        data_root: Path,
        settings: Settings,
        supervisor: WorkerSupervisor | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("vocabulary_widget")
        self._data_root = data_root
        self._settings = settings
        self._supervisor = supervisor
        self._delete_undo_snapshot: DeletedVocabularyEntry | None = None
        self._delete_undo_timer = QTimer(self)
        self._delete_undo_timer.setSingleShot(True)
        self._delete_undo_timer.timeout.connect(self._clear_delete_undo)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)

        toolbar = QHBoxLayout()

        self._search = QLineEdit(self)
        self._search.setObjectName("vocabulary_search")
        self._search.setPlaceholderText("Search vocabulary")
        self._search.textChanged.connect(self.refresh)
        toolbar.addWidget(self._search, stretch=1)

        self._sort = QComboBox(self)
        self._sort.setObjectName("vocabulary_sort")
        for sort in VocabularySort:
            self._sort.addItem(
                sort.value.replace("_", " ").title(),
                sort.value,
            )
        self._sort.currentIndexChanged.connect(lambda _index: self.refresh())
        toolbar.addWidget(self._sort)

        self._add_button = QPushButton("Add word", self)
        self._add_button.setObjectName("vocabulary_add_button")
        self._add_button.clicked.connect(self._manual_add_word)
        toolbar.addWidget(self._add_button)

        self._export_button = QPushButton("Export", self)
        self._export_button.setObjectName("vocabulary_export_button")
        self._export_button.clicked.connect(self._export_vocabulary)
        toolbar.addWidget(self._export_button)

        self._import_button = QPushButton("Import", self)
        self._import_button.setObjectName("vocabulary_import_button")
        self._import_button.clicked.connect(self._import_vocabulary)
        toolbar.addWidget(self._import_button)

        root.addLayout(toolbar)

        self._delete_undo_banner = QWidget(self)
        self._delete_undo_banner.setObjectName("vocabulary_delete_undo_banner")
        undo_layout = QHBoxLayout(self._delete_undo_banner)
        undo_layout.setContentsMargins(0, 0, 0, 0)
        self._delete_undo_label = QPushButton(
            "Word deleted.",
            self._delete_undo_banner,
        )
        self._delete_undo_label.setObjectName("vocabulary_delete_undo_label")
        self._delete_undo_label.setFlat(True)
        self._delete_undo_label.setEnabled(False)
        undo_layout.addWidget(self._delete_undo_label)
        self._delete_undo_button = QPushButton("Undo", self._delete_undo_banner)
        self._delete_undo_button.setObjectName("vocabulary_delete_undo_button")
        self._delete_undo_button.clicked.connect(self._undo_delete)
        undo_layout.addWidget(self._delete_undo_button)
        undo_layout.addStretch(1)
        self._delete_undo_banner.hide()
        root.addWidget(self._delete_undo_banner)

        self._stack = QStackedWidget(self)
        self._empty_state = EmptyStateWidget(
            title="No vocabulary yet",
            message="Words you save while reading will appear here.",
            parent=self._stack,
        )
        self._browse_table = VocabularyBrowseTable(self._stack)
        self._stack.addWidget(self._empty_state)
        self._stack.addWidget(self._browse_table)
        root.addWidget(self._stack, stretch=1)

        self._browse_table.edit_requested.connect(self._edit_entry)
        self._browse_table.delete_requested.connect(self._delete_entry)
        self._browse_table.difficulty_changed.connect(self._set_difficulty)

        self.refresh()

    def refresh(self) -> None:
        language = self._settings.active_target_language
        if language is None:
            self._stack.setCurrentWidget(self._empty_state)
            return
        store = VocabularyStore(self._data_root, language)
        entries = store.list_entries(sort=self._current_sort())
        query = self._search.text().strip().lower()
        if query:
            entries = tuple(
                entry
                for entry in entries
                if query in entry.lemma.lower()
                or query in entry.translation.lower()
                or query in entry.explanation.lower()
            )
        if not entries:
            self._stack.setCurrentWidget(self._empty_state)
            return
        self._stack.setCurrentWidget(self._browse_table)
        self._browse_table.set_entries(entries)

    def _current_sort(self) -> VocabularySort:
        value = self._sort.currentData()
        if isinstance(value, VocabularySort):
            return value
        if isinstance(value, str):
            try:
                return VocabularySort(value)
            except ValueError:
                pass
        return VocabularySort.RECENT

    def _set_difficulty(self, lemma: str, rating: DifficultyRating) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        store = VocabularyStore(self._data_root, language)
        try:
            store.set_difficulty(lemma, rating)
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Vocabulary", str(error))
            return
        self.vocabulary_changed.emit()
        self.refresh()

    def _edit_entry(self, lemma: str) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        store = VocabularyStore(self._data_root, language)
        entry = store.get(lemma)
        if entry is None:
            return
        form = prompt_edit_word(self, entry=entry)
        if form is None:
            return
        try:
            updated = store.update_entry(
                lemma,
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
            job_service = JobService(self._data_root)
            enqueue_vocabulary_word_embed(
                job_service,
                language_code=language,
                lemma=updated.lemma,
            )
            if self._supervisor is not None:
                self._supervisor.ensure_running()
        self.vocabulary_changed.emit()
        self.refresh()

    def _delete_entry(self, lemma: str) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        confirm = QMessageBox.question(
            self,
            "Delete word",
            f'Delete "{lemma}" from vocabulary?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        store = VocabularyStore(self._data_root, language)
        try:
            snapshot = store.delete_entry(lemma)
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Vocabulary", str(error))
            return
        self._show_delete_undo(snapshot)
        self.vocabulary_changed.emit()
        self.refresh()

    def _show_delete_undo(self, snapshot: DeletedVocabularyEntry) -> None:
        self._delete_undo_snapshot = snapshot
        self._delete_undo_banner.show()
        self._delete_undo_timer.start(DELETE_UNDO_WINDOW_MS)

    def _clear_delete_undo(self) -> None:
        self._delete_undo_snapshot = None
        self._delete_undo_banner.hide()

    def _undo_delete(self) -> None:
        language = self._settings.active_target_language
        snapshot = self._delete_undo_snapshot
        if language is None or snapshot is None:
            return
        store = VocabularyStore(self._data_root, language)
        try:
            store.restore_entry(snapshot)
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Vocabulary", str(error))
            return
        self._delete_undo_timer.stop()
        self._clear_delete_undo()
        self.vocabulary_changed.emit()
        self.refresh()

    def _manual_add_word(self) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        default_level = default_level_for_language(self._data_root, language)
        form = prompt_add_word(self, default_level=default_level)
        if form is None:
            return
        self._persist_add_form(form)

    def _persist_add_form(self, form: AddWordForm) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        store = VocabularyStore(self._data_root, language)
        try:
            store.add_entry(
                lemma=form.lemma,
                translation=form.translation,
                explanation=form.explanation,
                level_when_learned=form.level_when_learned,
                word_category=form.word_category,
            )
        except VocabularyStoreError as error:
            QMessageBox.warning(self, "Add word", str(error))
            return
        job_service = JobService(self._data_root)
        enqueue_vocabulary_word_embed(
            job_service,
            language_code=language,
            lemma=form.lemma,
        )
        if self._supervisor is not None:
            self._supervisor.ensure_running()
        self.vocabulary_changed.emit()
        self.refresh()

    def _export_vocabulary(self) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Export vocabulary",
            f"vocabulary-{language}.zip",
            "Zip archives (*.zip)",
        )
        if not path:
            return
        export_vocabulary_zip(
            Path(path),
            data_root=self._data_root,
            language_code=language,
        )

    def _import_vocabulary(self) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "Import vocabulary",
            "",
            "Zip archives (*.zip)",
        )
        if not path:
            return
        overwrite = (
            QMessageBox.question(
                self,
                "Import vocabulary",
                "Overwrite existing lemmas with the same spelling?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )
        try:
            result = import_vocabulary_zip(
                Path(path),
                data_root=self._data_root,
                language_code=language,
                overwrite=overwrite,
            )
        except (VocabularyImportError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Import vocabulary", str(error))
            return
        QMessageBox.information(
            self,
            "Import vocabulary",
            (
                f"Imported {result.imported}, skipped {result.skipped}, "
                f"overwritten {result.overwritten}."
            ),
        )
        self.vocabulary_changed.emit()
        self.refresh()
