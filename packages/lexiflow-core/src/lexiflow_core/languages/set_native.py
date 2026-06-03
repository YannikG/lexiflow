"""Update the user's native language in global settings."""

from __future__ import annotations

from dataclasses import replace

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore


class SetNativeLanguageError(Exception):
    """Raised when the native language cannot be updated."""


def set_native_language(
    *,
    settings_store: SettingsStore,
    settings: Settings,
    native_language: str,
) -> Settings:
    """Persist a new native language."""
    iso = native_language.strip()
    if not iso:
        raise SetNativeLanguageError("native language is required")
    active = settings.active_target_language
    if active is not None and iso == active:
        raise SetNativeLanguageError(
            "native language must differ from the active target language"
        )
    updated = replace(settings, native_language=iso)
    try:
        settings_store.save(updated)
    except Exception as exc:
        raise SetNativeLanguageError("failed to save settings") from exc
    return updated
