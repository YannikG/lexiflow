"""Primary application window."""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from uuid import UUID

from lexiflow_core.config.settings import Settings
from lexiflow_core.library.index import LibraryIndex, ensure_library_index
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
from lexiflow_ui.dialogs.add_text_dialog import open_add_text_dialog
from lexiflow_ui.reader_flow import (
    list_texts_for_sidebar,
    persist_last_viewed_tab,
    resolve_initial_tab,
)
from lexiflow_ui.widgets.active_target_language import ActiveTargetLanguageWidget
from lexiflow_ui.widgets.empty_state import EmptyStateWidget
from lexiflow_ui.widgets.reader_widget import ReaderWidget
from lexiflow_ui.widgets.sidebar import SidebarWidget
from lexiflow_ui.widgets.worker_status import WorkerStatusBar
from lexiflow_ui.worker_supervisor import WorkerSupervisor

NavigationMode = Literal["texts", "vocabulary"]

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
        settings: Settings | None = None,
        data_root: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._supervisor = supervisor
        self._settings = settings if settings is not None else Settings()
        self._data_root = data_root if data_root is not None else supervisor.data_root
        self.setWindowTitle("LexiFlow")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self._navigation_actions: dict[NavigationMode, QAction] = {}
        self._active_target_language: ActiveTargetLanguageWidget | None = None
        self._build_menu_bar()
        self._build_toolbar()
        self._build_central_layout()
        self._status_bar = WorkerStatusBar(supervisor, self)
        self.setStatusBar(self._status_bar)
        ensure_library_index(self._data_root)
        self._library_index = LibraryIndex(self._data_root)
        self._text_repository = TextRepository(self._data_root, self._library_index)
        self._open_text_id: UUID | None = None
        self._refresh_texts_ui()
        self._show_navigation_mode("texts")

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
    def data_root(self) -> Path:
        return self._data_root

    def add_text_action(self) -> QAction:
        """File menu action wired to the standard New shortcut."""
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
        file_menu = self.menuBar().addMenu("&File")
        self._add_text_menu_action = QAction("Add text…", self)
        self._add_text_menu_action.setShortcut(QKeySequence.StandardKey.New)
        self._add_text_menu_action.triggered.connect(self._open_add_text_dialog)
        file_menu.addAction(self._add_text_menu_action)

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
        for mode, label in (("texts", "Texts"), ("vocabulary", "Vocabulary")):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda _checked=False, m=mode: self._show_navigation_mode(m)
            )
            group.addAction(action)
            toolbar.addAction(action)
            self._navigation_actions[mode] = action

    def _build_central_layout(self) -> None:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self._sidebar = SidebarWidget(container)
        self._sidebar.setFixedWidth(SIDEBAR_WIDTH)
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
        self._reader = ReaderWidget(self._texts_stack)
        self._reader.tab_changed.connect(self._on_reader_tab_changed)
        self._texts_stack.addWidget(self._texts_view)
        self._texts_stack.addWidget(self._reader)
        self._content_stack = QStackedWidget(container)
        self._vocabulary_view = EmptyStateWidget(
            title="No vocabulary yet",
            message="Words you save while reading will appear here.",
            parent=self._content_stack,
        )
        self._content_stack.addWidget(self._texts_stack)
        self._content_stack.addWidget(self._vocabulary_view)
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

    def _open_reader_for_text(self, text_id: UUID) -> None:
        record = self._text_repository.get_text(text_id)
        initial_tab = resolve_initial_tab(self._library_index, record)
        self._open_text_id = text_id
        self._reader.open_text(
            record=record,
            repo=self._text_repository,
            index=self._library_index,
            settings=self._settings,
            initial_tab=initial_tab,
        )
        self._texts_stack.setCurrentWidget(self._reader)

    def _on_reader_tab_changed(self, tab_id: str) -> None:
        if self._open_text_id is None:
            return
        persist_last_viewed_tab(self._library_index, self._open_text_id, tab_id)

    def _open_add_text_dialog(self) -> None:
        if not self._can_add_text():
            QMessageBox.information(
                self,
                "Add text",
                "Finish language setup in onboarding before adding texts.",
            )
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
        submit_add_text(
            data_root=self._data_root,
            settings=self._settings,
            supervisor=self._supervisor,
            form=form,
            parent=self,
        )
        self._refresh_texts_ui()
        self._schedule_library_refresh()

    def _schedule_library_refresh(self) -> None:
        """Re-read the library index while background jobs may update titles."""
        for delay_ms in (500, 2000, 5000, 10000, 20000, 40000):
            QTimer.singleShot(delay_ms, lambda: self._refresh_texts_ui())

    def _show_navigation_mode(self, mode: NavigationMode) -> None:
        action = self._navigation_actions[mode]
        action.setChecked(True)
        self._sidebar.setVisible(mode == "texts")
        self._content_stack.setCurrentWidget(
            self._texts_stack if mode == "texts" else self._vocabulary_view
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._supervisor.shutdown(wait=True)
        super().closeEvent(event)
