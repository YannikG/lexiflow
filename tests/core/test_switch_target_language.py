"""Tests for switching the active target language."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.store import LanguageStore
from lexiflow_core.languages.switch_target import (
    SwitchTargetLanguageError,
    switch_active_target,
)


def test_switch_active_target_persists_settings(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    config_dir = tmp_path / "config"
    store = SettingsStore(config_dir=config_dir)
    LanguageStore(data_root).add_target("es")
    LanguageStore(data_root).add_target("de")
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    store.save(settings)

    updated = switch_active_target(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        target_language="de",
    )

    assert updated.active_target_language == "de"
    assert store.load().active_target_language == "de"


def test_switch_active_target_rejects_native_language(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    config_dir = tmp_path / "config"
    store = SettingsStore(config_dir=config_dir)
    LanguageStore(data_root).add_target("en")
    settings = Settings(
        data_root=data_root,
        native_language="en",
        active_target_language="es",
        onboarding_complete=True,
    )
    store.save(settings)

    with pytest.raises(SwitchTargetLanguageError, match="must differ"):
        switch_active_target(
            data_root=data_root,
            settings_store=store,
            settings=settings,
            target_language="en",
        )


def test_switch_active_target_requires_existing_target(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    config_dir = tmp_path / "config"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, active_target_language="es")

    with pytest.raises(SwitchTargetLanguageError, match="not found"):
        switch_active_target(
            data_root=data_root,
            settings_store=store,
            settings=settings,
            target_language="de",
        )
