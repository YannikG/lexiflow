"""Application shell layout tests."""

from __future__ import annotations

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QLabel, QPushButton, QToolBar


def test_main_window_shows_shell_with_navigation_modes(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

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

    toolbar_button = window.findChild(QPushButton, "toolbar_add_text_button")
    assert toolbar_button is not None
    assert toolbar_button.isVisible()
    sidebar_button = window.sidebar.add_text_button()
    assert sidebar_button.isVisible()


def test_texts_empty_state_shows_add_text_button(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    button = window.texts_empty_action_button()
    assert button is not None
    assert button.text() == "Add text"
    assert button.isEnabled()


def test_add_text_action_opens_dialog(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[bool] = []

    def fake_open(**_kwargs: object) -> None:
        opened.append(True)
        return None

    monkeypatch.setattr(
        "lexiflow_ui.main_window.open_add_text_dialog",
        fake_open,
    )
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    action = window.add_text_action()
    assert action.shortcut() == QKeySequence.StandardKey.New
    action.trigger()
    assert opened == [True]


def test_texts_ui_updates_after_text_exists(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    repo.create_text(
        CreateTextRequest(
            title="Hola",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    supervisor = WorkerSupervisor(data_root=data_root)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(
            data_root=data_root,
            active_target_language="es",
            native_language="en",
        ),
        data_root=data_root,
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    assert window.sidebar.findChild(QLabel, "sidebar_empty_label").isHidden()
    content = window.current_content_widget
    title = content.findChild(QLabel, "empty_state_title")
    assert title is not None
    assert "library" in title.text().lower()
    action = content.findChild(QPushButton, "empty_state_action")
    assert action is None or not action.isVisible()


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


def test_request_activation_restores_minimized_window(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(supervisor=supervisor)
    qtbot.addWidget(window)
    window.show()
    window.showMinimized()
    qtbot.waitUntil(window.isMinimized, timeout=2000)

    window.request_activation()

    qtbot.waitUntil(lambda: not window.isMinimized(), timeout=2000)
    assert window.isVisible()
