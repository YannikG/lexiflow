"""Primary application window."""

from __future__ import annotations

from typing import Literal

from PySide6.QtGui import QAction, QActionGroup, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QToolBar,
    QWidget,
)

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
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._supervisor = supervisor
        self.setWindowTitle("LexiFlow")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self._navigation_actions: dict[NavigationMode, QAction] = {}
        self._build_toolbar()
        self._build_central_layout()
        self._status_bar = WorkerStatusBar(supervisor, self)
        self.setStatusBar(self._status_bar)
        self._show_navigation_mode("texts")

    @property
    def sidebar(self) -> SidebarWidget:
        return self._sidebar

    def navigation_action(self, mode: NavigationMode) -> QAction | None:
        return self._navigation_actions.get(mode)

    @property
    def current_content_widget(self) -> QWidget:
        return self._content_stack.currentWidget()

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

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setObjectName("main_toolbar")
        self.addToolBar(toolbar)
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
        self._content_stack = QStackedWidget(container)
        self._texts_view = EmptyStateWidget(
            title="No texts yet",
            message="Add a text to start reading and building vocabulary.",
            parent=self._content_stack,
        )
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
