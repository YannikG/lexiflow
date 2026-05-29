"""Tests for lexiflow_core.config.paths."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.bootstrap import bootstrap_runtime
from lexiflow_core.config.paths import (
    app_config_dir,
    default_data_root,
    ensure_app_layout,
    language_data_root,
)
from lexiflow_core.config.settings import Settings, SettingsStore


def test_default_data_root_is_lexiflow_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("USERPROFILE", raising=False)

    assert default_data_root() == (tmp_path / "LexiFlow").resolve()


def test_ensure_app_layout_creates_dot_app(tmp_path: Path) -> None:
    data_root = tmp_path / "library"

    ensure_app_layout(data_root)
    ensure_app_layout(data_root)

    assert (data_root / ".app").is_dir()
    assert (data_root / ".app" / "logs").is_dir()


def test_app_config_dir_is_absolute() -> None:
    config_dir = app_config_dir()

    assert config_dir.is_absolute()


def test_language_data_root_returns_language_folder(tmp_path: Path) -> None:
    assert language_data_root(tmp_path, "de") == tmp_path / "de"


def test_app_config_dir_uses_app_data_name_on_linux(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("lexiflow_core.config.paths.sys.platform", "linux")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    assert app_config_dir() == (tmp_path / ".config" / "LexiFlow").resolve()


def test_bootstrap_runtime_ensures_app_layout(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    store.save(Settings(data_root=data_root))

    resolved = bootstrap_runtime(store)

    assert resolved == data_root.resolve()
    assert (data_root / ".app" / "logs").is_dir()
