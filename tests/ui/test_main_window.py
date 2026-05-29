"""Application shell layout tests."""

from __future__ import annotations

from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtWidgets import QLabel, QToolBar


def test_main_window_shows_shell_with_navigation_modes(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(supervisor=supervisor)
    qtbot.addWidget(window)

    assert window.windowTitle() == "LexiFlow"
    assert window.minimumWidth() >= 800
    assert window.minimumHeight() >= 500
    assert window.findChild(QToolBar) is not None
    assert window.findChild(QToolBar, "main_toolbar") is not None
    assert window.findChild(type(window.sidebar), "sidebar") is not None

    texts_action = window.navigation_action("texts")
    vocabulary_action = window.navigation_action("vocabulary")
    assert texts_action is not None
    assert vocabulary_action is not None
    assert texts_action.text() == "Texts"
    assert vocabulary_action.text() == "Vocabulary"


def test_vocabulary_mode_shows_empty_state_and_hides_sidebar(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(supervisor=supervisor)
    qtbot.addWidget(window)

    vocabulary_action = window.navigation_action("vocabulary")
    assert vocabulary_action is not None
    vocabulary_action.trigger()

    assert window.sidebar.isVisible() is False
    empty_title = window.current_content_widget.findChild(QLabel, "empty_state_title")
    assert empty_title is not None
    assert "vocabulary" in empty_title.text().lower()


def test_status_bar_shows_worker_offline_before_spawn(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(supervisor=supervisor)
    qtbot.addWidget(window)

    assert "offline" in window.statusBar().currentMessage().lower()


def test_status_bar_shows_idle_after_worker_spawn(qtbot, tmp_path) -> None:
    import sys

    from tests.ui.fakes import FakeProcess

    FakeProcess.instances.clear()
    supervisor = WorkerSupervisor(
        data_root=tmp_path,
        executable=sys.executable,
        process_factory=FakeProcess,
    )
    window = MainWindow(supervisor=supervisor)
    qtbot.addWidget(window)

    supervisor.ensure_running()

    assert "idle" in window.statusBar().currentMessage().lower()
