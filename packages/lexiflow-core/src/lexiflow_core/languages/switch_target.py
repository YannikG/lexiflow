"""Switch the active target language in global settings."""

from __future__ import annotations

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
    updated = Settings(
        data_root=settings.data_root,
        native_language=settings.native_language,
        active_target_language=target_language,
        onboarding_complete=settings.onboarding_complete,
        ollama_url=settings.ollama_url,
        llama_server_url=settings.llama_server_url,
        huggingface_token=settings.huggingface_token,
        llm_enabled=settings.llm_enabled,
        theme=settings.theme,
        reader_font_size=settings.reader_font_size,
    )
    try:
        settings_store.save(updated)
    except Exception as exc:
        raise SwitchTargetLanguageError("failed to save settings") from exc
    return updated
