"""Factory reset of local application data."""

from __future__ import annotations

import shutil
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore


class AppResetError(Exception):
    """Raised when factory reset cannot complete."""


def reset_local_app(
    *,
    data_root: Path,
    settings_store: SettingsStore,
) -> Settings:
    """Delete library data under data_root and reset global settings."""
    if data_root.is_dir():
        try:
            for child in data_root.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        except OSError as exc:
            raise AppResetError(f"failed to delete data under {data_root}") from exc
    cleared = Settings(data_root=data_root, onboarding_complete=False)
    try:
        settings_store.save(cleared)
    except OSError as exc:
        raise AppResetError("failed to save settings after reset") from exc
    return cleared
