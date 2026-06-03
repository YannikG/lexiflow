"""Tests for native language settings updates."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.set_native import (
    SetNativeLanguageError,
    set_native_language,
)


def test_set_native_language_persists_iso(tmp_path: Path) -> None:
    store = SettingsStore(config_dir=tmp_path / "config")
    settings = Settings(
        data_root=tmp_path / "library",
        native_language="en",
        active_target_language="es",
    )
    store.save(settings)

    updated = set_native_language(
        settings_store=store,
        settings=settings,
        native_language="de",
    )

    assert updated.native_language == "de"
    assert store.load().native_language == "de"


def test_set_native_language_rejects_target_match(tmp_path: Path) -> None:
    store = SettingsStore(config_dir=tmp_path / "config")
    settings = Settings(
        data_root=tmp_path / "library",
        native_language="en",
        active_target_language="de",
    )

    with pytest.raises(SetNativeLanguageError, match="must differ"):
        set_native_language(
            settings_store=store,
            settings=settings,
            native_language="de",
        )
