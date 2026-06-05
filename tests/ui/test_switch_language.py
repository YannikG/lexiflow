"""Tests for switching the active target language."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.store import LanguageStore
from lexiflow_core.languages.switch_target import switch_active_target
from lexiflow_core.library.index import LibraryIndex, ensure_library_index
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget


def _seed_text(data_root: Path, *, language: str, title: str) -> None:
    ensure_library_index(data_root)
    index = LibraryIndex(data_root)
    repo = TextRepository(data_root, index)
    repo.create_text(
        CreateTextRequest(
            title=title,
            group="News",
            target_language=language,
            native_language="en",
            body="# Hello\n\nBody.",
        )
    )


def test_switch_language_refreshes_sidebar_for_active_target(
    qtbot, tmp_path: Path
) -> None:
    data_root = tmp_path / "LexiFlow"
    config_dir = tmp_path / "config"
    LanguageStore(data_root).add_target("es")
    LanguageStore(data_root).add_target("de")
    _seed_text(data_root, language="es", title="Spanish text")
    _seed_text(data_root, language="de", title="German text")

    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    SettingsStore(config_dir=config_dir).save(settings)

    supervisor = WorkerSupervisor(data_root=data_root)
    window = MainWindow(
        supervisor=supervisor,
        settings=settings,
        data_root=data_root,
    )
    qtbot.addWidget(window)

    assert any(
        window.sidebar._list.item(row).text() == "Spanish text"
        for row in range(window.sidebar._list.count())
    )

    updated = switch_active_target(
        data_root=data_root,
        settings_store=SettingsStore(config_dir=config_dir),
        settings=settings,
        target_language="de",
    )
    window._on_active_language_changed(updated)

    titles = [
        window.sidebar._list.item(row).text()
        for row in range(window.sidebar._list.count())
    ]
    assert "German text" in titles
    assert "Spanish text" not in titles
    assert window._settings.active_target_language == "de"


def test_switch_to_empty_language_closes_reader(qtbot, tmp_path: Path) -> None:
    """After add-language, a text from the previous language must not stay visible."""
    data_root = tmp_path / "LexiFlow"
    config_dir = tmp_path / "config"
    LanguageStore(data_root).add_target("es")
    LanguageStore(data_root).add_target("fr")
    _seed_text(data_root, language="es", title="Spanish text")

    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    SettingsStore(config_dir=config_dir).save(settings)

    supervisor = WorkerSupervisor(data_root=data_root)
    window = MainWindow(
        supervisor=supervisor,
        settings=settings,
        data_root=data_root,
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

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
    assert window._open_text_id is not None
    assert window._texts_stack.currentWidget() is window._reader

    updated = switch_active_target(
        data_root=data_root,
        settings_store=SettingsStore(config_dir=config_dir),
        settings=settings,
        target_language="fr",
    )
    window._on_active_language_changed(updated)

    assert window._settings.active_target_language == "fr"
    assert window._open_text_id is None
    assert window._texts_stack.currentWidget() is window._texts_view
    assert window._reader._record is None
