"""Primary application window."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from lexiflow_core.config.settings import Settings
from lexiflow_core.library.index import ensure_library_index
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
    QWidgetAction,
)

from lexiflow_ui.add_text_flow import list_texts_for_sidebar, submit_add_text
from lexiflow_ui.dialogs.add_text_dialog import open_add_text_dialog
from lexiflow_ui.widgets.active_target_language import ActiveTargetLanguageWidget
from lexiflow_ui.widgets.empty_state import EmptyStateWidget
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
        self._add_text_toolbar_button: QPushButton | None = None
        self._active_target_language: ActiveTargetLanguageWidget | None = None
        self._build_menu_bar()
        self._build_toolbar()
        self._build_central_layout()
        self._status_bar = WorkerStatusBar(supervisor, self)
        self.setStatusBar(self._status_bar)
        self._refresh_texts_ui(ensure_index=True)
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
        return self._content_stack.currentWidget()

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
        toolbar.addSeparator()
        self._add_text_toolbar_button = QPushButton("Add text", self)
        self._add_text_toolbar_button.setObjectName("toolbar_add_text_button")
        self._add_text_toolbar_button.setMinimumWidth(96)
        self._add_text_toolbar_button.clicked.connect(self._open_add_text_dialog)
        add_text_widget_action = QWidgetAction(self)
        add_text_widget_action.setDefaultWidget(self._add_text_toolbar_button)
        toolbar.addAction(add_text_widget_action)

    def _build_central_layout(self) -> None:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self._sidebar = SidebarWidget(container)
        self._sidebar.setFixedWidth(SIDEBAR_WIDTH)
        self._sidebar.add_text_button().clicked.connect(self._open_add_text_dialog)
        self._content_stack = QStackedWidget(container)
        self._texts_view = EmptyStateWidget(
            title="No texts yet",
            message="Add a text to start reading and building vocabulary.",
            action_text="Add text",
            parent=self._content_stack,
        )
        texts_action_button = self._texts_view.action_button()
        if texts_action_button is not None:
            texts_action_button.clicked.connect(self._open_add_text_dialog)
        self._vocabulary_view = EmptyStateWidget(
            title="No vocabulary yet",
            message="Words you save while reading will appear here.",
            parent=self._content_stack,
        )
        self._content_stack.addWidget(self._texts_view)
        self._content_stack.addWidget(self._vocabulary_view)
        layout.addWidget(self._sidebar)
        layout.addWidget(self._content_stack, stretch=1)
        self.setCentralWidget(container)

    def _can_add_text(self) -> bool:
        return self._settings.active_target_language is not None

    def _update_add_text_enabled(self) -> None:
        enabled = self._can_add_text()
        self._add_text_menu_action.setEnabled(enabled)
        if self._add_text_toolbar_button is not None:
            self._add_text_toolbar_button.setEnabled(enabled)
        self._sidebar.add_text_button().setEnabled(enabled)
        action = self._texts_view.action_button()
        if action is not None:
            action.setEnabled(enabled)

    def _refresh_texts_ui(self, *, ensure_index: bool = False) -> None:
        if ensure_index:
            ensure_library_index(self._data_root)
        titles = list_texts_for_sidebar(
            self._data_root, self._settings.active_target_language
        )
        self._sidebar.set_titles(titles)
        if titles:
            self._texts_view.set_content(
                title="Texts in your library",
                message=(
                    "Your texts are listed in the sidebar. "
                    "Background jobs may still be generating translations. "
                    "The reader opens in a later phase."
                ),
                show_action=False,
            )
        else:
            self._texts_view.set_content(
                title="No texts yet",
                message="Add a text to start reading and building vocabulary.",
                show_action=True,
            )
        self._update_add_text_enabled()

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
        self._refresh_texts_ui(ensure_index=True)
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
            self._texts_view if mode == "texts" else self._vocabulary_view
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._supervisor.shutdown(wait=True)
        super().closeEvent(event)
