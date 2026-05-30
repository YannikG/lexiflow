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
    QLabel,
    QLineEdit,
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


def _click_sidebar_text_by_title(qtbot, window: MainWindow, title: str) -> None:
    sidebar_list = _sidebar_list(window)
    for row in range(sidebar_list.count()):
        item = sidebar_list.item(row)
        if item is not None and item.text() == title:
            _click_sidebar_text(qtbot, window, row=row)
            return
    raise AssertionError(f"sidebar text not found: {title}")


def _open_reader_window(qtbot, data_root: Path) -> MainWindow:
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
    return window


def _seed_second_text(data_root: Path) -> None:
    _, index = LibraryCoordinator.open(data_root)
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Second text",
            group="News",
            target_language="es",
            native_language="en",
            body="adios",
        )
    )
    repo.apply_translated_variant(
        record.id,
        "# Segundo\n\nOtro cuerpo traducido.",
    )


@pytest.fixture
def reader_window(qtbot, tmp_path):
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    window = _open_reader_window(qtbot, data_root)
    return window, data_root


@pytest.fixture
def reader_window_two_texts(qtbot, tmp_path):
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    _seed_second_text(data_root)
    window = _open_reader_window(qtbot, data_root)
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
    assert mode_stack.currentIndex() == 0
    assert "Cuerpo traducido" in read_pane.toPlainText()
    assert "Traducción" in read_pane.toPlainText()


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


def test_edit_mode_updates_preview_before_save(reader_window, qtbot) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    preview_pane = window.reader.findChild(QTextBrowser, "reader_edit_preview_pane")
    assert edit_button is not None
    assert edit_pane is not None
    assert preview_pane is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\n**Live** preview.")
    qtbot.wait(50)

    assert "Live" in preview_pane.toPlainText()
    assert "preview" in preview_pane.toPlainText()
    assert "Traducción" in preview_pane.toPlainText()
    assert "**Live**" not in preview_pane.toPlainText()


def test_read_mode_shows_library_title_label(reader_window, qtbot) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    library_title = window.reader.findChild(QLabel, "reader_library_title")
    title_edit = window.reader.findChild(QLineEdit, "reader_title_edit")
    assert library_title is not None and title_edit is not None
    assert library_title.isVisible()
    assert not title_edit.isVisible()
    assert library_title.text() == "Traducción"


def test_edit_mode_shows_save_and_cancel_controls(reader_window, qtbot) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    save_button = window.reader.findChild(QPushButton, "reader_save_button")
    cancel_button = window.reader.findChild(QPushButton, "reader_cancel_button")
    assert edit_button is not None
    assert save_button is not None
    assert cancel_button is not None
    assert edit_button.isVisible()
    assert not save_button.isVisible()
    assert not cancel_button.isVisible()

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)

    assert not edit_button.isVisible()
    assert save_button.isVisible()
    assert cancel_button.isVisible()


