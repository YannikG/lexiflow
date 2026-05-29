"""Pure path calculations for LexiFlow on disk."""

from __future__ import annotations

import os
import sys
from pathlib import Path

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


def ensure_app_layout(data_root: Path) -> None:
    """Create runtime directories under the user library data root."""
    (data_root / ".app").mkdir(parents=True, exist_ok=True)
    (data_root / ".app" / "logs").mkdir(parents=True, exist_ok=True)


def language_data_root(data_root: Path, language_code: str) -> Path:
    """Return the per-target-language folder (stub for later phases)."""
    return data_root / language_code
