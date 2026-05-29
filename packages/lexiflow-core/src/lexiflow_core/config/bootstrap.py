"""Startup orchestration for settings and library layout."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import ensure_app_layout
from lexiflow_core.config.settings import SettingsStore, resolve_data_root


def bootstrap_runtime(settings_store: SettingsStore | None = None) -> Path:
    """Load settings, resolve the data root, and ensure runtime layout exists."""
    store = settings_store if settings_store is not None else SettingsStore()
    settings = store.load()
    data_root = resolve_data_root(settings)
    ensure_app_layout(data_root)
    return data_root
