"""Trash dialog and library options menu tests."""

from __future__ import annotations

from lexiflow_core.config.settings import Settings
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.vocabulary.store import VocabularyStore
from lexiflow_ui.library_options_flow import rebuild_library_index
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QPushButton, QTabWidget


def _menu_action_labels(menu: QMenu) -> list[str]:
    return [
        action.text()
        for action in menu.actions()
        if action.text() and not action.isSeparator()
    ]


def test_library_and_options_menu_layout(qtbot, tmp_path) -> None:
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)

    top_level: list[str] = []
    library_labels: list[str] = []
    options_labels: list[str] = []
    for action in window.menuBar().actions():
        menu = action.menu()
        if menu is None:
            continue
        label = action.text().replace("&", "")
        top_level.append(label)
        labels = _menu_action_labels(menu)
        if label == "Library":
            library_labels = labels
        elif label == "Options":
            options_labels = labels

    assert top_level == ["Texts", "Library", "Settings", "Options"]
    assert library_labels == ["Switch language…", "Trash…"]
    assert options_labels == [
        "Export library…",
        "Restore library to new folder…",
        "Replace current library…",
        "Rebuild library index",
        "Export vocabulary…",
        "Import vocabulary…",
        "Delete language…",
    ]


def test_delete_language_opens_switch_language_dialog(
    qtbot, tmp_path, monkeypatch
) -> None:
    opened: list[bool] = []

    def fake_remove(*_args: object, **_kwargs: object) -> Settings:
        return Settings(active_target_language=None, native_language="en")

    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    monkeypatch.setattr(
        "lexiflow_ui.main_window._shell_dialogs.offer_remove_target_language",
        fake_remove,
    )
    monkeypatch.setattr(
        window,
        "_open_switch_language_dialog",
        lambda: opened.append(True),
    )

    window._remove_target_language()

    assert opened == [True]


def test_delete_language_does_not_open_switch_dialog_when_cancelled(
    qtbot, tmp_path, monkeypatch
) -> None:
    opened: list[bool] = []

    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    monkeypatch.setattr(
        "lexiflow_ui.main_window._shell_dialogs.offer_remove_target_language",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        window,
        "_open_switch_language_dialog",
        lambda: opened.append(True),
    )

    window._remove_target_language()

    assert opened == []


