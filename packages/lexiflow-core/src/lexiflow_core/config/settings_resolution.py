"""Resolve effective library paths from global settings."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import default_data_root
from lexiflow_core.config.settings import Settings


def resolve_data_root(settings: Settings) -> Path:
    """Return the effective data root from settings or the default."""
    if settings.data_root is not None:
        return settings.data_root.expanduser().resolve()
    return default_data_root()
