"""Complete first-run language onboarding."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.setup import add_target_with_spacy_download


def complete_onboarding(
    *,
    data_root: Path,
    settings_store: SettingsStore,
    settings: Settings,
    native_language: str,
    target_language: str,
    level: CEFRLevel,
) -> Settings:
    """Persist language choices, enqueue spaCy download, and mark onboarding done."""
    add_target_with_spacy_download(data_root, target_language, level)
    updated = Settings(
        data_root=settings.data_root,
        native_language=native_language,
        active_target_language=target_language,
        onboarding_complete=True,
        ollama_url=settings.ollama_url,
        llm_enabled=settings.llm_enabled,
        theme=settings.theme,
    )
    settings_store.save(updated)
    return updated
