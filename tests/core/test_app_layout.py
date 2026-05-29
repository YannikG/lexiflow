"""Tests for lexiflow_core.config.app_layout and bootstrap."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.app_layout import ensure_app_layout
from lexiflow_core.config.bootstrap import bootstrap_runtime
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore


def test_ensure_app_layout_creates_dot_app(tmp_path: Path) -> None:
    data_root = tmp_path / "library"

    ensure_app_layout(data_root)
    ensure_app_layout(data_root)

    assert (data_root / ".app").is_dir()
    assert (data_root / ".app" / "logs").is_dir()


def test_bootstrap_runtime_ensures_app_layout(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    store.save(Settings(data_root=data_root))

    resolved = bootstrap_runtime(store)

    assert resolved == data_root.resolve()
    assert (data_root / ".app" / "logs").is_dir()
