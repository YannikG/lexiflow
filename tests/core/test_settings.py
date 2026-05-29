"""Tests for lexiflow_core.config.settings."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.paths import resolve_data_root
from lexiflow_core.config.settings import Settings, SettingsError, SettingsStore


def test_settings_round_trip_native_language(tmp_path: Path) -> None:
    store = SettingsStore(config_dir=tmp_path)
    settings = Settings(native_language="de")

    store.save(settings)
    loaded = store.load()

    assert loaded.native_language == "de"


def test_settings_load_returns_defaults_when_missing(tmp_path: Path) -> None:
    store = SettingsStore(config_dir=tmp_path)

    loaded = store.load()

    assert loaded == Settings()


def test_settings_load_raises_on_corrupt_file(tmp_path: Path) -> None:
    store = SettingsStore(config_dir=tmp_path)
    (tmp_path / "settings.toml").write_text("not valid toml {{{", encoding="utf-8")

    with pytest.raises(SettingsError, match="invalid settings.toml"):
        store.load()


def test_resolve_data_root_uses_settings_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    override = tmp_path / "custom-library"
    settings = Settings(data_root=override)

    assert resolve_data_root(settings) == override.resolve()


def test_resolve_data_root_uses_default_when_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("USERPROFILE", raising=False)

    settings = Settings()

    assert resolve_data_root(settings) == (tmp_path / "LexiFlow").resolve()
