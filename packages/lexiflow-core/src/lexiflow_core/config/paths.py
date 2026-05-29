"""Data root and app layout path helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lexiflow_core.config.settings import Settings, SettingsStore

APP_DATA_NAME = "LexiFlow"


def app_config_dir() -> Path:
    """Return the machine-local directory for global settings."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_DATA_NAME
        return base.resolve()
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return (Path(appdata) / APP_DATA_NAME).resolve()
        return (Path.home() / "AppData" / "Roaming" / APP_DATA_NAME).resolve()
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return (Path(xdg_config) / APP_DATA_NAME).resolve()
    return (Path.home() / ".config" / APP_DATA_NAME).resolve()


def default_data_root() -> Path:
    """Return the default user library path when settings do not override it."""
    return (Path.home() / APP_DATA_NAME).resolve()


def resolve_data_root(settings: Settings) -> Path:
    """Return the effective data root from settings or the default."""
    if settings.data_root is not None:
        return settings.data_root.expanduser().resolve()
    return default_data_root()


def ensure_app_layout(data_root: Path) -> None:
    """Create runtime directories under the user library data root."""
    (data_root / ".app").mkdir(parents=True, exist_ok=True)
    (data_root / ".app" / "logs").mkdir(parents=True, exist_ok=True)


def language_data_root(data_root: Path, language_code: str) -> Path:
    """Return the per-target-language folder (stub for later phases)."""
    return data_root / language_code


def bootstrap_runtime(
    settings_store: SettingsStore | None = None,
) -> Path:
    """Load settings, resolve the data root, and ensure runtime layout exists."""
    from lexiflow_core.config.settings import SettingsStore as RuntimeSettingsStore

    store = settings_store if settings_store is not None else RuntimeSettingsStore()
    settings = store.load()
    data_root = resolve_data_root(settings)
    ensure_app_layout(data_root)
    return data_root
