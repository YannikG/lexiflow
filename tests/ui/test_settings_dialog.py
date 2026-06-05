"""Settings dialog behavior."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.models.download import FakeModelDownloader
from lexiflow_core.models.lockfile import load_models_lock
from lexiflow_core.models.paths import artifact_revision_path
from lexiflow_core.models.store import ModelStore
from lexiflow_ui.dialogs.settings_dialog import SettingsDialog
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.onboarding.ollama_probe import FakeOllamaProbe
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMenu,
    QProgressDialog,
    QPushButton,
    QRadioButton,
    QSpinBox,
)


def _options_menu(window: MainWindow) -> QMenu | None:
    for action in window.menuBar().actions():
        menu = action.menu()
        if menu is not None and action.text().replace("&", "") == "Options":
            return menu
    return None


def _click_save(dialog: SettingsDialog, qtbot) -> None:
    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    save = box.button(QDialogButtonBox.StandardButton.Save)
    assert save is not None
    qtbot.mouseClick(save, Qt.MouseButton.LeftButton)


def test_settings_dialog_opens_from_options_menu(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def immediate_close(self: SettingsDialog) -> int:
        return int(QDialog.DialogCode.Rejected)

    monkeypatch.setattr(SettingsDialog, "exec", immediate_close)

    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
        data_root=tmp_path,
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    window._settings_action.trigger()
    dialog = window.findChild(QDialog, "settings_dialog")
    assert dialog is not None


def test_settings_save_persists_provider_and_theme(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    store.save(
        Settings(
            data_root=data_root,
            active_target_language="es",
            native_language="en",
            theme="light",
        )
    )
    apply_calls: list[str] = []

    def track_apply(app: QApplication, *, theme: str) -> None:
        apply_calls.append(theme)

    monkeypatch.setattr(
        "lexiflow_ui.dialogs.settings_dialog.apply_app_theme",
        track_apply,
    )
    monkeypatch.setattr(
        "lexiflow_ui.dialogs.settings_dialog.prompt_restart_lexiflow",
        lambda *_args, **_kwargs: False,
    )

    app = QApplication.instance()
    assert app is not None
    dialog = SettingsDialog(
        app=app,
        settings=store.load(),
        settings_store=store,
        data_root=data_root,
    )
    qtbot.addWidget(dialog)
    dialog.show()

    theme_combo = dialog.findChild(QComboBox, "settings_theme_combo")
    assert theme_combo is not None
    dark_index = theme_combo.findData("dark")
    assert dark_index >= 0
    theme_combo.setCurrentIndex(dark_index)
    ollama_radio = dialog.findChild(QRadioButton, "settings_ollama_radio")
    assert ollama_radio is not None
    ollama_radio.click()
    url = dialog.findChild(QLineEdit, "settings_ollama_url")
    assert url is not None
    url.setText("http://127.0.0.1:11434")

    _click_save(dialog, qtbot)

    loaded = store.load()
    assert loaded.theme == "dark"
    assert loaded.ollama_url == "http://127.0.0.1:11434"
    assert apply_calls == ["dark"]


def test_settings_reader_font_size_persists(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    store.save(
        Settings(
            data_root=data_root,
            active_target_language="es",
            native_language="en",
            reader_font_size=14,
        )
    )
    app = QApplication.instance()
    assert app is not None
    dialog = SettingsDialog(
        app=app,
        settings=store.load(),
        settings_store=store,
        data_root=data_root,
    )
    qtbot.addWidget(dialog)
    spin = dialog.findChild(QSpinBox, "settings_font_size")
    assert spin is not None
    spin.setValue(20)
    _click_save(dialog, qtbot)
    assert store.load().reader_font_size == 20


def test_model_store_upgrade_artifact_updates_marker(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "native-embedding"
repo = "LLukas22/all-MiniLM-L6-v2-GGUF"
revision = "new-pin"
""".strip(),
        encoding="utf-8",
    )
    marker = artifact_revision_path(data_root, "native-embedding")
    marker.parent.mkdir(parents=True)
    marker.write_text("old-pin", encoding="utf-8")
    store = ModelStore(
        data_root=data_root,
        lock=load_models_lock(lock_path),
        downloader=FakeModelDownloader(),
    )

    store.upgrade_artifact("native-embedding", on_progress=lambda *_: None)

    assert marker.read_text(encoding="utf-8") == "new-pin"


def test_test_ollama_connection_updates_status(qtbot, tmp_path: Path) -> None:
    probe = FakeOllamaProbe(available=True)
    app = QApplication.instance()
    assert app is not None
    dialog = SettingsDialog(
        app=app,
        settings=Settings(active_target_language="es", native_language="en"),
        settings_store=SettingsStore(config_dir=tmp_path / "config"),
        data_root=tmp_path / "library",
        ollama_probe=probe,
    )
    qtbot.addWidget(dialog)
    ollama_radio = dialog.findChild(QRadioButton, "settings_ollama_radio")
    assert ollama_radio is not None
    ollama_radio.click()
    test_button = dialog.findChild(QPushButton, "settings_test_ollama")
    assert test_button is not None
    qtbot.mouseClick(test_button, Qt.MouseButton.LeftButton)
    status = dialog.findChild(QLabel, "settings_ollama_status")
    assert status is not None
    assert status.text() == "Ollama is reachable."
    assert probe.last_url == "http://127.0.0.1:11434"


