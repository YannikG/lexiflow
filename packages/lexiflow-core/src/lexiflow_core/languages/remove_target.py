"""Remove a target language and its on-disk library."""

from __future__ import annotations

import shutil
from pathlib import Path

from lexiflow_core.config.paths import language_data_root
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.store import LanguageStore


class RemoveTargetLanguageError(Exception):
    """Raised when a target language cannot be removed."""


def remove_target_language(
    data_root: Path,
    iso: str,
    *,
    settings_store: SettingsStore,
    settings: Settings,
) -> Settings:
    """Delete the target language folder and update global settings."""
    store = LanguageStore(data_root)
    targets = store.list_targets()
    if iso not in targets:
        raise RemoveTargetLanguageError(f"target language not found: {iso}")

    lang_root = language_data_root(data_root, iso)
    if lang_root.is_dir():
        shutil.rmtree(lang_root)

    updated = Settings(
        data_root=settings.data_root,
        native_language=settings.native_language,
        active_target_language=(
            None
            if settings.active_target_language == iso
            else settings.active_target_language
        ),
        onboarding_complete=settings.onboarding_complete,
        ollama_url=settings.ollama_url,
        huggingface_token=settings.huggingface_token,
        llm_enabled=settings.llm_enabled,
        theme=settings.theme,
        reader_font_size=settings.reader_font_size,
        llama_server_url=settings.llama_server_url,
    )
    settings_store.save(updated)
    return updated
