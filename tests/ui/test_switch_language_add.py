"""Tests for add-language flow."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.setup import add_target_language
from lexiflow_ui.switch_language_flow import open_switch_language_dialog
from PySide6.QtWidgets import QWidget


def test_add_language_switches_active_without_background_job(
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

    parent = QWidget()
    qtbot.addWidget(parent)
    open_switch_language_dialog(
        parent,
        data_root=data_root,
        settings=settings,
        settings_store=SettingsStore(config_dir=config_dir),
        on_switched=switched.append,
    )

    assert JobService(data_root).list_jobs() == []
    assert len(switched) == 1
    assert switched[0].active_target_language == "de"
