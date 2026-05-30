"""Reader widget and sidebar integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.paths import variant_path
from lexiflow_core.config.settings import Settings
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.reader_tabs import NATIVE_TAB, TRANSLATED_TAB
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QToolButton,
)


def _seed_reader_text(
    data_root: Path, *, source_url: str | None = None
) -> TextRepository:
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
            source_url=source_url,
        )
    )
    repo.apply_translated_variant(
        record.id,
        "# Traducción\n\nCuerpo traducido.",
    )
    return repo


def _sidebar_list(window: MainWindow) -> QListWidget:
    sidebar_list = window.sidebar.findChild(QListWidget, "sidebar_text_list")
    assert sidebar_list is not None
    return sidebar_list


def _click_sidebar_text(qtbot, window: MainWindow, row: int = 0) -> None:
    sidebar_list = _sidebar_list(window)
    item = sidebar_list.item(row)
    assert item is not None
    rect = sidebar_list.visualItemRect(item)
    qtbot.mouseClick(
        sidebar_list.viewport(),
        Qt.MouseButton.LeftButton,
        pos=rect.center(),
    )
    qtbot.wait(50)


@pytest.fixture
def reader_window(qtbot, tmp_path):
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
    return window, data_root


def test_first_open_defaults_to_translated_tab(reader_window, qtbot) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    reader = window.reader
    translated_tab = reader.findChild(QPushButton, "reader_tab_translated")
    assert translated_tab is not None
    assert translated_tab.isChecked()
    assert reader.active_tab_id == TRANSLATED_TAB
    read_pane = reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    mode_stack = reader.findChild(QStackedWidget, "reader_mode_stack")
    assert mode_stack is not None
    assert mode_stack.currentWidget() is read_pane
    assert "Cuerpo traducido" in read_pane.toPlainText()


def test_reopen_restores_last_viewed_tab(reader_window, qtbot) -> None:
    window, data_root = reader_window
    _click_sidebar_text(qtbot, window)

    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    assert native_tab is not None
    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)
    assert window.reader.active_tab_id == NATIVE_TAB

    supervisor = WorkerSupervisor(data_root=data_root)
    reopened = MainWindow(
        supervisor=supervisor,
        settings=Settings(
            data_root=data_root,
            active_target_language="es",
            native_language="en",
        ),
        data_root=data_root,
    )
    qtbot.addWidget(reopened)
    reopened.show()
    qtbot.waitExposed(reopened)
    _click_sidebar_text(qtbot, reopened)
    assert reopened.reader.active_tab_id == NATIVE_TAB


def test_single_simplified_variant_shows_flat_tab_label(
    reader_window, qtbot, tmp_path
) -> None:
    window, data_root = reader_window
    index = LibraryIndex(data_root)
    record = index.list_by_lang("es")[0]
    variant_path(Path(record.folder), "simplified-a2").write_text(
        "# Simple\n\nTexto simple.",
        encoding="utf-8",
    )

    _click_sidebar_text(qtbot, window)

    simplified_tab = window.reader.findChild(QPushButton, "reader_tab_simplified")
    menu = window.reader.findChild(QToolButton, "reader_simplified_menu")
    assert simplified_tab is not None
    assert simplified_tab.isVisible()
    assert "A2" in simplified_tab.text()
    assert menu is None or not menu.isVisible()


def test_multiple_simplified_variants_show_dropdown_menu(reader_window, qtbot) -> None:
    window, data_root = reader_window
    record = LibraryIndex(data_root).list_by_lang("es")[0]
    folder = Path(record.folder)
    variant_path(folder, "simplified-a2").write_text(
        "# A2\n\nTexto A2.",
        encoding="utf-8",
    )
    variant_path(folder, "simplified-b1").write_text(
        "# B1\n\nTexto B1.",
        encoding="utf-8",
    )

    _click_sidebar_text(qtbot, window)

    menu = window.reader.simplified_menu()
    assert menu.isVisible()
    assert menu.menu() is not None
    assert len(menu.menu().actions()) == 2


def test_edit_save_updates_translated_variant(reader_window, qtbot) -> None:
    window, data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    save_button = window.reader.findChild(QPushButton, "reader_save_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    assert edit_button is not None and save_button is not None and edit_pane is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nTexto guardado.")
    qtbot.mouseClick(save_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    record = LibraryIndex(data_root).list_by_lang("es")[0]
    saved = variant_path(Path(record.folder), "translated").read_text(encoding="utf-8")
    assert "Texto guardado." in saved
    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert read_pane is not None
    assert "Texto guardado." in read_pane.toPlainText()


def test_source_url_button_visible_when_metadata_has_url(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root, source_url="https://example.com/article")
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

    _click_sidebar_text(qtbot, window)

    source_button = window.reader.findChild(QPushButton, "reader_source_button")
    assert source_button is not None
    assert source_button.isVisible()
