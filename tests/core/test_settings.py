"""Tests for lexiflow_core.config.settings and related modules."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings, SettingsError
from lexiflow_core.config.settings_resolution import resolve_data_root
from lexiflow_core.config.settings_store import SettingsStore


def test_settings_round_trip_native_language(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(native_language="de", data_root=data_root)

    store.save(settings)
    loaded = store.load()

    assert loaded.native_language == "de"
    assert store.settings_path == config_dir / "settings.toml"
    assert store.settings_path.is_file()
    assert not (data_root / "settings.toml").exists()


def test_resolve_data_root_expands_tilde(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("USERPROFILE", raising=False)

    settings = Settings(data_root=Path("~/custom-library"))

    assert resolve_data_root(settings) == (tmp_path / "custom-library").resolve()


def test_settings_load_returns_defaults_when_missing(tmp_path: Path) -> None:
    store = SettingsStore(config_dir=tmp_path / "config")

    loaded = store.load()

    assert loaded == Settings()


def test_settings_load_raises_on_corrupt_file(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    store = SettingsStore(config_dir=config_dir)
    (config_dir / "settings.toml").write_text("not valid toml {{{", encoding="utf-8")

    with pytest.raises(SettingsError, match="invalid settings.toml"):
        store.load()


def test_settings_load_raises_on_read_error(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    store = SettingsStore(config_dir=config_dir)
    settings_file = config_dir / "settings.toml"
    settings_file.write_text('native_language = "de"\n', encoding="utf-8")
    settings_file.chmod(0o000)
    try:
        with pytest.raises(SettingsError, match="failed to read settings.toml"):
            store.load()
    finally:
        settings_file.chmod(0o644)


def test_settings_save_raises_on_write_error(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_dir.chmod(0o500)
    store = SettingsStore(config_dir=config_dir)
    try:
        with pytest.raises(SettingsError, match="failed to save settings"):
            store.save(Settings(native_language="de"))
    finally:
        config_dir.chmod(0o700)


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
