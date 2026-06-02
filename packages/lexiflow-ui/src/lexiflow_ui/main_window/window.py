"""Primary application window."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.config.settings import Settings
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.index import LibraryIndex, ensure_library_index
from lexiflow_core.library.text_repository import TextRepository
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.main_window._chrome import MainWindowChromeMixin
from lexiflow_ui.main_window._jobs import MainWindowJobsMixin
from lexiflow_ui.main_window._menu import MainWindowMenuMixin
from lexiflow_ui.main_window._navigation import MainWindowNavigationMixin
from lexiflow_ui.main_window._shell_dialogs import MainWindowShellDialogsMixin
from lexiflow_ui.main_window._texts import MainWindowTextsMixin
from lexiflow_ui.main_window._types import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    NavigationMode,
)
from lexiflow_ui.shutdown_flow import confirm_application_quit
from lexiflow_ui.widgets.active_target_language import ActiveTargetLanguageWidget
from lexiflow_ui.widgets.reader_widget import ReaderWidget
from lexiflow_ui.widgets.sidebar import SidebarWidget
from lexiflow_ui.widgets.study_widget import StudyWidget
from lexiflow_ui.widgets.worker_status import WorkerStatusBar
from lexiflow_ui.worker_supervisor import WorkerSupervisor


class MainWindow(
    MainWindowMenuMixin,
    MainWindowChromeMixin,
    MainWindowTextsMixin,
    MainWindowJobsMixin,
    MainWindowNavigationMixin,
    MainWindowShellDialogsMixin,
    QMainWindow,
):
    """LexiFlow desktop shell: menus, navigation, reader, and job coordination."""

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
            data_root=self._data_root,
            on_open_jobs=self._open_jobs_panel,
            parent=self,
        )
        self.setStatusBar(self._status_bar)
        if self._llama_supervisor is not None:
            self._llama_supervisor.state_changed.connect(
                self._on_infrastructure_state_changed
            )
        self._supervisor.crashed.connect(self._on_worker_crashed)
        self._supervisor.state_changed.connect(self._status_bar.refresh)
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

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if not self._confirm_leave_editing_surfaces():
            event.ignore()
            return
        self._job_poll_timer.stop()
        job_service = JobService(self._data_root)
        if not confirm_application_quit(
            self,
            job_service=job_service,
            worker_supervisor=self._supervisor,
            llama_supervisor=self._llama_supervisor,
        ):
            event.ignore()
            return
        super().closeEvent(event)
