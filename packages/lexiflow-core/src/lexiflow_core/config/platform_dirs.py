"""OS-specific application config directory resolution."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from lexiflow_core.config.paths import APP_DATA_NAME


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