def test_rebuild_library_index_from_options(qtbot, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "lexiflow_ui.library_options_flow.QMessageBox.information",
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

    rebuild_library_index(
        parent=window,
        data_root=window.data_root,
        library_index=window._library_index,
        language_code="es",
    )

    assert len(window._library_index.list_by_lang("es")) == 1


def test_rebuild_library_index_message_scopes_trash_to_language(
    qtbot, tmp_path, monkeypatch
) -> None:
    messages: list[str] = []

    def capture_message(_parent, _title, message: str) -> None:
        messages.append(message)

    monkeypatch.setattr(
        "lexiflow_ui.library_options_flow.QMessageBox.information",
        capture_message,
    )
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    active = window._text_repository.create_text(
        CreateTextRequest(
            title="Active",
            group="News",
            target_language="es",
            native_language="en",
        )
    )
    trashed = window._text_repository.create_text(
        CreateTextRequest(
            title="Trashed",
            group="News",
            target_language="es",
            native_language="en",
        )
    )
    german = window._text_repository.create_text(
        CreateTextRequest(
            title="German trash",
            group="News",
            target_language="de",
            native_language="en",
        )
    )
    window._text_repository.delete_to_trash(trashed.id)
    window._text_repository.delete_to_trash(german.id)

    rebuild_library_index(
        parent=window,
        data_root=window.data_root,
        library_index=window._library_index,
        language_code="es",
    )

    assert len(messages) == 1
    assert "1 active text(s) for ES" in messages[0]
    assert "1 trashed text(s) for ES" in messages[0]
    assert "DE" not in messages[0]
    listed = window._library_index.list_by_lang("es")
    assert active.id in {record.id for record in listed}


def test_library_menu_opens_trash_dialog(qtbot, tmp_path, monkeypatch) -> None:
    opened: list[bool] = []

    def fake_open(_parent, **_kwargs: object) -> None:
        opened.append(True)

    monkeypatch.setattr(
        "lexiflow_ui.main_window._shell_dialogs.open_trash_dialog",
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

    window._trash_action.trigger()

    assert opened == [True]


def test_trash_dialog_has_text_and_vocabulary_tabs(
    qtbot, tmp_path, monkeypatch
) -> None:
    from lexiflow_ui.dialogs.trash_dialog import TrashDialog

    monkeypatch.setattr(
        "lexiflow_ui.dialogs.trash_dialog.QMessageBox.information",
        lambda *args, **kwargs: None,
    )
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)

    dialog = TrashDialog(
        data_root=window.data_root,
        language_code="es",
        text_repository=window._text_repository,
        parent=window,
    )
    qtbot.addWidget(dialog)

    tabs = dialog.findChild(QTabWidget, "trash_tabs")
    assert tabs is not None
    assert tabs.tabText(0) == "Texts"
    assert tabs.tabText(1) == "Vocabulary"


def test_trash_dialog_lists_only_active_language_texts(
    qtbot, tmp_path, monkeypatch
) -> None:
    from lexiflow_ui.dialogs.trash_dialog import TrashDialog

    monkeypatch.setattr(
        "lexiflow_ui.dialogs.trash_dialog.QMessageBox.information",
        lambda *args, **kwargs: None,
    )
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    es = window._text_repository.create_text(
        CreateTextRequest(
            title="Spanish",
            group="News",
            target_language="es",
            native_language="en",
        )
    )
    de = window._text_repository.create_text(
        CreateTextRequest(
            title="German",
            group="News",
            target_language="de",
            native_language="en",
        )
    )
    window._text_repository.delete_to_trash(es.id)
    window._text_repository.delete_to_trash(de.id)

    dialog = TrashDialog(
        data_root=window.data_root,
        language_code="es",
        text_repository=window._text_repository,
        parent=window,
    )
    qtbot.addWidget(dialog)

    assert dialog._texts_list.count() == 1
    assert "Spanish" in dialog._texts_list.item(0).text()


def test_trash_dialog_rebuilds_list_after_restore(qtbot, tmp_path, monkeypatch) -> None:
    from lexiflow_ui.dialogs.trash_dialog import TrashDialog

    monkeypatch.setattr(
        "lexiflow_ui.dialogs.trash_dialog.QMessageBox.information",
        lambda *args, **kwargs: None,
    )
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    text = window._text_repository.create_text(
        CreateTextRequest(
            title="Trashed",
            group="News",
            target_language="es",
            native_language="en",
        )
    )
    window._text_repository.delete_to_trash(text.id)

    dialog = TrashDialog(
        data_root=window.data_root,
        language_code="es",
        text_repository=window._text_repository,
        parent=window,
    )
    qtbot.addWidget(dialog)

    restore_button = next(
        button
        for button in dialog.findChildren(QPushButton)
        if button.text() == "Restore selected"
    )
    dialog._texts_list.setCurrentRow(0)
    qtbot.mouseClick(restore_button, Qt.MouseButton.LeftButton)

    assert window._text_repository.list_trash(language_code="es") == []


def test_trash_restore_vocabulary_schedules_embed(qtbot, tmp_path, monkeypatch) -> None:
    from lexiflow_core.jobs.models import JobType
    from lexiflow_core.jobs.service import JobService
    from lexiflow_ui.dialogs.trash_dialog import TrashDialog

    monkeypatch.setattr(
        "lexiflow_ui.dialogs.trash_dialog.QMessageBox.information",
        lambda *args, **kwargs: None,
    )
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    VocabularyStore(window.data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    VocabularyStore(window.data_root, "es").delete_entry("correr")

    dialog = TrashDialog(
        data_root=window.data_root,
        language_code="es",
        text_repository=window._text_repository,
        supervisor=supervisor,
        parent=window,
    )
    qtbot.addWidget(dialog)
    dialog._tabs.setCurrentIndex(1)
    dialog._vocabulary_list.setCurrentRow(0)

    restore_button = next(
        button
        for button in dialog.findChildren(QPushButton)
        if button.text() == "Restore selected"
    )
    qtbot.mouseClick(restore_button, Qt.MouseButton.LeftButton)

    jobs = JobService(window.data_root).list_jobs()
    assert len(jobs) == 1
    assert jobs[0].job_type == JobType.EMBED
    assert jobs[0].payload == {"language_code": "es", "lemma": "correr"}


def test_trash_dialog_lists_deleted_vocabulary(qtbot, tmp_path, monkeypatch) -> None:
    from lexiflow_ui.dialogs.trash_dialog import TrashDialog

    monkeypatch.setattr(
        "lexiflow_ui.dialogs.trash_dialog.QMessageBox.information",
        lambda *args, **kwargs: None,
    )
    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    VocabularyStore(window.data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    VocabularyStore(window.data_root, "es").delete_entry("correr")

    dialog = TrashDialog(
        data_root=window.data_root,
        language_code="es",
        text_repository=window._text_repository,
        parent=window,
    )
    qtbot.addWidget(dialog)
    dialog._tabs.setCurrentIndex(1)

    assert dialog._vocabulary_list.count() == 1
    assert "correr" in dialog._vocabulary_list.item(0).text()
