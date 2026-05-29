"""Startup orchestration for settings and library layout."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.app_layout import ensure_app_layout
from lexiflow_core.config.settings_resolution import resolve_data_root
from lexiflow_core.config.settings_store import SettingsStore


def bootstrap_runtime(settings_store: SettingsStore | None = None) -> Path:
    """Load settings, resolve the data root, and ensure runtime layout exists."""
    store = settings_store if settings_store is not None else SettingsStore()
    settings = store.load()
    data_root = resolve_data_root(settings)
    ensure_app_layout(data_root)
    return data_root
