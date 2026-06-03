"""Tests for factory reset of local application data."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.app_reset import reset_local_app
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore


def test_reset_local_app_clears_data_root_and_onboarding(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    data_root.mkdir()
    (data_root / "es").mkdir()
    (data_root / ".app").mkdir()
    (data_root / ".app" / "models").mkdir()
    (data_root / "marker.txt").write_text("x", encoding="utf-8")

    store = SettingsStore(config_dir=config_dir)
    store.save(
        Settings(
            data_root=data_root,
            native_language="en",
            active_target_language="es",
            onboarding_complete=True,
        )
    )

    cleared = reset_local_app(data_root=data_root, settings_store=store)

    assert cleared.onboarding_complete is False
    assert cleared.native_language is None
    assert cleared.active_target_language is None
    assert list(data_root.iterdir()) == []
    assert store.load().onboarding_complete is False
