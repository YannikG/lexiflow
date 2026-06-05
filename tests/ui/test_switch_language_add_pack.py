"""Tests for add-language flow with in-dialog spaCy pack install."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.setup import add_target_language
from lexiflow_core.languages.spacy_pack import SpacyPackError
from lexiflow_core.vocabulary.lemma_resolution import spacy_pack_available
from lexiflow_ui.spacy_pack_install import install_spacy_pack_with_progress
from lexiflow_ui.switch_language_flow import open_switch_language_dialog
from PySide6.QtWidgets import QWidget

from tests.spacy_pack_fakes import fake_ensure_model, fake_load_model


def test_add_language_installs_pack_no_background_job(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "library"
    config_dir = tmp_path / "config"
    add_target_language(data_root, "es")
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    SettingsStore(config_dir=config_dir).save(settings)
    switched: list[Settings] = []

    class FakeDialog:
        DialogCode = type("DialogCode", (), {"Accepted": 1})

        def __init__(self, **_kwargs) -> None:
            self._add_mode = True

        @property
        def is_add_language(self) -> bool:
            return True

        @property
        def selected_iso(self) -> str:
            return "de"

        def exec(self) -> int:
            return 1

    monkeypatch.setattr(
        "lexiflow_ui.switch_language_flow.SwitchLanguageDialog",
        FakeDialog,
    )

    def install_pack(parent, *, data_root: Path, iso: str, **_kwargs) -> bool:
        return install_spacy_pack_with_progress(
            parent,
            data_root=data_root,
            iso=iso,
            ensure_model=fake_ensure_model,
            load_model=fake_load_model,
        )

    parent = QWidget()
    qtbot.addWidget(parent)
    open_switch_language_dialog(
        parent,
        data_root=data_root,
        settings=settings,
        settings_store=SettingsStore(config_dir=config_dir),
        on_switched=switched.append,
        install_spacy_pack=install_pack,
    )

    assert JobService(data_root).list_jobs() == []
    assert spacy_pack_available(data_root, "de")
    assert len(switched) == 1
    assert switched[0].active_target_language == "de"


def test_add_language_install_failure_discards_target(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "library"
    config_dir = tmp_path / "config"
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    SettingsStore(config_dir=config_dir).save(settings)
    switched: list[Settings] = []

    class FakeDialog:
        DialogCode = type("DialogCode", (), {"Accepted": 1})

        def __init__(self, **_kwargs) -> None:
            self._add_mode = True

        @property
        def is_add_language(self) -> bool:
            return True

        @property
        def selected_iso(self) -> str:
            return "de"

        def exec(self) -> int:
            return 1

    monkeypatch.setattr(
        "lexiflow_ui.switch_language_flow.SwitchLanguageDialog",
        FakeDialog,
    )
    monkeypatch.setattr(
        "lexiflow_ui.switch_language_flow.QMessageBox.critical",
        lambda *_args, **_kwargs: None,
    )

    def failing_install(parent, *, data_root: Path, iso: str, **_kwargs) -> bool:
        return install_spacy_pack_with_progress(
            parent,
            data_root=data_root,
            iso=iso,
            ensure_model=lambda _name: (_ for _ in ()).throw(
                SpacyPackError("download failed")
            ),
            load_model=fake_load_model,
        )

    parent = QWidget()
    qtbot.addWidget(parent)
    open_switch_language_dialog(
        parent,
        data_root=data_root,
        settings=settings,
        settings_store=SettingsStore(config_dir=config_dir),
        on_switched=switched.append,
        install_spacy_pack=failing_install,
    )

    assert switched == []
    assert not spacy_pack_available(data_root, "de")