def test_cancel_edit_discards_title_and_markdown_changes(reader_window, qtbot) -> None:
    window, data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    save_button = window.reader.findChild(QPushButton, "reader_save_button")
    cancel_button = window.reader.findChild(QPushButton, "reader_cancel_button")
    title_edit = window.reader.findChild(QLineEdit, "reader_title_edit")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    assert (
        edit_button is not None
        and save_button is not None
        and cancel_button is not None
        and title_edit is not None
        and edit_pane is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    title_edit.setText("Discarded title")
    edit_pane.setPlainText("# Discarded\n\nBody.")
    qtbot.mouseClick(cancel_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    library_title = window.reader.findChild(QLabel, "reader_library_title")
    assert library_title is not None
    assert library_title.isVisible()
    assert not title_edit.isVisible()
    assert library_title.text() == "Traducción"
    record = LibraryIndex(data_root).list_by_lang("es")[0]
    saved = variant_path(Path(record.folder), "translated").read_text(encoding="utf-8")
    assert "Discarded" not in saved


def test_save_edit_rejects_invalid_title_in_textbox(
    reader_window, qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    warnings: list[str] = []

    def capture_warning(_parent, _title, message: str) -> None:
        warnings.append(message)

    monkeypatch.setattr(
        "lexiflow_ui.widgets.reader_widget.QMessageBox.warning",
        capture_warning,
    )
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    save_button = window.reader.findChild(QPushButton, "reader_save_button")
    title_edit = window.reader.findChild(QLineEdit, "reader_title_edit")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert (
        edit_button is not None
        and save_button is not None
        and title_edit is not None
        and mode_stack is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    title_edit.setText("Bad # title")
    qtbot.mouseClick(save_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert warnings
    assert mode_stack.currentIndex() == 1
    assert save_button.isVisible()


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


def test_edit_disabled_when_translated_variant_missing(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    repo.create_text(
        CreateTextRequest(
            title="Untitled",
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

    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    assert edit_button is not None
    assert not edit_button.isEnabled()


def test_edit_mode_shows_title_textbox(reader_window, qtbot) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    title_edit = window.reader.findChild(QLineEdit, "reader_title_edit")
    library_title = window.reader.findChild(QLabel, "reader_library_title")
    assert edit_button is not None
    assert title_edit is not None
    assert library_title is not None
    assert library_title.isVisible()
    assert not title_edit.isVisible()

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)

    assert not library_title.isVisible()
    assert title_edit.isVisible()
    assert title_edit.text() == "Traducción"


def test_save_edit_keeps_sidebar_library_title_when_only_markdown_changes(
    reader_window, qtbot
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    save_button = window.reader.findChild(QPushButton, "reader_save_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    assert edit_button is not None and save_button is not None and edit_pane is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Nuevo Título\n\nTexto guardado.")
    qtbot.mouseClick(save_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    sidebar_list = _sidebar_list(window)
    item = sidebar_list.item(0)
    assert item is not None
    assert item.text() == "Traducción"
    library_title = window.reader.findChild(QLabel, "reader_library_title")
    assert library_title is not None
    assert library_title.text() == "Traducción"


def test_save_edit_updates_title_from_title_textbox(reader_window, qtbot) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    save_button = window.reader.findChild(QPushButton, "reader_save_button")
    title_edit = window.reader.findChild(QLineEdit, "reader_title_edit")
    assert edit_button is not None
    assert save_button is not None
    assert title_edit is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    title_edit.setText("Nuevo Título")
    qtbot.mouseClick(save_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    sidebar_list = _sidebar_list(window)
    item = sidebar_list.item(0)
    assert item is not None
    assert item.text() == "Nuevo Título"
    library_title = window.reader.findChild(QLabel, "reader_library_title")
    assert library_title is not None
    assert library_title.text() == "Nuevo Título"


def test_edit_mode_shows_source_url_field_when_missing(reader_window, qtbot) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    source_button = window.reader.findChild(QPushButton, "reader_source_button")
    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    source_url_edit = window.reader.findChild(QLineEdit, "reader_source_url_edit")
    assert source_button is not None
    assert edit_button is not None
    assert source_url_edit is not None
    assert not source_button.isVisible()

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)

    assert source_url_edit.isVisible()
    assert source_url_edit.text() == ""


def test_save_edit_persists_source_url_and_shows_open_button(
    reader_window, qtbot
) -> None:
    window, data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    save_button = window.reader.findChild(QPushButton, "reader_save_button")
    source_url_edit = window.reader.findChild(QLineEdit, "reader_source_url_edit")
    assert edit_button is not None
    assert save_button is not None
    assert source_url_edit is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    source_url_edit.setText("https://example.com/new-article")
    qtbot.mouseClick(save_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    source_button = window.reader.findChild(QPushButton, "reader_source_button")
    assert source_button is not None
    assert source_button.isVisible()

    _, index = LibraryCoordinator.open(data_root)
    record = index.list_by_lang("es")[0]
    assert record.source_url == "https://example.com/new-article"


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


def test_unsaved_tab_switch_cancel_stays_in_edit_mode(reader_window, qtbot) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    translated_tab = window.reader.findChild(QPushButton, "reader_tab_translated")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert (
        edit_button is not None
        and edit_pane is not None
        and native_tab is not None
        and translated_tab is not None
        and mode_stack is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert mode_stack.currentIndex() == 1
    assert window.reader.active_tab_id == TRANSLATED_TAB
    assert translated_tab.isChecked()


def test_unsaved_tab_switch_discard_switches_tab(
    reader_window, qtbot, stub_discard_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert (
        edit_button is not None
        and edit_pane is not None
        and native_tab is not None
        and mode_stack is not None
        and read_pane is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert mode_stack.currentIndex() == 0
    assert window.reader.active_tab_id == NATIVE_TAB
    assert native_tab.isChecked()
    assert "hola" in read_pane.toPlainText()


def test_unsaved_sidebar_switch_cancel_keeps_current_text(
    reader_window_two_texts, qtbot
) -> None:
    window, _data_root = reader_window_two_texts
    _click_sidebar_text_by_title(qtbot, window, "Traducción")

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert edit_button is not None and edit_pane is not None and mode_stack is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    _click_sidebar_text_by_title(qtbot, window, "Segundo")
    qtbot.wait(50)

    assert mode_stack.currentIndex() == 1
    sidebar_list = _sidebar_list(window)
    assert sidebar_list.currentItem() is not None
    assert sidebar_list.currentItem().text() == "Traducción"


def test_unsaved_sidebar_switch_discard_opens_other_text(
    reader_window_two_texts, qtbot, stub_discard_unsaved_prompt
) -> None:
    window, _data_root = reader_window_two_texts
    _click_sidebar_text_by_title(qtbot, window, "Traducción")

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    assert (
        edit_button is not None
        and edit_pane is not None
        and mode_stack is not None
        and read_pane is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    _click_sidebar_text_by_title(qtbot, window, "Segundo")
    qtbot.wait(50)

    assert mode_stack.currentIndex() == 0
    assert "Otro cuerpo traducido" in read_pane.toPlainText()
    sidebar_list = _sidebar_list(window)
    assert sidebar_list.currentItem() is not None
    assert sidebar_list.currentItem().text() == "Segundo"


def test_unsaved_vocabulary_navigation_cancel_stays_in_texts(
    reader_window, qtbot
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    vocabulary_action = window.navigation_action("vocabulary")
    texts_action = window.navigation_action("texts")
    assert (
        edit_button is not None
        and edit_pane is not None
        and mode_stack is not None
        and vocabulary_action is not None
        and texts_action is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    vocabulary_action.trigger()
    qtbot.wait(50)

    assert mode_stack.currentIndex() == 1
    assert texts_action.isChecked()
    assert window.sidebar.isVisible()


def test_clean_edit_tab_switch_does_not_prompt(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert edit_button is not None and native_tab is not None and mode_stack is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert track_unsaved_prompt() == 0
    assert mode_stack.currentIndex() == 0
    assert window.reader.active_tab_id == NATIVE_TAB


def test_title_only_change_prompts_before_tab_switch(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    title_edit = window.reader.findChild(QLineEdit, "reader_title_edit")
    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert (
        edit_button is not None
        and title_edit is not None
        and native_tab is not None
        and mode_stack is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    title_edit.setText("Nuevo título")
    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert track_unsaved_prompt() == 1
    assert mode_stack.currentIndex() == 1


def test_source_url_only_change_prompts_before_tab_switch(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    source_url_edit = window.reader.findChild(QLineEdit, "reader_source_url_edit")
    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert (
        edit_button is not None
        and source_url_edit is not None
        and native_tab is not None
        and mode_stack is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    source_url_edit.setText("https://example.com/article")
    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert track_unsaved_prompt() == 1
    assert mode_stack.currentIndex() == 1


def test_cancel_edit_does_not_prompt(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    cancel_button = window.reader.findChild(QPushButton, "reader_cancel_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    assert edit_button is not None
    assert cancel_button is not None
    assert edit_pane is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    qtbot.mouseClick(cancel_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert track_unsaved_prompt() == 0


def test_save_clears_dirty_before_tab_switch(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    save_button = window.reader.findChild(QPushButton, "reader_save_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    native_tab = window.reader.findChild(QPushButton, "reader_tab_native")
    assert (
        edit_button is not None
        and save_button is not None
        and edit_pane is not None
        and native_tab is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nTexto guardado.")
    qtbot.mouseClick(save_button, Qt.MouseButton.LeftButton)
    qtbot.wait(50)
    qtbot.mouseClick(native_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert track_unsaved_prompt() == 0
    assert window.reader.active_tab_id == NATIVE_TAB


def test_same_tab_click_while_editing_stays_in_edit_mode(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    translated_tab = window.reader.findChild(QPushButton, "reader_tab_translated")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert (
        edit_button is not None
        and translated_tab is not None
        and edit_pane is not None
        and mode_stack is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    qtbot.mouseClick(translated_tab, Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert track_unsaved_prompt() == 0
    assert mode_stack.currentIndex() == 1


def test_reclick_same_sidebar_text_while_editing_stays_in_edit_mode(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert edit_button is not None and edit_pane is not None and mode_stack is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    _click_sidebar_text(qtbot, window)
    qtbot.wait(50)

    assert track_unsaved_prompt() == 0
    assert mode_stack.currentIndex() == 1


def test_close_window_cancel_keeps_window_open(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    assert edit_button is not None and edit_pane is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    window.close()
    qtbot.wait(50)

    assert track_unsaved_prompt() == 1
    assert window.isVisible()


def test_add_text_cancel_keeps_edit_mode(
    reader_window, qtbot, track_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    mode_stack = window.reader.findChild(QStackedWidget, "reader_mode_stack")
    assert edit_button is not None and edit_pane is not None and mode_stack is not None

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    window.add_text_action().trigger()
    qtbot.wait(50)

    assert track_unsaved_prompt() == 1
    assert mode_stack.currentIndex() == 1


def test_unsaved_vocabulary_navigation_discard_leaves_texts(
    reader_window, qtbot, stub_discard_unsaved_prompt
) -> None:
    window, _data_root = reader_window
    _click_sidebar_text(qtbot, window)

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    vocabulary_action = window.navigation_action("vocabulary")
    assert (
        edit_button is not None
        and edit_pane is not None
        and vocabulary_action is not None
    )

    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)
    edit_pane.setPlainText("# Traducción\n\nCambio sin guardar.")
    vocabulary_action.trigger()
    qtbot.wait(50)

    assert not window.sidebar.isVisible()
    assert vocabulary_action.isChecked()


def test_open_source_url_opens_in_browser(
    qtbot, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[str] = []

    def capture_open(url) -> None:
        opened.append(url.toString())

    monkeypatch.setattr(
        "lexiflow_ui.widgets.reader_widget.QDesktopServices.openUrl",
        capture_open,
    )
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root, source_url="https://example.com/article")
    window = _open_reader_window(qtbot, data_root)
    _click_sidebar_text(qtbot, window)

    source_button = window.reader.findChild(QPushButton, "reader_source_button")
    assert source_button is not None
    qtbot.mouseClick(source_button, Qt.MouseButton.LeftButton)

    assert opened == ["https://example.com/article"]


def test_reader_applies_font_size_from_settings(qtbot, tmp_path) -> None:
    data_root = tmp_path / "LexiFlow"
    _seed_reader_text(data_root)
    supervisor = WorkerSupervisor(data_root=data_root)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(
            data_root=data_root,
            active_target_language="es",
            native_language="en",
            reader_font_size=22,
        ),
        data_root=data_root,
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    _click_sidebar_text(qtbot, window)

    read_pane = window.reader.findChild(QTextBrowser, "reader_read_pane")
    edit_pane = window.reader.findChild(QPlainTextEdit, "reader_edit_pane")
    assert read_pane is not None and edit_pane is not None
    assert read_pane.font().pointSize() == 22

    edit_button = window.reader.findChild(QPushButton, "reader_edit_button")
    assert edit_button is not None
    qtbot.mouseClick(edit_button, Qt.MouseButton.LeftButton)

    assert edit_pane.font().pointSize() == 22
