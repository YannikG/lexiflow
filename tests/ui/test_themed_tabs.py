"""Tab controls with global UI theme applied."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.reader_tabs import NATIVE_TAB, TRANSLATED_TAB
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.text_pipeline.models import InputTab
from lexiflow_ui.dialogs.add_text_dialog import AddTextDialog
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.theme import apply_app_theme
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
)


@pytest.fixture(autouse=True)
def _themed_app() -> Iterator[None]:
    app = QApplication.instance()
    assert app is not None
    app.setStyleSheet("")
    apply_app_theme(app, theme="dark")
    yield


def _seed_reader_text(data_root: Path) -> None:
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    repo.apply_translated_variant(
        record.id,
        "# Traducción\n\nCuerpo traducido.",
    )


def test_themed_main_navigation_switches_modes(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
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

    texts_action = window.navigation_action("texts")
    vocabulary_action = window.navigation_action("vocabulary")
    assert texts_action is not None and vocabulary_action is not None
    assert texts_action.isChecked()

    vocabulary_action.trigger()
    qtbot.wait(50)

    assert vocabulary_action.isChecked()
    assert not texts_action.isChecked()
    heading = window.current_content_widget.findChild(QLabel, "empty_state_title")
    assert heading is not None
    assert heading.text() == "No vocabulary yet"


def test_themed_reader_active_tab_stays_checked_on_reclick(
    qtbot, tmp_path: Path
) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
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

    from PySide6.QtWidgets import QListWidget

    sidebar_list = window.sidebar.findChild(QListWidget, "sidebar_text_list")
    assert sidebar_list is not None
    item = sidebar_list.item(0)
    assert item is not None
    rect = sidebar_list.visualItemRect(item)
    qtbot.mouseClick(
        sidebar_list.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center(),
    )
    qtbot.wait(50)

    translated_tab = window.reader.findChild(QPushButton, "reader_tab_translated")
    assert translated_tab is not None
    assert translated_tab.isChecked()

    qtbot.mouseClick(translated_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert translated_tab.isChecked()
    assert window.reader.active_tab_id == TRANSLATED_TAB


def test_themed_reader_tab_switch_updates_content(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
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

    from PySide6.QtWidgets import QListWidget

    sidebar_list = window.sidebar.findChild(QListWidget, "sidebar_text_list")
    assert sidebar_list is not None
    item = sidebar_list.item(0)
    assert item is not None
    rect = sidebar_list.visualItemRect(item)
    qtbot.mouseClick(
        sidebar_list.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center(),
    )
    qtbot.wait(50)

    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert native_tab is not None and read_pane is not None
    assert window.reader.active_tab_id == TRANSLATED_TAB

    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert window.reader.active_tab_id == NATIVE_TAB
    assert native_tab.isChecked()
    assert "hola" in read_pane.toPlainText()


def test_themed_add_text_dialog_tab_switch_selects_target(
    qtbot, tmp_path: Path
) -> None:
    dialog = AddTextDialog(
        data_root=tmp_path / "LexiFlow",
        target_language="es",
    )
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)

    native_tab = dialog.findChild(QPushButton, "add_text_tab_native")
    target_tab = dialog.findChild(QPushButton, "add_text_tab_target")
    assert native_tab is not None and target_tab is not None
    assert native_tab.isChecked()
    assert not target_tab.isChecked()

    qtbot.mouseClick(target_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert target_tab.isChecked()
    assert not native_tab.isChecked()

    title = dialog.findChild(QLineEdit, "add_text_title")
    assert title is not None
    title.setText("My title")
    dialog.paste_edit().setPlainText("Hola")
    data = dialog.form_data()
    assert data is not None
    assert data.input_tab == InputTab.TARGET


def test_theme_stylesheet_targets_tab_object_names() -> None:
    from lexiflow_ui.theme_stylesheet import build_theme_stylesheet

    stylesheet = build_theme_stylesheet("dark")
    assert "QPushButton#reader_tab_native" in stylesheet
    assert "QPushButton#add_text_tab_target" in stylesheet
    assert 'objectName^="reader_tab_simplified_"' in stylesheet
    assert "QPushButton#reader_tab_native:checked" in stylesheet
    assert "QPushButton#reader_tab_translated:checked" in stylesheet
    assert stylesheet.count(":checked") >= 6


def test_themed_reader_only_active_tab_is_checked(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
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

    from PySide6.QtWidgets import QListWidget

    sidebar_list = window.sidebar.findChild(QListWidget, "sidebar_text_list")
    assert sidebar_list is not None
    item = sidebar_list.item(0)
    assert item is not None
    rect = sidebar_list.visualItemRect(item)
    qtbot.mouseClick(
        sidebar_list.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center(),
    )
    qtbot.wait(50)

    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    translated_tab = window.reader.findChild(QPushButton, "reader_tab_translated")
    assert native_tab is not None and translated_tab is not None
    assert translated_tab.isChecked()
    assert not native_tab.isChecked()

    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert native_tab.isChecked()
    assert not translated_tab.isChecked()
    checked = [tab for tab in (native_tab, translated_tab) if tab.isChecked()]
    assert checked == [native_tab]
