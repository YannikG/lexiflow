"""Resolve effective library paths from global settings."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import default_data_root
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore


def resolve_data_root(settings: Settings) -> Path:
    """Return the effective data root from settings or the default."""
    if settings.data_root is not None:
        return settings.data_root.expanduser().resolve()
    return default_data_root()


def resolve_gloss_language(*, fallback: str | None = None) -> str:
    """Return the ISO code for glosses and learner-facing word translations."""
    settings = SettingsStore().load()
    native = settings.native_language
    if native is not None and native.strip():
        return native.strip()
    if fallback is not None and fallback.strip():
        return fallback.strip()
    raise ValueError("native language is not configured")
