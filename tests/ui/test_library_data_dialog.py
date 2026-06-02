"""Library data dialog tests."""

from __future__ import annotations

from lexiflow_core.config.settings import Settings
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_ui.dialogs.library_data_dialog import LibraryDataDialog
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


def test_library_data_dialog_rebuilds_index(qtbot, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.dialogs.library_data_dialog.QMessageBox.information",
        lambda *args, **kwargs: None,
    )
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window._text_repository.create_text(
        CreateTextRequest(
            title="Indexed",
            group="News",
            target_language="es",
            native_language="en",
        )
    )
    dialog = LibraryDataDialog(
        data_root=window.data_root,
        text_repository=window._text_repository,
        library_index=window._library_index,
        parent=window,
    )
    qtbot.addWidget(dialog)

    rebuild_button = next(
        button
        for button in dialog.findChildren(QPushButton)
        if button.text() == "Rebuild library index"
    )
    qtbot.mouseClick(rebuild_button, Qt.MouseButton.LeftButton)

    assert len(window._library_index.list_by_lang("es")) == 1


def test_file_menu_opens_library_data_dialog(qtbot, tmp_path, monkeypatch) -> None:
    opened: list[bool] = []

    def fake_open(_parent, **_kwargs: object) -> None:
        opened.append(True)

    monkeypatch.setattr("lexiflow_ui.main_window.open_library_data_dialog", fake_open)
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    window._library_data_action.trigger()

    assert opened == [True]