def test_check_model_updates_shows_result_dialog(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown: list[str] = []

    def fake_information(_parent, _title: str, message: str) -> None:
        shown.append(message)

    monkeypatch.setattr(
        "lexiflow_ui.dialogs.settings_dialog.QMessageBox.information",
        fake_information,
    )
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "native-embedding"
repo = "LLukas22/all-MiniLM-L6-v2-GGUF"
revision = "new-pin"
""".strip(),
        encoding="utf-8",
    )
    marker = artifact_revision_path(data_root, "native-embedding")
    marker.parent.mkdir(parents=True)
    marker.write_text("old-pin", encoding="utf-8")
    model_store = ModelStore(
        data_root=data_root,
        lock=load_models_lock(lock_path),
        downloader=FakeModelDownloader(),
    )
    app = QApplication.instance()
    assert app is not None
    dialog = SettingsDialog(
        app=app,
        settings=Settings(active_target_language="es", native_language="en"),
        settings_store=SettingsStore(config_dir=tmp_path / "config"),
        data_root=data_root,
        model_store=model_store,
    )
    qtbot.addWidget(dialog)
    check_button = dialog.findChild(QPushButton, "settings_check_updates")
    assert check_button is not None
    qtbot.mouseClick(check_button, Qt.MouseButton.LeftButton)
    assert shown == ["Updates available: native-embedding"]


def test_redownload_model_when_pins_up_to_date(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    completed: list[tuple[str, str]] = []

    def fake_information(_parent, title: str, message: str) -> None:
        completed.append((title, message))

    monkeypatch.setattr(
        "lexiflow_ui.dialogs.settings_dialog.QMessageBox.information",
        fake_information,
    )
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "native-embedding"
repo = "LLukas22/all-MiniLM-L6-v2-GGUF"
revision = "abc"
""".strip(),
        encoding="utf-8",
    )
    downloader = FakeModelDownloader()
    model_store = ModelStore(
        data_root=data_root,
        lock=load_models_lock(lock_path),
        downloader=downloader,
    )
    model_store.ensure_installed("native-embedding", on_progress=lambda *_: None)
    assert downloader.call_count == 1
    assert model_store.check_for_updates() == []

    app = QApplication.instance()
    assert app is not None
    dialog = SettingsDialog(
        app=app,
        settings=Settings(active_target_language="es", native_language="en"),
        settings_store=SettingsStore(config_dir=tmp_path / "config"),
        data_root=data_root,
        model_store=model_store,
    )
    qtbot.addWidget(dialog)
    redownload = dialog.findChild(QPushButton, "settings_redownload_native-embedding")
    assert redownload is not None
    assert redownload.isEnabled()
    qtbot.mouseClick(redownload, Qt.MouseButton.LeftButton)

    assert downloader.call_count == 2
    assert completed == [("Models re-downloaded", "Embedding model was re-downloaded.")]


def test_model_download_progress_shows_hub_log_line(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    progress_labels: list[str] = []
    original_set_label_text = QProgressDialog.setLabelText

    def track_label_text(self: QProgressDialog, text: str) -> None:
        progress_labels.append(text)
        original_set_label_text(self, text)

    monkeypatch.setattr(QProgressDialog, "setLabelText", track_label_text)
    monkeypatch.setattr(
        "lexiflow_ui.dialogs.settings_dialog.QMessageBox.information",
        lambda *_args, **_kwargs: None,
    )
    data_root = tmp_path / "library"
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "native-embedding"
repo = "LLukas22/all-MiniLM-L6-v2-GGUF"
revision = "abc"
""".strip(),
        encoding="utf-8",
    )
    model_store = ModelStore(
        data_root=data_root,
        lock=load_models_lock(lock_path),
        downloader=FakeModelDownloader(),
    )
    app = QApplication.instance()
    assert app is not None
    dialog = SettingsDialog(
        app=app,
        settings=Settings(active_target_language="es", native_language="en"),
        settings_store=SettingsStore(config_dir=tmp_path / "config"),
        data_root=data_root,
        model_store=model_store,
    )
    qtbot.addWidget(dialog)
    redownload = dialog.findChild(QPushButton, "settings_redownload_native-embedding")
    assert redownload is not None
    qtbot.mouseClick(redownload, Qt.MouseButton.LeftButton)

    assert any(
        "Downloading Embedding model" in label
        and "Installing native-embedding" in label
        for label in progress_labels
    )
