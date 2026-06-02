"""Primary application window."""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from uuid import UUID

from lexiflow_core.config.settings import Settings
from lexiflow_core.jobs.job_errors import user_facing_job_error
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.index import LibraryIndex, ensure_library_index
from lexiflow_core.library.reader_tabs import NATIVE_TAB
from lexiflow_core.library.search_models import SearchHit
from lexiflow_core.library.text_repository import TextRepository
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QWidget,
)

from lexiflow_ui.add_text_flow import submit_add_text
from lexiflow_ui.ai_worker_startup import ensure_ai_workers_running
from lexiflow_ui.dialogs.add_text_dialog import open_add_text_dialog
from lexiflow_ui.dialogs.trash_dialog import open_trash_dialog
from lexiflow_ui.find_in_texts_flow import find_in_texts
from lexiflow_ui.library_options_flow import (
    export_library_backup,
    rebuild_library_index,
    replace_current_library,
    restore_library_to_new_folder,
)
from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.reader_flow import (
    list_texts_for_sidebar,
    persist_last_viewed_tab,
    resolve_initial_tab,
)
from lexiflow_ui.remove_target_language_flow import offer_remove_target_language
from lexiflow_ui.unsaved_changes import DirtyEditor, confirm_leave_dirty_editors
from lexiflow_ui.widgets.active_target_language import ActiveTargetLanguageWidget
from lexiflow_ui.widgets.empty_state import EmptyStateWidget
from lexiflow_ui.widgets.library_search_field import LibrarySearchField
from lexiflow_ui.widgets.reader_widget import ReaderWidget
from lexiflow_ui.widgets.sidebar import SidebarWidget
from lexiflow_ui.widgets.study_widget import StudyWidget
from lexiflow_ui.widgets.vocabulary_widget import VocabularyWidget
from lexiflow_ui.widgets.worker_status import WorkerStatusBar
from lexiflow_ui.worker_supervisor import WorkerSupervisor

NavigationMode = Literal["texts", "vocabulary", "study"]

_LLM_JOB_TYPES = frozenset(
    {JobType.CLEANUP, JobType.TRANSLATE, JobType.SIMPLIFY, JobType.LEMMA}
)

DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 500
SIDEBAR_WIDTH = 260


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        supervisor: WorkerSupervisor,
        llama_supervisor: LlamaServerSupervisor | None = None,
        settings: Settings | None = None,
        data_root: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._supervisor = supervisor
        self._llama_supervisor = llama_supervisor
        self._settings = settings if settings is not None else Settings()
        self._data_root = data_root if data_root is not None else supervisor.data_root
        self.setWindowTitle("LexiFlow")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self._navigation_actions: dict[NavigationMode, QAction] = {}
        self._active_target_language: ActiveTargetLanguageWidget | None = None
        ensure_library_index(self._data_root)
        self._library_index = LibraryIndex(self._data_root)
        self._text_repository = TextRepository(self._data_root, self._library_index)
        self._build_menu_bar()
        self._build_toolbar()
        self._build_central_layout()
        self._status_bar = WorkerStatusBar(
            supervisor,
            llama_supervisor,
            self,
        )
        self.setStatusBar(self._status_bar)
        if self._llama_supervisor is not None:
            self._llama_supervisor.state_changed.connect(
                self._on_infrastructure_state_changed
            )
        self._open_text_id: UUID | None = None
        self._seen_completed_job_ids: set[UUID] = set()
        self._seen_failed_job_ids: set[UUID] = set()
        self._refresh_texts_ui()
        self._show_navigation_mode("texts")
        self._job_poll_timer = QTimer(self)
        self._job_poll_timer.setInterval(1000)
        self._job_poll_timer.timeout.connect(self._poll_background_jobs)
        self._job_poll_timer.start()

    @property
    def active_target_language(self) -> ActiveTargetLanguageWidget | None:
        return self._active_target_language

    @property
    def sidebar(self) -> SidebarWidget:
        return self._sidebar

    def navigation_action(self, mode: NavigationMode) -> QAction | None:
        return self._navigation_actions.get(mode)

    @property
    def current_content_widget(self) -> QWidget:
        mode_widget = self._content_stack.currentWidget()
        if mode_widget is self._texts_stack:
            return self._texts_stack.currentWidget()
        return mode_widget

    @property
    def reader(self) -> ReaderWidget:
        return self._reader

    @property
    def study(self) -> StudyWidget:
        return self._study

    @property
    def data_root(self) -> Path:
        return self._data_root

    def add_text_action(self) -> QAction:
        """Texts menu action wired to the standard New shortcut."""
        return self._add_text_menu_action

    def texts_empty_action_button(self) -> QPushButton | None:
        """Add text button in the Texts empty state, when shown."""
        return self._texts_view.action_button()

    def request_activation(self) -> None:
        """Raise and focus this window (e.g. second-instance Open existing)."""
        if self.isMinimized():
            self.showNormal()
        elif not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()
        app = QApplication.instance()
        if app is not None:
            app.alert(self)

    def _build_menu_bar(self) -> None:
        texts_menu = self.menuBar().addMenu("&Texts")
        self._add_text_menu_action = QAction("Add text…", self)
        self._add_text_menu_action.setShortcut(QKeySequence.StandardKey.New)
        self._add_text_menu_action.triggered.connect(self._open_add_text_dialog)
        texts_menu.addAction(self._add_text_menu_action)

        vocabulary_menu = self.menuBar().addMenu("&Vocabulary")
        self._export_vocabulary_action = QAction("Export vocabulary…", self)
        vocabulary_menu.addAction(self._export_vocabulary_action)
        self._import_vocabulary_action = QAction("Import vocabulary…", self)
        vocabulary_menu.addAction(self._import_vocabulary_action)
        vocabulary_menu.addSeparator()
        self._remove_language_action = QAction("Remove target language…", self)
        self._remove_language_action.triggered.connect(self._remove_target_language)
        vocabulary_menu.addAction(self._remove_language_action)

        library_menu = self.menuBar().addMenu("&Library")
        self._trash_action = QAction("Trash…", self)
        self._trash_action.triggered.connect(self._open_trash_dialog)
        library_menu.addAction(self._trash_action)

        options_menu = self.menuBar().addMenu("&Options")
        self._export_library_action = QAction("Export library…", self)
        self._export_library_action.triggered.connect(self._export_library_backup)
        options_menu.addAction(self._export_library_action)
        self._restore_library_action = QAction("Restore library to new folder…", self)
        self._restore_library_action.triggered.connect(self._restore_library_backup)
        options_menu.addAction(self._restore_library_action)
        self._replace_library_action = QAction("Replace current library…", self)
        self._replace_library_action.triggered.connect(self._replace_current_library)
        options_menu.addAction(self._replace_library_action)
        options_menu.addSeparator()
        self._rebuild_index_action = QAction("Rebuild library index", self)
        self._rebuild_index_action.triggered.connect(self._rebuild_library_index)
        options_menu.addAction(self._rebuild_index_action)

        self._search_action = QAction("Search library", self)
        self._search_action.setShortcut(QKeySequence.StandardKey.Find)
        self._search_action.triggered.connect(self._focus_library_search)
        self.addAction(self._search_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setObjectName("main_toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)
        if self._settings.active_target_language is not None:
            self._active_target_language = ActiveTargetLanguageWidget(
                settings=self._settings,
                data_root=self._data_root,
                parent=self,
            )
            toolbar.addWidget(self._active_target_language)
            toolbar.addSeparator()
        group = QActionGroup(self)
        group.setExclusive(True)
        for mode, label in (
            ("texts", "Texts"),
            ("vocabulary", "Vocabulary"),
            ("study", "Study"),
        ):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda _checked=False, m=mode: self._show_navigation_mode(m)
            )
            group.addAction(action)
            toolbar.addAction(action)
            self._navigation_actions[mode] = action
        toolbar.addSeparator()
        self._toolbar_search = LibrarySearchField(
            index=self._library_index,
            language_code=lambda: self._settings.active_target_language,
            object_name="toolbar_search",
            parent=toolbar,
        )
        self._toolbar_search.setMinimumWidth(220)
        self._toolbar_search.hit_selected.connect(self._on_library_search_hit)
        toolbar.addWidget(self._toolbar_search)

    def _build_central_layout(self) -> None:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self._sidebar = SidebarWidget(container)
        self._sidebar.setFixedWidth(SIDEBAR_WIDTH)
        self._sidebar.search_requested.connect(self._toolbar_search.focus_search)
        self._sidebar.add_text_button().clicked.connect(self._open_add_text_dialog)
        self._sidebar.text_selected.connect(self._open_reader_for_text)
        self._texts_stack = QStackedWidget(container)
        self._texts_stack.setObjectName("texts_content_stack")
        self._texts_view = EmptyStateWidget(
            title="No texts yet",
            message="Add a text to start reading and building vocabulary.",
            action_text="Add text",
            parent=self._texts_stack,
        )
        texts_action_button = self._texts_view.action_button()
        if texts_action_button is not None:
            texts_action_button.clicked.connect(self._open_add_text_dialog)
        self._reader = ReaderWidget(
            self._texts_stack,
            data_root=self._data_root,
            supervisor=self._supervisor,
            llama_supervisor=self._llama_supervisor,
        )
        self._reader.tab_changed.connect(self._on_reader_tab_changed)
        self._reader.text_saved.connect(self._refresh_texts_ui)
        self._reader.text_deleted.connect(self._on_reader_text_deleted)
        self._reader.simplify_submitted.connect(self._on_simplify_submitted)
        self._supervisor.state_changed.connect(self._on_infrastructure_state_changed)
        self._texts_stack.addWidget(self._texts_view)
        self._texts_stack.addWidget(self._reader)
        self._content_stack = QStackedWidget(container)
        self._vocabulary = VocabularyWidget(
            data_root=self._data_root,
            settings=self._settings,
            supervisor=self._supervisor,
            parent=self._content_stack,
        )
        self._vocabulary.vocabulary_changed.connect(self._on_vocabulary_changed)
        self._vocabulary.find_in_texts_requested.connect(self._find_in_texts_for_lemma)
        self._export_vocabulary_action.triggered.connect(
            self._vocabulary.export_vocabulary
        )
        self._import_vocabulary_action.triggered.connect(
            self._vocabulary.import_vocabulary
        )
        self._study = StudyWidget(
            data_root=self._data_root,
            settings=self._settings,
            parent=self._content_stack,
        )
        self._study.vocabulary_changed.connect(self._on_vocabulary_changed)
        self._reader.vocabulary_changed.connect(self._on_vocabulary_changed)
        self._content_stack.addWidget(self._texts_stack)
        self._content_stack.addWidget(self._vocabulary)
        self._content_stack.addWidget(self._study)
        layout.addWidget(self._sidebar)
        layout.addWidget(self._content_stack, stretch=1)
        self.setCentralWidget(container)

    def _can_add_text(self) -> bool:
        return self._settings.active_target_language is not None

    def _update_add_text_enabled(self) -> None:
        enabled = self._can_add_text()
        self._add_text_menu_action.setEnabled(enabled)
        self._sidebar.add_text_button().setEnabled(enabled)
        action = self._texts_view.action_button()
        if action is not None:
            action.setEnabled(enabled)

    def _refresh_texts_ui(self) -> None:
        titles = list_texts_for_sidebar(
            self._data_root, self._settings.active_target_language
        )
        self._sidebar.set_texts(titles)
        if titles:
            self._texts_view.set_content(
                title="Texts in your library",
                message="Select a text in the sidebar to open the reader.",
                show_action=False,
            )
            if self._open_text_id is not None:
                self._sidebar.select_text(self._open_text_id)
                self._texts_stack.setCurrentWidget(self._reader)
            else:
                self._texts_stack.setCurrentWidget(self._texts_view)
        else:
            self._texts_view.set_content(
                title="No texts yet",
                message="Add a text to start reading and building vocabulary.",
                show_action=True,
            )
        self._update_add_text_enabled()

    def _dirty_editors(self) -> tuple[DirtyEditor, ...]:
        return (self._reader,)

    def _confirm_leave_editing_surfaces(self) -> bool:
        return confirm_leave_dirty_editors(self, self._dirty_editors())

    def _open_reader_for_text(self, text_id: UUID) -> None:
        if (
            self._open_text_id == text_id
            and self._texts_stack.currentWidget() is self._reader
            and self._reader.is_editing()
        ):
            self._sidebar.select_text(text_id)
            return
        record = self._text_repository.get_text(text_id)
        initial_tab = resolve_initial_tab(self._library_index, record)
        opened = self._reader.open_text(
            record=record,
            repo=self._text_repository,
            index=self._library_index,
            settings=self._settings,
            initial_tab=initial_tab,
        )
        if not opened:
            if self._open_text_id is not None:
                self._sidebar.select_text(self._open_text_id)
            return
        self._open_text_id = text_id
        self._texts_stack.setCurrentWidget(self._reader)

    def _open_reader_for_search_hit(self, hit: SearchHit, *, query: str) -> None:
        if not self._confirm_leave_editing_surfaces():
            return
        texts_action = self._navigation_actions.get("texts")
        if texts_action is not None:
            texts_action.setChecked(True)
        self._show_navigation_mode("texts")
        record = self._text_repository.get_text(hit.text_id)
        opened = self._reader.open_text(
            record=record,
            repo=self._text_repository,
            index=self._library_index,
            settings=self._settings,
            initial_tab=hit.variant,
        )
        if not opened:
            return
        self._open_text_id = hit.text_id
        self._sidebar.select_text(hit.text_id)
        self._texts_stack.setCurrentWidget(self._reader)
        self._reader.scroll_to_match(query)

    def _on_library_search_hit(self, hit: SearchHit) -> None:
        self._open_reader_for_search_hit(
            hit,
            query=self._search_query_from_hit(hit),
        )

    def _focus_library_search(self) -> None:
        if self._settings.active_target_language is None:
            QMessageBox.information(
                self,
                "Search",
                "Finish language setup before searching the library.",
            )
            return
        self._toolbar_search.focus_search()

    def _search_query_from_hit(self, hit: SearchHit) -> str:
        import re

        match = re.search(r"<mark>(.*?)</mark>", hit.snippet)
        if match is not None:
            return match.group(1)
        return hit.title

    def _find_in_texts_for_lemma(self, lemma: str) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        find_in_texts(
            self,
            index=self._library_index,
            language_code=language,
            query=lemma,
            on_hit_selected=lambda hit: self._open_reader_for_search_hit(
                hit,
                query=lemma,
            ),
        )

    def _open_trash_dialog(self) -> None:
        open_trash_dialog(
            self,
            data_root=self._data_root,
            language_code=self._settings.active_target_language,
            text_repository=self._text_repository,
            supervisor=self._supervisor,
        )
        self._refresh_texts_ui()
        self._vocabulary.refresh()
        self._on_vocabulary_changed()

    def _export_library_backup(self) -> None:
        export_library_backup(parent=self, data_root=self._data_root)

    def _restore_library_backup(self) -> None:
        restore_library_to_new_folder(parent=self)

    def _replace_current_library(self) -> None:
        if replace_current_library(
            parent=self,
            data_root=self._data_root,
            library_index=self._library_index,
        ):
            self._refresh_texts_ui()
            self._vocabulary.refresh()

    def _rebuild_library_index(self) -> None:
        rebuild_library_index(
            parent=self,
            data_root=self._data_root,
            library_index=self._library_index,
            language_code=self._settings.active_target_language,
        )
        self._refresh_texts_ui()

    def _on_reader_tab_changed(self, tab_id: str) -> None:
        if self._open_text_id is None:
            return
        persist_last_viewed_tab(self._library_index, self._open_text_id, tab_id)

    def _on_reader_text_deleted(self) -> None:
        self._open_text_id = None
        self._refresh_texts_ui()
        self._texts_stack.setCurrentWidget(self._texts_view)

    def _open_add_text_dialog(self) -> None:
        if not self._can_add_text():
            QMessageBox.information(
                self,
                "Add text",
                "Finish language setup in onboarding before adding texts.",
            )
            return
        if not self._confirm_leave_editing_surfaces():
            return
        target = self._settings.active_target_language
        assert target is not None
        form = open_add_text_dialog(
            data_root=self._data_root,
            target_language=target,
            parent=self,
        )
        if form is None:
            return
        text_id = submit_add_text(
            data_root=self._data_root,
            settings=self._settings,
            form=form,
            parent=self,
        )
        if text_id is None:
            return
        self._refresh_texts_ui()
        self._open_reader_for_text(text_id)
        self._reader.select_tab(NATIVE_TAB)
        self._ensure_background_workers(JobService(self._data_root))
        self._schedule_reader_refresh()
        self._schedule_library_refresh()

    def _schedule_library_refresh(self) -> None:
        """Re-read the library index while background jobs may update titles."""
        for delay_ms in (500, 2000, 5000, 10000, 20000, 40000):
            QTimer.singleShot(delay_ms, lambda: self._refresh_texts_ui())

    def _on_simplify_submitted(self) -> None:
        self._ensure_background_workers(JobService(self._data_root))
        self._schedule_reader_refresh()

    def _on_infrastructure_state_changed(self) -> None:
        self._ensure_background_workers(JobService(self._data_root))
        self._status_bar.refresh()
        if self._texts_stack.currentWidget() is self._reader:
            self._reader.refresh_infrastructure_status()

    def _schedule_reader_refresh(self) -> None:
        for delay_ms in (500, 1500, 3000, 6000, 12000):
            QTimer.singleShot(delay_ms, self._poll_background_jobs)

    def _uses_native_llm(self) -> bool:
        return not self._settings.ollama_url and self._llama_supervisor is not None

    def _ensure_background_workers(self, job_service: JobService) -> None:
        pending_llm = any(
            job.status == JobStatus.PENDING and job.job_type in _LLM_JOB_TYPES
            for job in job_service.list_jobs()
        )
        pending_any = any(
            job.status == JobStatus.PENDING for job in job_service.list_jobs()
        )
        if not pending_any:
            return
        if pending_llm and self._uses_native_llm():
            ensure_ai_workers_running(self._supervisor, self._llama_supervisor)
            return
        self._supervisor.ensure_running()

    def _poll_background_jobs(self) -> None:
        job_service = JobService(self._data_root)
        self._ensure_background_workers(job_service)
        if self._open_text_id is None:
            return
        open_text = str(self._open_text_id)
        reload_reader = False
        refresh_sidebar = False
        focus_simplified_level: CEFRLevel | None = None
        for job in job_service.list_jobs():
            payload_text_id = job.payload.get("text_id")
            if payload_text_id != open_text:
                continue
            if job.id in self._seen_completed_job_ids:
                continue
            if job.id in self._seen_failed_job_ids:
                continue
            if job.status == JobStatus.FAILED:
                if job.job_type in (
                    JobType.CLEANUP,
                    JobType.TRANSLATE,
                    JobType.SIMPLIFY,
                ):
                    self._seen_failed_job_ids.add(job.id)
                    label = job.job_type.value.capitalize()
                    error = user_facing_job_error(job.error_message or "unknown error")
                    self._status_bar.show_job_error(f"{label} failed: {error}")
                    reload_reader = True
                continue
            if job.status != JobStatus.COMPLETED:
                continue
            self._seen_completed_job_ids.add(job.id)
            if job.job_type in (JobType.CLEANUP, JobType.TRANSLATE, JobType.SIMPLIFY):
                reload_reader = True
            if job.job_type in (JobType.TRANSLATE, JobType.SIMPLIFY):
                refresh_sidebar = True
            if job.job_type == JobType.SIMPLIFY:
                level_raw = job.payload.get("level")
                if isinstance(level_raw, str):
                    try:
                        focus_simplified_level = CEFRLevel(level_raw.strip().upper())
                    except ValueError:
                        focus_simplified_level = None
        if refresh_sidebar:
            self._refresh_texts_ui()
        if reload_reader and self._texts_stack.currentWidget() is self._reader:
            self._reader.reload_from_disk(focus_simplified_level=focus_simplified_level)

    def _show_navigation_mode(self, mode: NavigationMode) -> None:
        if mode != "texts" and not self._confirm_leave_editing_surfaces():
            self._navigation_actions["texts"].setChecked(True)
            return
        action = self._navigation_actions[mode]
        action.setChecked(True)
        self._sidebar.setVisible(mode == "texts")
        mode_widget = {
            "texts": self._texts_stack,
            "vocabulary": self._vocabulary,
            "study": self._study,
        }[mode]
        self._content_stack.setCurrentWidget(mode_widget)
        if mode == "vocabulary":
            self._vocabulary.refresh()
        elif mode == "study":
            self._study.refresh()

    def _on_vocabulary_changed(self) -> None:
        self._vocabulary.refresh()
        self._study.refresh()
        self._reader.refresh_word_panel()

    def _remove_target_language(self) -> None:
        iso = self._settings.active_target_language
        if iso is None:
            QMessageBox.information(
                self,
                "Remove target language",
                "No active target language is configured.",
            )
            return
        from lexiflow_core.config.settings_store import SettingsStore

        updated = offer_remove_target_language(
            self,
            data_root=self._data_root,
            language_code=iso,
            settings=self._settings,
            settings_store=SettingsStore(),
        )
        if updated is None:
            return
        self._settings = updated
        self._refresh_texts_ui()
        self._vocabulary.refresh()
        self._study.refresh()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if not self._confirm_leave_editing_surfaces():
            event.ignore()
            return
        self._job_poll_timer.stop()
        if self._llama_supervisor is not None:
            self._llama_supervisor.shutdown(wait=True)
        self._supervisor.shutdown(wait=True)
        super().closeEvent(event)
