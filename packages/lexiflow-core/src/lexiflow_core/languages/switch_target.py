"""Switch the active target language in global settings."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.store import LanguageStore


class SwitchTargetLanguageError(Exception):
    """Raised when the active target language cannot be switched."""


def switch_active_target(
    *,
    data_root: Path,
    settings_store: SettingsStore,
    settings: Settings,
    target_language: str,
) -> Settings:
    """Persist a new active target language."""
    store = LanguageStore(data_root)
    if not store.has_target(target_language):
        raise SwitchTargetLanguageError(f"target language not found: {target_language}")
    native = settings.native_language
    if native is not None and target_language == native:
        raise SwitchTargetLanguageError(
            "target language must differ from the native language"
        )
    updated = replace(settings, active_target_language=target_language)
    try:
        settings_store.save(updated)
    except Exception as exc:
        raise SwitchTargetLanguageError("failed to save settings") from exc
    return updated
