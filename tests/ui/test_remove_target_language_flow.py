"""UI flow tests for removing a target language."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import language_data_root
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.store import LanguageStore
from lexiflow_core.vocabulary.store import VocabularyStore
from lexiflow_ui.remove_target_language_flow import offer_remove_target_language
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


def test_remove_target_offers_export_before_wipe(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    LanguageStore(data_root).add_target("es")
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    config_dir = tmp_path / "config"
    settings_store = SettingsStore(config_dir)
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    settings_store.save(settings)

    export_prompts: list[str] = []

    def fake_question(_parent, _title, message, *_args, **_kwargs):
        export_prompts.append(message)
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "question", fake_question)
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "PySide6.QtWidgets.QInputDialog.getText",
        lambda *_args, **_kwargs: ("es", True),
    )

    parent = QWidget()
    qtbot.addWidget(parent)
    updated = offer_remove_target_language(
        parent,
        data_root=data_root,
        language_code="es",
        settings=settings,
        settings_store=settings_store,
    )

    assert updated is not None
    assert export_prompts
    assert "Export vocabulary" in export_prompts[0]
    assert not language_data_root(data_root, "es").exists()


def test_remove_target_exports_when_requested(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    LanguageStore(data_root).add_target("es")
    VocabularyStore(data_root, "es").add_entry(
        lemma="correr",
        translation="to run",
        level_when_learned=CEFRLevel.A2,
    )
    config_dir = tmp_path / "config"
    settings_store = SettingsStore(config_dir)
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    settings_store.save(settings)
    export_path = tmp_path / "handoff.zip"

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(export_path), "Zip archives (*.zip)"),
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "PySide6.QtWidgets.QInputDialog.getText",
        lambda *_args, **_kwargs: ("es", True),
    )

    parent = QWidget()
    qtbot.addWidget(parent)
    updated = offer_remove_target_language(
        parent,
        data_root=data_root,
        language_code="es",
        settings=settings,
        settings_store=settings_store,
    )

    assert updated is not None
    assert export_path.is_file()


def test_remove_target_aborts_when_export_dialog_cancelled(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    LanguageStore(data_root).add_target("es")
    config_dir = tmp_path / "config"
    settings_store = SettingsStore(config_dir)
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    settings_store.save(settings)

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: ("", "Zip archives (*.zip)"),
    )

    parent = QWidget()
    qtbot.addWidget(parent)
    updated = offer_remove_target_language(
        parent,
        data_root=data_root,
        language_code="es",
        settings=settings,
        settings_store=settings_store,
    )

    assert updated is None
    assert language_data_root(data_root, "es").exists()
